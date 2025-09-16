"""Authentication endpoints."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import RoleBasedAccess, get_current_user
from app.core.config import settings
from app.db import get_async_session
from app.models.user import User, UserRole
from app.schemas import (
    LoginRequest,
    RefreshTokenRequest,
    RefreshTokenResponse,
    TokenResponse,
    UserCreate,
    UserRead,
)
from app.services import (
    create_user,
    get_user_by_id,
    get_user_by_username,
    user_exists_with_username_or_email,
)
from app.utils import (
    InvalidTokenError,
    create_access_token,
    create_refresh_token,
    decode_token,
    verify_password,
)

router = APIRouter()


@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def register_user(
    user_in: UserCreate,
    session: AsyncSession = Depends(get_async_session),
) -> User:
    """Register a new user account."""
    if await user_exists_with_username_or_email(
        session, username=user_in.username, email=user_in.email
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username or email already registered",
        )

    try:
        user = await create_user(session, user_in)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    return user


@router.post("/login", response_model=TokenResponse)
async def login(
    request: LoginRequest,
    session: AsyncSession = Depends(get_async_session),
) -> TokenResponse:
    """Authenticate a user and issue JWT tokens."""
    user = await get_user_by_username(session, request.username)

    if user is None or not verify_password(request.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive",
        )

    access_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    refresh_expires = timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

    access_token = create_access_token(
        subject=str(user.id),
        username=user.username,
        role=user.role.value,
        expires_delta=access_expires,
    )
    refresh_token = create_refresh_token(
        subject=str(user.id),
        username=user.username,
        role=user.role.value,
        expires_delta=refresh_expires,
    )

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=int(access_expires.total_seconds()),
    )


@router.post("/refresh", response_model=RefreshTokenResponse)
async def refresh_access_token(
    request: RefreshTokenRequest,
    session: AsyncSession = Depends(get_async_session),
) -> RefreshTokenResponse:
    """Generate a new access token from a refresh token."""
    try:
        payload = decode_token(request.refresh_token, expected_type="refresh")
    except InvalidTokenError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc

    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token payload missing subject",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        user_id_int = int(user_id)
    except (TypeError, ValueError) as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token subject",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc

    user = await get_user_by_id(session, user_id_int)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive",
        )

    access_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    new_access_token = create_access_token(
        subject=str(user.id),
        username=user.username,
        role=user.role.value,
        expires_delta=access_expires,
    )

    return RefreshTokenResponse(
        access_token=new_access_token,
        expires_in=int(access_expires.total_seconds()),
        issued_at=datetime.now(timezone.utc),
    )


@router.get("/me", response_model=UserRead)
async def read_current_user(current_user: User = Depends(get_current_user)) -> User:
    """Return the authenticated user's profile."""
    return current_user


@router.post("/logout")
async def logout(current_user: User = Depends(RoleBasedAccess(list(UserRole)))) -> dict[str, str]:
    """Placeholder logout endpoint relying on RBAC dependency."""
    return {"message": f"User {current_user.username} logged out"}
