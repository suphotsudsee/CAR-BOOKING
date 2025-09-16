"""Pydantic schemas exposed by the application."""

from .auth import (
    LoginRequest,
    RefreshTokenRequest,
    RefreshTokenResponse,
    TokenPayload,
    TokenResponse,
)
from .user import (
    UserCreate,
    UserPasswordChange,
    UserProfileUpdate,
    UserRead,
    UserRoleUpdate,
    UserUpdate,
)
from .vehicle import (
    VehicleCreate,
    VehicleRead,
    VehicleStatusUpdate,
    VehicleUpdate,
)

__all__ = [
    "LoginRequest",
    "RefreshTokenRequest",
    "RefreshTokenResponse",
    "TokenPayload",
    "TokenResponse",
    "UserCreate",
    "UserPasswordChange",
    "UserProfileUpdate",
    "UserRead",
    "UserRoleUpdate",
    "UserUpdate",
    "VehicleCreate",
    "VehicleRead",
    "VehicleStatusUpdate",
    "VehicleUpdate",
]
