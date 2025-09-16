"""Service helpers for interacting with user records."""

from __future__ import annotations

from typing import Optional, Sequence

from sqlalchemy import Select, func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User, UserRole
from app.schemas.user import (
    UserCreate,
    UserPasswordChange,
    UserProfileUpdate,
    UserUpdate,
)
from app.utils.security import get_password_hash


async def get_user_by_id(session: AsyncSession, user_id: int) -> Optional[User]:
    """Return the user with the supplied primary key, if present."""
    result = await session.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()


async def get_user_by_username(session: AsyncSession, username: str) -> Optional[User]:
    """Return the user with the supplied *username*, if present."""
    result = await session.execute(select(User).where(User.username == username))
    return result.scalar_one_or_none()


async def get_user_by_email(session: AsyncSession, email: str) -> Optional[User]:
    """Return the user with the supplied *email*, if present."""
    result = await session.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none()


async def create_user(session: AsyncSession, user_in: UserCreate) -> User:
    """Persist a new user to the database."""
    user = User(
        username=user_in.username,
        email=user_in.email,
        full_name=user_in.full_name,
        department=user_in.department,
        role=user_in.role,
        password_hash=get_password_hash(user_in.password),
    )
    session.add(user)

    try:
        await session.commit()
    except IntegrityError as exc:
        await session.rollback()
        raise ValueError("Username or email already exists") from exc

    await session.refresh(user)
    return user


async def list_users(
    session: AsyncSession,
    *,
    skip: int = 0,
    limit: Optional[int] = None,
    role: Optional[UserRole] = None,
    is_active: Optional[bool] = None,
    search: Optional[str] = None,
) -> list[User]:
    """Return a collection of users filtered by the supplied parameters."""
    stmt: Select[tuple[User]] = select(User).order_by(User.id)

    if role is not None:
        stmt = stmt.where(User.role == role)

    if is_active is not None:
        stmt = stmt.where(User.is_active == is_active)

    if search:
        pattern = f"%{search.lower()}%"
        stmt = stmt.where(
            or_(
                func.lower(User.username).like(pattern),
                func.lower(User.full_name).like(pattern),
                func.lower(User.email).like(pattern),
            )
        )

    if skip:
        stmt = stmt.offset(skip)

    if limit is not None:
        stmt = stmt.limit(limit)

    result = await session.execute(stmt)
    return list(result.scalars().all())


async def _check_unique_constraints(
    session: AsyncSession,
    *,
    username: Optional[str],
    email: Optional[str],
    exclude_user_ids: Sequence[int] | None = None,
) -> None:
    """Ensure that the supplied username and email are unique."""
    conditions = []
    if username is not None:
        conditions.append(User.username == username)
    if email is not None:
        conditions.append(User.email == email)

    if not conditions:
        return

    stmt = select(User.id).where(or_(*conditions))

    if exclude_user_ids:
        stmt = stmt.where(User.id.notin_(exclude_user_ids))

    result = await session.execute(stmt)
    if result.first() is not None:
        raise ValueError("Username or email already exists")


async def update_user(
    session: AsyncSession, *, user: User, user_update: UserUpdate
) -> User:
    """Update a user's attributes from administrative input."""
    data = user_update.model_dump(exclude_unset=True)

    await _check_unique_constraints(
        session,
        username=data.get("username", user.username) if "username" in data else None,
        email=data.get("email", user.email) if "email" in data else None,
        exclude_user_ids=[user.id],
    )

    password = data.pop("password", None)
    if password:
        user.password_hash = get_password_hash(password)

    for field, value in data.items():
        setattr(user, field, value)

    await session.commit()
    await session.refresh(user)
    return user


async def update_user_profile(
    session: AsyncSession, *, user: User, profile_update: UserProfileUpdate
) -> User:
    """Update mutable profile fields for the provided *user*."""
    data = profile_update.model_dump(exclude_unset=True)

    await _check_unique_constraints(
        session,
        username=None,
        email=data.get("email", user.email) if "email" in data else None,
        exclude_user_ids=[user.id],
    )

    for field, value in data.items():
        setattr(user, field, value)

    await session.commit()
    await session.refresh(user)
    return user


async def change_user_password(
    session: AsyncSession, *, user: User, password_change: UserPasswordChange
) -> User:
    """Change the password for *user* using the provided request data."""
    user.password_hash = get_password_hash(password_change.new_password)
    await session.commit()
    await session.refresh(user)
    return user


async def delete_user(session: AsyncSession, *, user: User) -> None:
    """Remove *user* from the database."""
    await session.delete(user)
    await session.commit()


async def user_exists_with_username_or_email(
    session: AsyncSession, *, username: str, email: str
) -> bool:
    """Check whether a user already exists with the provided username or email."""
    result = await session.execute(
        select(User.id).where(or_(User.username == username, User.email == email))
    )
    return result.first() is not None
