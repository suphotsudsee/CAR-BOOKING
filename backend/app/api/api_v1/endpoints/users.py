"""User management API endpoints."""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import RoleBasedAccess, get_current_user
from app.core.config import settings
from app.db import get_async_session
from app.models.user import User, UserRole
from app.schemas import (
    UserCreate,
    UserPasswordChange,
    UserProfileUpdate,
    UserRead,
    UserRoleUpdate,
    UserUpdate,
)
from app.services import (
    change_user_password,
    create_user,
    delete_user as delete_user_service,
    get_user_by_id,
    list_users,
    update_user as update_user_service,
    update_user_profile,
    user_exists_with_username_or_email,
)
from app.utils import verify_password

router = APIRouter()

_MANAGEMENT_ROLES = (UserRole.FLEET_ADMIN, UserRole.MANAGER)
_manage_users = RoleBasedAccess(_MANAGEMENT_ROLES)
_assign_roles = RoleBasedAccess([UserRole.FLEET_ADMIN])


@router.get("/me", response_model=UserRead)
async def read_own_profile(current_user: User = Depends(get_current_user)) -> User:
    """Return profile information for the authenticated user."""
    return current_user


@router.patch("/me", response_model=UserRead)
async def update_own_profile(
    profile_update: UserProfileUpdate,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user),
) -> User:
    """Allow the authenticated user to update their own profile."""
    try:
        return await update_user_profile(
            session, user=current_user, profile_update=profile_update
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc


@router.post("/me/change-password", status_code=status.HTTP_200_OK)
async def change_password(
    password_change: UserPasswordChange,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user),
) -> dict[str, str]:
    """Update the authenticated user's password after verifying the current one."""
    if not verify_password(password_change.current_password, current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect",
        )

    await change_user_password(session, user=current_user, password_change=password_change)
    return {"message": "Password updated successfully"}


@router.get("/", response_model=list[UserRead])
async def list_users_endpoint(
    skip: int = Query(0, ge=0),
    limit: int = Query(
        default=settings.DEFAULT_PAGE_SIZE,
        ge=1,
        le=settings.MAX_PAGE_SIZE,
    ),
    role: Optional[UserRole] = None,
    is_active: Optional[bool] = None,
    search: Optional[str] = Query(default=None, min_length=1),
    session: AsyncSession = Depends(get_async_session),
    _: User = Depends(_manage_users),
) -> list[User]:
    """List users with optional filtering and pagination."""
    search_term = search.strip() if search else None
    return await list_users(
        session,
        skip=skip,
        limit=limit,
        role=role,
        is_active=is_active,
        search=search_term,
    )


@router.post("/", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def create_user_endpoint(
    user_in: UserCreate,
    session: AsyncSession = Depends(get_async_session),
    _: User = Depends(_manage_users),
) -> User:
    """Create a new user. Restricted to management roles."""
    if await user_exists_with_username_or_email(
        session, username=user_in.username, email=user_in.email
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username or email already registered",
        )

    try:
        return await create_user(session, user_in)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc


@router.get("/{user_id}", response_model=UserRead)
async def get_user_detail(
    user_id: int,
    session: AsyncSession = Depends(get_async_session),
    _: User = Depends(_manage_users),
) -> User:
    """Retrieve a single user by identifier."""
    user = await get_user_by_id(session, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user


@router.patch("/{user_id}", response_model=UserRead)
async def update_user_endpoint(
    user_id: int,
    user_update: UserUpdate,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(_manage_users),
) -> User:
    """Update the specified user's information."""
    user = await get_user_by_id(session, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    if user_update.role is not None and current_user.role != UserRole.FLEET_ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to modify role",
        )

    try:
        return await update_user_service(session, user=user, user_update=user_update)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc


@router.delete(
    "/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
)
async def delete_user_endpoint(
    user_id: int,
    session: AsyncSession = Depends(get_async_session),
    _: User = Depends(_manage_users),
) -> Response:
    """Delete the specified user from the system."""
    user = await get_user_by_id(session, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    await delete_user_service(session, user=user)

    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/{user_id}/role", response_model=UserRead)
async def assign_role(
    user_id: int,
    role_update: UserRoleUpdate,
    session: AsyncSession = Depends(get_async_session),
    _: User = Depends(_assign_roles),
) -> User:
    """Assign a new role to an existing user. Restricted to fleet administrators."""
    user = await get_user_by_id(session, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    if user.role == role_update.role:
        return user

    user.role = role_update.role
    await session.commit()
    await session.refresh(user)
    return user
