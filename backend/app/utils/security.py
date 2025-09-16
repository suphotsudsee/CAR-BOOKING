"""Security related helper functions."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings


class InvalidTokenError(Exception):
    """Raised when a provided JWT token cannot be validated."""


_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def get_password_hash(password: str) -> str:
    """Hash *password* using the configured password hashing context."""
    return _pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Validate that *plain_password* matches *hashed_password*."""
    return _pwd_context.verify(plain_password, hashed_password)


def _create_token(
    *,
    subject: str,
    username: str,
    role: str,
    token_type: str,
    expires_delta: timedelta,
    additional_claims: Optional[Dict[str, Any]] = None,
) -> str:
    """Create a JWT token containing the supplied metadata."""
    now = datetime.now(timezone.utc)
    expire = now + expires_delta

    payload: Dict[str, Any] = {
        "sub": subject,
        "iat": int(now.timestamp()),
        "exp": int(expire.timestamp()),
        "type": token_type,
        "username": username,
        "role": role,
    }

    if additional_claims:
        payload.update(additional_claims)

    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def create_access_token(
    *,
    subject: str,
    username: str,
    role: str,
    expires_delta: Optional[timedelta] = None,
    additional_claims: Optional[Dict[str, Any]] = None,
) -> str:
    """Create a signed JWT access token for the given subject."""
    delta = expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    return _create_token(
        subject=subject,
        username=username,
        role=role,
        token_type="access",
        expires_delta=delta,
        additional_claims=additional_claims,
    )


def create_refresh_token(
    *,
    subject: str,
    username: str,
    role: str,
    expires_delta: Optional[timedelta] = None,
    additional_claims: Optional[Dict[str, Any]] = None,
) -> str:
    """Create a signed JWT refresh token for the given subject."""
    delta = expires_delta or timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    return _create_token(
        subject=subject,
        username=username,
        role=role,
        token_type="refresh",
        expires_delta=delta,
        additional_claims=additional_claims,
    )


def decode_token(token: str, *, expected_type: Optional[str] = None) -> Dict[str, Any]:
    """Decode *token* and optionally verify the ``type`` claim."""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    except JWTError as exc:  # pragma: no cover - defensive, depends on external lib
        raise InvalidTokenError("Could not validate credentials") from exc

    if expected_type is not None and payload.get("type") != expected_type:
        raise InvalidTokenError("Invalid token type")

    return payload


__all__ = [
    "InvalidTokenError",
    "create_access_token",
    "create_refresh_token",
    "decode_token",
    "get_password_hash",
    "verify_password",
]
