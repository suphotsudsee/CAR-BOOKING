"""Notification service layer."""

from __future__ import annotations

from collections.abc import Iterable
from datetime import datetime, timezone
from typing import Optional

from fastapi import WebSocket
from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Notification, NotificationChannel, NotificationPreference, User

from .line_notify import LineNotifyClient, LineNotifyError


class NotificationBroadcastManager:
    """Manages websocket connections for real-time notifications."""

    def __init__(self) -> None:
        self._connections: dict[int, set[WebSocket]] = {}

    async def connect(self, user_id: int, websocket: WebSocket) -> None:
        await websocket.accept()
        self._connections.setdefault(user_id, set()).add(websocket)

    def disconnect(self, user_id: int, websocket: WebSocket) -> None:
        connections = self._connections.get(user_id)
        if not connections:
            return
        connections.discard(websocket)
        if not connections:
            self._connections.pop(user_id, None)

    async def broadcast(self, user_id: int, payload: dict) -> None:
        connections = list(self._connections.get(user_id, set()))
        for websocket in connections:
            try:
                await websocket.send_json(payload)
            except Exception:  # pragma: no cover - defensive cleanup
                try:
                    await websocket.close()
                finally:
                    self.disconnect(user_id, websocket)


notification_broadcaster = NotificationBroadcastManager()


class NotificationService:
    """High level orchestrator for user notifications."""

    def __init__(
        self,
        session: AsyncSession,
        *,
        line_client: Optional[LineNotifyClient] = None,
    ) -> None:
        self._session = session
        self._line_client = line_client or LineNotifyClient()

    async def get_preferences(self, user_id: int) -> NotificationPreference:
        preference = await self._session.get(NotificationPreference, user_id)
        if preference is None:
            preference = NotificationPreference(user_id=user_id)
            self._session.add(preference)
            await self._session.commit()
            await self._session.refresh(preference)
        return preference

    async def update_preferences(
        self,
        user_id: int,
        *,
        in_app_enabled: Optional[bool] = None,
        email_enabled: Optional[bool] = None,
        line_enabled: Optional[bool] = None,
        line_access_token: Optional[str] = None,
    ) -> NotificationPreference:
        preference = await self.get_preferences(user_id)

        if in_app_enabled is not None:
            preference.in_app_enabled = in_app_enabled
        if email_enabled is not None:
            preference.email_enabled = email_enabled
        if line_enabled is not None:
            preference.line_enabled = line_enabled
            if not line_enabled:
                preference.line_access_token = None
        if line_access_token is not None:
            trimmed = line_access_token.strip()
            preference.line_access_token = trimmed or None

        await self._session.commit()
        await self._session.refresh(preference)
        return preference

    async def list_notifications(
        self,
        user_id: int,
        *,
        limit: int = 20,
        offset: int = 0,
        unread_only: bool = False,
    ) -> list[Notification]:
        stmt: Select[tuple[Notification]] = (
            select(Notification)
            .where(Notification.user_id == user_id)
            .order_by(Notification.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        if unread_only:
            stmt = stmt.where(Notification.read_at.is_(None))

        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def count_unread(self, user_id: int) -> int:
        stmt = (
            select(func.count())
            .select_from(Notification)
            .where(Notification.user_id == user_id, Notification.read_at.is_(None))
        )
        result = await self._session.execute(stmt)
        return int(result.scalar_one())

    async def mark_read(self, notification: Notification) -> Notification:
        notification.mark_read(datetime.now(timezone.utc))
        await self._session.commit()
        await self._session.refresh(notification)
        await notification_broadcaster.broadcast(
            notification.user_id,
            {
                "type": "notification.read",
                "payload": {
                    "id": notification.id,
                    "read_at": notification.read_at.isoformat()
                    if notification.read_at
                    else None,
                },
            },
        )
        return notification

    async def mark_all_read(self, user_id: int) -> int:
        stmt = (
            select(Notification)
            .where(Notification.user_id == user_id, Notification.read_at.is_(None))
        )
        result = await self._session.execute(stmt)
        notifications = list(result.scalars().all())
        now = datetime.now(timezone.utc)
        for item in notifications:
            item.mark_read(now)
        await self._session.commit()
        for item in notifications:
            await notification_broadcaster.broadcast(
                user_id,
                {
                    "type": "notification.read",
                    "payload": {
                        "id": item.id,
                        "read_at": item.read_at.isoformat() if item.read_at else None,
                    },
                },
            )
        return len(notifications)

    async def create_notification(
        self,
        user: User,
        *,
        title: str,
        message: str,
        category: str = "general",
        metadata: Optional[dict] = None,
        channels: Optional[Iterable[NotificationChannel]] = None,
    ) -> Notification:
        preference = await self.get_preferences(user.id)
        available_channels = set(
            channel
            for channel in NotificationChannel
            if preference.allow_channel(channel)
        )

        if channels is not None:
            target_channels = [channel for channel in channels if channel in available_channels]
        else:
            target_channels = list(available_channels)

        # Always persist in-app notifications so that a record exists.
        if NotificationChannel.IN_APP not in target_channels and preference.in_app_enabled:
            target_channels.append(NotificationChannel.IN_APP)

        notification = Notification(
            user_id=user.id,
            title=title,
            message=message,
            category=category,
            data=metadata,
            delivered_channels=[channel.value for channel in target_channels],
            delivery_errors={},
        )
        self._session.add(notification)
        await self._session.commit()
        await self._session.refresh(notification)

        await notification_broadcaster.broadcast(
            user.id,
            {
                "type": "notification.created",
                "payload": self._serialise_notification(notification),
            },
        )

        # Handle asynchronous integrations after the notification has been persisted.
        await self._deliver_external_channels(notification, preference, target_channels)
        return notification

    async def _deliver_external_channels(
        self,
        notification: Notification,
        preference: NotificationPreference,
        channels: Iterable[NotificationChannel],
    ) -> None:
        errors: dict[str, str] = {}

        for channel in channels:
            if channel is NotificationChannel.LINE:
                try:
                    await self._line_client.send_message(
                        notification.message,
                        token=preference.line_access_token,
                    )
                except LineNotifyError as exc:
                    errors[channel.value] = str(exc)

        if errors:
            notification.delivery_errors.update(errors)
            await self._session.commit()
            await self._session.refresh(notification)

    def _serialise_notification(self, notification: Notification) -> dict:
        return {
            "id": notification.id,
            "title": notification.title,
            "message": notification.message,
            "category": notification.category,
            "data": notification.data or {},
            "created_at": notification.created_at.isoformat()
            if notification.created_at
            else None,
            "read_at": notification.read_at.isoformat() if notification.read_at else None,
            "delivered_channels": notification.delivered_channels,
            "delivery_errors": notification.delivery_errors,
        }


__all__ = [
    "NotificationService",
    "notification_broadcaster",
]

