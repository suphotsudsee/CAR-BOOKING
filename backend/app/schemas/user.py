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

    model_config = ConfigDict(from_attributes=True)
