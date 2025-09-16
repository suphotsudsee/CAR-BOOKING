"""Reusable FastAPI dependencies."""

from __future__ import annotations

from typing import Sequence

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_async_session
from app.models.user import User, UserRole
from app.utils import InvalidTokenError, decode_token

_bearer_scheme = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer_scheme),
    session: AsyncSession = Depends(get_async_session),
) -> User:
    """Resolve the currently authenticated user based on the Authorization header."""
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials

    try:
        payload = decode_token(token, expected_type="access")
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

    result = await session.execute(select(User).where(User.id == user_id_int))
    user = result.scalar_one_or_none()

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

    return user


class RoleBasedAccess:
    """Dependency that enforces role-based access control."""

    def __init__(self, roles: Sequence[UserRole | str]):
        if not roles:
            msg = "At least one role must be provided"
            raise ValueError(msg)
        self._allowed_roles = {self._normalise_role(role) for role in roles}

    def _normalise_role(self, role: UserRole | str) -> UserRole:
        if isinstance(role, UserRole):
            return role
        try:
            return UserRole(role)
        except ValueError as exc:  # pragma: no cover - guard against bad configuration
            raise ValueError(f"Unknown role: {role}") from exc

    async def __call__(self, user: User = Depends(get_current_user)) -> User:
        if user.role not in self._allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions",
            )
        return user


__all__ = ["RoleBasedAccess", "get_current_user"]
