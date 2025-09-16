"""Pydantic schemas for user related operations."""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.models.user import UserRole


class UserBase(BaseModel):
    """Shared user attributes."""

    username: str = Field(min_length=3, max_length=50)
    email: EmailStr
    full_name: str = Field(min_length=1, max_length=120)
    department: Optional[str] = Field(default=None, max_length=100)
    role: UserRole


class UserCreate(UserBase):
    """Schema for user registration input."""

    password: str = Field(min_length=8, max_length=128)


class UserRead(UserBase):
    """Schema returned for user information."""

    id: int
    is_active: bool
    two_fa_enabled: bool

    model_config = ConfigDict(from_attributes=True)


class UserUpdate(BaseModel):
    """Schema for administrative updates to user records."""

    username: Optional[str] = Field(default=None, min_length=3, max_length=50)
    email: Optional[EmailStr] = None
    full_name: Optional[str] = Field(default=None, min_length=1, max_length=120)
    department: Optional[str] = Field(default=None, max_length=100)
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None
    two_fa_enabled: Optional[bool] = None
    password: Optional[str] = Field(default=None, min_length=8, max_length=128)

    model_config = ConfigDict(extra="forbid")


class UserProfileUpdate(BaseModel):
    """Schema for self-service profile updates."""

    full_name: Optional[str] = Field(default=None, min_length=1, max_length=120)
    department: Optional[str] = Field(default=None, max_length=100)
    email: Optional[EmailStr] = None
    two_fa_enabled: Optional[bool] = None

    model_config = ConfigDict(extra="forbid")


class UserPasswordChange(BaseModel):
    """Schema for requesting a password change."""

    current_password: str = Field(min_length=8, max_length=128)
    new_password: str = Field(min_length=8, max_length=128)


class UserRoleUpdate(BaseModel):
    """Schema for assigning a new role to a user."""

    role: UserRole
