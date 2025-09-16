"""Unit tests for the user service layer."""

from __future__ import annotations

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import UserRole
from app.schemas import (
    UserCreate,
    UserPasswordChange,
    UserProfileUpdate,
    UserUpdate,
)
from app.services import (
    change_user_password,
    create_user,
    delete_user,
    get_user_by_id,
    list_users,
    update_user,
    update_user_profile,
)
from app.utils import verify_password


@pytest.mark.asyncio
async def test_create_user(async_session: AsyncSession) -> None:
    user_in = UserCreate(
        username="alice",
        email="alice@example.com",
        full_name="Alice Example",
        department="IT",
        role=UserRole.REQUESTER,
        password="securepass123",
    )

    user = await create_user(async_session, user_in)

    assert user.id is not None
    assert user.username == "alice"
    assert user.role == UserRole.REQUESTER
    assert verify_password("securepass123", user.password_hash)


@pytest.mark.asyncio
async def test_create_user_duplicate(async_session: AsyncSession) -> None:
    user_in = UserCreate(
        username="bob",
        email="bob@example.com",
        full_name="Bob Example",
        department="HR",
        role=UserRole.MANAGER,
        password="anotherpass123",
    )

    await create_user(async_session, user_in)

    with pytest.raises(ValueError):
        await create_user(async_session, user_in)


@pytest.mark.asyncio
async def test_update_user(async_session: AsyncSession) -> None:
    user = await create_user(
        async_session,
        UserCreate(
            username="charlie",
            email="charlie@example.com",
            full_name="Charlie Example",
            department="Logistics",
            role=UserRole.REQUESTER,
            password="changeme123",
        ),
    )

    updated = await update_user(
        async_session,
        user=user,
        user_update=UserUpdate(
            email="charlie.new@example.com",
            full_name="Charlie Updated",
            department="Operations",
            role=UserRole.MANAGER,
            is_active=False,
            two_fa_enabled=True,
            password="newpassword123",
        ),
    )

    assert updated.email == "charlie.new@example.com"
    assert updated.full_name == "Charlie Updated"
    assert updated.department == "Operations"
    assert updated.role == UserRole.MANAGER
    assert updated.is_active is False
    assert updated.two_fa_enabled is True
    assert verify_password("newpassword123", updated.password_hash)


@pytest.mark.asyncio
async def test_update_user_conflict(async_session: AsyncSession) -> None:
    existing = await create_user(
        async_session,
        UserCreate(
            username="diana",
            email="diana@example.com",
            full_name="Diana Example",
            department="Finance",
            role=UserRole.AUDITOR,
            password="dianapass123",
        ),
    )
    target = await create_user(
        async_session,
        UserCreate(
            username="eve",
            email="eve@example.com",
            full_name="Eve Example",
            department="Finance",
            role=UserRole.REQUESTER,
            password="evepass123",
        ),
    )

    with pytest.raises(ValueError):
        await update_user(
            async_session,
            user=target,
            user_update=UserUpdate(email=existing.email),
        )


@pytest.mark.asyncio
async def test_list_users_filters(async_session: AsyncSession) -> None:
    await create_user(
        async_session,
        UserCreate(
            username="alpha",
            email="alpha@example.com",
            full_name="Alpha Tester",
            department="QA",
            role=UserRole.REQUESTER,
            password="alphapass123",
        ),
    )
    manager = await create_user(
        async_session,
        UserCreate(
            username="bravo",
            email="bravo@example.com",
            full_name="Bravo Manager",
            department="Operations",
            role=UserRole.MANAGER,
            password="bravopass123",
        ),
    )
    inactive = await create_user(
        async_session,
        UserCreate(
            username="charlie2",
            email="charlie2@example.com",
            full_name="Charlie Two",
            department="Operations",
            role=UserRole.FLEET_ADMIN,
            password="charliepass123",
        ),
    )

    await update_user(
        async_session,
        user=inactive,
        user_update=UserUpdate(is_active=False),
    )

    managers = await list_users(async_session, role=UserRole.MANAGER)
    assert [user.username for user in managers] == ["bravo"]

    inactive_users = await list_users(async_session, is_active=False)
    assert [user.username for user in inactive_users] == ["charlie2"]

    searched = await list_users(async_session, search="tester")
    assert [user.username for user in searched] == ["alpha"]

    limited = await list_users(async_session, limit=1)
    assert len(limited) == 1


@pytest.mark.asyncio
async def test_delete_user(async_session: AsyncSession) -> None:
    user = await create_user(
        async_session,
        UserCreate(
            username="frank",
            email="frank@example.com",
            full_name="Frank Example",
            department="Support",
            role=UserRole.REQUESTER,
            password="frankpass123",
        ),
    )

    await delete_user(async_session, user=user)
    fetched = await get_user_by_id(async_session, user.id)
    assert fetched is None


@pytest.mark.asyncio
async def test_update_user_profile(async_session: AsyncSession) -> None:
    user = await create_user(
        async_session,
        UserCreate(
            username="grace",
            email="grace@example.com",
            full_name="Grace Example",
            department="Engineering",
            role=UserRole.REQUESTER,
            password="gracepass123",
        ),
    )

    updated = await update_user_profile(
        async_session,
        user=user,
        profile_update=UserProfileUpdate(
            full_name="Grace Updated",
            department="Product",
            email="grace.updated@example.com",
            two_fa_enabled=True,
        ),
    )

    assert updated.full_name == "Grace Updated"
    assert updated.department == "Product"
    assert updated.email == "grace.updated@example.com"
    assert updated.two_fa_enabled is True


@pytest.mark.asyncio
async def test_update_user_profile_conflict(async_session: AsyncSession) -> None:
    await create_user(
        async_session,
        UserCreate(
            username="henry",
            email="henry@example.com",
            full_name="Henry Example",
            department="Sales",
            role=UserRole.REQUESTER,
            password="henrypass123",
        ),
    )
    user = await create_user(
        async_session,
        UserCreate(
            username="irene",
            email="irene@example.com",
            full_name="Irene Example",
            department="Marketing",
            role=UserRole.REQUESTER,
            password="irenepass123",
        ),
    )

    with pytest.raises(ValueError):
        await update_user_profile(
            async_session,
            user=user,
            profile_update=UserProfileUpdate(email="henry@example.com"),
        )


@pytest.mark.asyncio
async def test_change_user_password(async_session: AsyncSession) -> None:
    user = await create_user(
        async_session,
        UserCreate(
            username="judy",
            email="judy@example.com",
            full_name="Judy Example",
            department="Compliance",
            role=UserRole.AUDITOR,
            password="judypass123",
        ),
    )

    await change_user_password(
        async_session,
        user=user,
        password_change=UserPasswordChange(
            current_password="judypass123",
            new_password="judynewpass123",
        ),
    )

    refreshed = await get_user_by_id(async_session, user.id)
    assert refreshed is not None
    assert verify_password("judynewpass123", refreshed.password_hash)
