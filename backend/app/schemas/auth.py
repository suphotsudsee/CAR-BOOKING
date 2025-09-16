"""Schemas for authentication endpoints."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.user import UserRole


class LoginRequest(BaseModel):
    """Payload for login requests."""

    username: str = Field(min_length=3, max_length=50)
    password: str = Field(min_length=8, max_length=128)


class TokenResponse(BaseModel):
    """Response returned when issuing JWT tokens."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class TokenPayload(BaseModel):
    """Structure of the JWT payload we expect from generated tokens."""

    sub: str
    username: str
    role: UserRole
    type: str
    exp: int
    iat: int


class RefreshTokenRequest(BaseModel):
    """Payload for refreshing access tokens."""

    refresh_token: str


class RefreshTokenResponse(BaseModel):
    """Response returned when a refresh token is exchanged."""

    access_token: str
    token_type: str = "bearer"
    expires_in: int
    issued_at: datetime

    model_config = ConfigDict(from_attributes=True)
