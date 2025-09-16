"""Shared pytest fixtures for backend tests."""

from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Any

import pytest_asyncio
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.models.base import Base


class _AsyncSessionWrapper:
    """A lightweight asynchronous facade over a synchronous Session."""

    def __init__(self, session: Session):
        self._session = session

    async def execute(self, *args: Any, **kwargs: Any):  # type: ignore[override]
        return self._session.execute(*args, **kwargs)

    def add(self, instance: Any) -> None:
        self._session.add(instance)

    async def commit(self) -> None:
        self._session.commit()

    async def rollback(self) -> None:
        self._session.rollback()

    async def refresh(self, instance: Any) -> None:
        self._session.refresh(instance)

    async def delete(self, instance: Any) -> None:
        self._session.delete(instance)

    async def close(self) -> None:
        self._session.close()


@pytest_asyncio.fixture()
async def async_session() -> AsyncIterator[_AsyncSessionWrapper]:
    """Provide an isolated in-memory database session for each test."""

    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        future=True,
        echo=False,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine, expire_on_commit=False)
    session = session_factory()
    wrapped_session = _AsyncSessionWrapper(session)

    try:
        yield wrapped_session
    finally:
        await wrapped_session.rollback()
        await wrapped_session.close()
        engine.dispose()
