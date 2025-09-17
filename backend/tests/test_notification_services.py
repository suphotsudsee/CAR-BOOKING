from __future__ import annotations

import pytest

from app.models import Notification, User, UserRole
from app.services.notification import NotificationService


class _StubLineClient:
    def __init__(self) -> None:
        self.messages: list[str] = []

    async def send_message(self, message: str, *, token: str | None = None):
        self.messages.append(message)
        class _Response:
            success = True
            status_code = 200
            message = "ok"

        return _Response()


@pytest.mark.asyncio()
async def test_preferences_created_with_defaults(async_session):
    user = User(
        username="alice",
        email="alice@example.com",
        full_name="Alice Example",
        department="IT",
        role=UserRole.REQUESTER,
        password_hash="hashed",
    )
    async_session.add(user)
    await async_session.commit()

    service = NotificationService(async_session)
    preferences = await service.get_preferences(user.id)

    assert preferences.in_app_enabled is True
    assert preferences.email_enabled is False
    assert preferences.line_enabled is False


@pytest.mark.asyncio()
async def test_create_notification_persists_record(async_session):
    user = User(
        username="bob",
        email="bob@example.com",
        full_name="Bob Example",
        department="Ops",
        role=UserRole.MANAGER,
        password_hash="hashed",
    )
    async_session.add(user)
    await async_session.commit()

    stub_line = _StubLineClient()
    service = NotificationService(async_session, line_client=stub_line)
    await service.update_preferences(
        user.id,
        in_app_enabled=True,
        line_enabled=True,
        line_access_token="token-123",
    )

    notification = await service.create_notification(
        user,
        title="Test",
        message="Booking approved",
        category="booking",
        metadata={"booking_id": 1},
        channels=None,
    )

    assert notification.id is not None
    assert notification.data == {"booking_id": 1}
    assert set(notification.delivered_channels) >= {"in_app", "line"}
    assert notification.delivery_errors == {}
    assert stub_line.messages == ["Booking approved"]


@pytest.mark.asyncio()
async def test_mark_all_read_updates_state(async_session):
    user = User(
        username="carol",
        email="carol@example.com",
        full_name="Carol Example",
        department="Finance",
        role=UserRole.MANAGER,
        password_hash="hashed",
    )
    async_session.add(user)
    await async_session.commit()

    service = NotificationService(async_session)

    for index in range(3):
        await service.create_notification(
            user,
            title=f"Notification {index}",
            message="Please review booking",
            category="booking",
            metadata={"booking_id": index},
            channels=[],
        )

    result = await service.mark_all_read(user.id)
    assert result == 3

    notifications = await service.list_notifications(user.id)
    assert all(isinstance(item, Notification) and item.read_at is not None for item in notifications)
