"""Service helpers for interacting with user records."""

from __future__ import annotations

from typing import Optional

from sqlalchemy import or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.schemas.user import UserCreate
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


async def user_exists_with_username_or_email(
    session: AsyncSession, *, username: str, email: str
) -> bool:
    """Check whether a user already exists with the provided username or email."""
    result = await session.execute(
        select(User.id).where(or_(User.username == username, User.email == email))
    )
    return result.first() is not None
