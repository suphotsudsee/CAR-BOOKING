"""Database session management helpers."""

from collections.abc import AsyncIterator
from typing import Final

from sqlalchemy.ext.asyncio import (AsyncSession, async_sessionmaker,
                                    create_async_engine)

from app.core.config import settings

# Create async engine and session factory
_engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    future=True,
    pool_pre_ping=True,
)

async_session_factory: Final[async_sessionmaker[AsyncSession]] = async_sessionmaker(
    _engine,
    expire_on_commit=False,
    autoflush=False,
)


async def get_async_session() -> AsyncIterator[AsyncSession]:
    """FastAPI dependency that yields an :class:`AsyncSession`."""
    async with async_session_factory() as session:
        yield session
