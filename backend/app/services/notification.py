"""Notification service layer and WebSocket broadcasting utilities."""

from __future__ import annotations

import asyncio
from collections import defaultdict
from datetime import datetime, timezone
from typing import Any, Iterable, Optional

from fastapi import WebSocket
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.models import Notification, NotificationChannel, NotificationPreference, User
from app.models.notification import (
    EmailDeliveryState,
    EmailDeliveryStatus,
    EmailNotification,
)
from app.services.email import email_service
from app.services.line_notify import LineNotifyClient, LineNotifyError
from app.tasks.email import send_email_notification

logger = get_logger(__name__)


class NotificationBroadcaster:
    """Manage active WebSocket connections for real-time notifications."""

    def __init__(self) -> None:
        self._connections: dict[int, set[WebSocket]] = defaultdict(set)
        self._lock = asyncio.Lock()

    async def connect(self, user_id: int, websocket: WebSocket) -> None:
        """Register a new WebSocket connection for ``user_id``."""

        await websocket.accept()
        async with self._lock:
            self._connections[user_id].add(websocket)

    def disconnect(self, user_id: int, websocket: WebSocket) -> None:
        """Remove ``websocket`` from the active connection set."""

        connections = self._connections.get(user_id)
        if not connections:
            return
        connections.discard(websocket)
        if not connections:
            self._connections.pop(user_id, None)

    async def broadcast(self, user_id: int, payload: dict[str, Any]) -> None:
        """Send *payload* to all active connections for ``user_id``."""

        connections = list(self._connections.get(user_id, set()))
        for websocket in connections:
            try:
                await websocket.send_json(payload)
            except Exception:  # pragma: no cover - defensive cleanup
                logger.warning("notification_ws_send_failed", user_id=user_id)
                self.disconnect(user_id, websocket)


notification_broadcaster = NotificationBroadcaster()


def queue_email_notification(email: EmailNotification) -> None:
    """Queue an :class:`EmailNotification` for asynchronous delivery."""

    payload = email.to_payload()
    try:
        send_email_notification.apply_async(args=[payload], ignore_result=True)
    except Exception as exc:  # pragma: no cover - depends on broker availability
        logger.exception("email_notification_queue_failed", error=str(exc))
        raise


class NotificationService:
    """High level APIs for managing notifications."""

    def __init__(
        self,
        session: AsyncSession,
        *,
        line_client: Optional[LineNotifyClient] = None,
        broadcaster: Optional[NotificationBroadcaster] = None,
    ) -> None:
        self._session = session
        self._line_client = line_client or LineNotifyClient()
        self._broadcaster = broadcaster or notification_broadcaster

    async def get_preferences(self, user_id: int) -> NotificationPreference:
        """Return the user's notification preferences, creating defaults if needed."""

        stmt = select(NotificationPreference).where(NotificationPreference.user_id == user_id)
        result = await self._session.execute(stmt)
        preference = result.scalar_one_or_none()
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
        """Update and return the user's notification preferences."""

        preference = await self.get_preferences(user_id)
        if in_app_enabled is not None:
            preference.in_app_enabled = in_app_enabled
        if email_enabled is not None:
            preference.email_enabled = email_enabled
        if line_enabled is not None:
            preference.line_enabled = line_enabled
        if line_access_token is not None or (line_enabled is False):
            token = (line_access_token or "").strip() or None
            preference.line_access_token = token

        await self._session.commit()
        await self._session.refresh(preference)
        return preference

    async def list_notifications(
        self, user_id: int, *, limit: int = 50, offset: int = 0
    ) -> list[Notification]:
        """Return recent notifications for ``user_id`` ordered by recency."""

        stmt = (
            select(Notification)
            .where(Notification.user_id == user_id)
            .order_by(Notification.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def mark_all_read(self, user_id: int) -> int:
        """Mark all unread notifications as read and return the count."""

        stmt = select(Notification).where(
            Notification.user_id == user_id, Notification.read_at.is_(None)
        )
        result = await self._session.execute(stmt)
        notifications = result.scalars().all()
        if not notifications:
            return 0

        now = datetime.now(timezone.utc)
        for notification in notifications:
            notification.mark_read(now)

        await self._session.commit()
        return len(notifications)

    async def create_notification(
        self,
        user: User,
        *,
        title: str,
        message: str,
        category: str = "general",
        metadata: Optional[dict[str, Any]] = None,
        channels: Optional[Iterable[NotificationChannel | str]] = None,
        email_subject: Optional[str] = None,
        email_template: str = "generic_notification",
        email_context: Optional[dict[str, Any]] = None,
        email_cc: Optional[Iterable[str]] = None,
        email_bcc: Optional[Iterable[str]] = None,
        reply_to: Optional[str] = None,
    ) -> Notification:
        """Create a notification for ``user`` and attempt delivery via channels."""

        preference = await self.get_preferences(user.id)
        resolved_channels = self._resolve_channels(preference, channels)

        data = dict(metadata) if metadata else None
        notification = Notification(
            user_id=user.id,
            title=title,
            message=message,
            category=category,
            data=data,
            delivered_channels=[],
            delivery_errors={},
        )
        self._session.add(notification)
        await self._session.commit()
        await self._session.refresh(notification)

        delivery_changed = False
        if NotificationChannel.IN_APP in resolved_channels:
            delivery_changed |= await self._deliver_in_app(notification, user)

        if NotificationChannel.LINE in resolved_channels:
            delivery_changed |= await self._deliver_line(notification, preference)

        if NotificationChannel.EMAIL in resolved_channels:
            delivery_changed |= self._queue_email_delivery(
                notification,
                user,
                subject=email_subject or title,
                template=email_template,
                base_context=email_context,
                metadata=data,
                cc=email_cc,
                bcc=email_bcc,
                reply_to=reply_to,
            )

        if delivery_changed:
            await self._session.commit()
            await self._session.refresh(notification)

        return notification

    def _resolve_channels(
        self,
        preference: NotificationPreference,
        channels: Optional[Iterable[NotificationChannel | str]],
    ) -> list[NotificationChannel]:
        if channels is None:
            return [
                channel
                for channel in (
                    NotificationChannel.IN_APP,
                    NotificationChannel.EMAIL,
                    NotificationChannel.LINE,
                )
                if preference.allow_channel(channel)
            ]

        resolved: list[NotificationChannel] = []
        seen: set[NotificationChannel] = set()
        for item in channels:
            channel = item if isinstance(item, NotificationChannel) else NotificationChannel(str(item))
            if channel not in seen:
                resolved.append(channel)
                seen.add(channel)
        return resolved

    async def _deliver_in_app(self, notification: Notification, user: User) -> bool:
        delivered = set(notification.delivered_channels or [])
        if NotificationChannel.IN_APP.value not in delivered:
            delivered.add(NotificationChannel.IN_APP.value)
            notification.delivered_channels = list(delivered)

        errors = dict(notification.delivery_errors or {})
        errors.pop(NotificationChannel.IN_APP.value, None)
        notification.delivery_errors = errors

        payload = {
            "type": "notification.created",
            "data": self._serialise_notification(notification),
        }
        try:
            await self._broadcaster.broadcast(user.id, payload)
        except Exception:  # pragma: no cover - broadcast failures shouldn't stop delivery
            logger.warning("notification_broadcast_failed", user_id=user.id)
        return True

    async def _deliver_line(
        self, notification: Notification, preference: NotificationPreference
    ) -> bool:
        if not self._line_client or not preference.allow_channel(NotificationChannel.LINE):
            return False

        token = preference.line_access_token
        try:
            await self._line_client.send_message(notification.message, token=token)
        except LineNotifyError as exc:
            logger.warning(
                "line_notification_failed",
                user_id=notification.user_id,
                error=str(exc),
            )
            errors = dict(notification.delivery_errors or {})
            errors[NotificationChannel.LINE.value] = str(exc)
            notification.delivery_errors = errors
            return True
        else:
            delivered = set(notification.delivered_channels or [])
            delivered.add(NotificationChannel.LINE.value)
            notification.delivered_channels = list(delivered)

            errors = dict(notification.delivery_errors or {})
            errors.pop(NotificationChannel.LINE.value, None)
            notification.delivery_errors = errors
            return True

    def _queue_email_delivery(
        self,
        notification: Notification,
        user: User,
        *,
        subject: str,
        template: str,
        base_context: Optional[dict[str, Any]],
        metadata: Optional[dict[str, Any]],
        cc: Optional[Iterable[str]],
        bcc: Optional[Iterable[str]],
        reply_to: Optional[str],
    ) -> bool:
        if not user.email:
            errors = dict(notification.delivery_errors or {})
            errors[NotificationChannel.EMAIL.value] = "Recipient email address is missing"
            notification.delivery_errors = errors
            return True

        if not email_service.is_configured:
            errors = dict(notification.delivery_errors or {})
            errors[NotificationChannel.EMAIL.value] = "Email service is not configured"
            notification.delivery_errors = errors
            return True

        context = self._build_email_context(
            subject=subject,
            message=notification.message,
            base_context=base_context,
            metadata=metadata,
            user=user,
        )

        email = EmailNotification(
            to_email=user.email,
            subject=subject,
            template_name=template,
            context=context,
            cc=list(cc or []),
            bcc=list(bcc or []),
            reply_to=reply_to,
            notification_id=notification.id,
            user_id=user.id,
            metadata=metadata or {},
        )

        status = EmailDeliveryStatus(status=EmailDeliveryState.QUEUED, attempts=0)
        self._apply_email_status(notification, status)

        try:
            queue_email_notification(email)
        except Exception as exc:  # pragma: no cover - depends on broker availability
            logger.exception(
                "email_notification_queue_failed",
                user_id=user.id,
                notification_id=notification.id,
            )
            failure_status = EmailDeliveryStatus(
                status=EmailDeliveryState.FAILED,
                error=str(exc),
            )
            self._apply_email_status(notification, failure_status)
        return True

    def _apply_email_status(
        self, notification: Notification, status: EmailDeliveryStatus
    ) -> None:
        data = dict(notification.data or {})
        existing_raw = data.get("_email_delivery")
        previous_attempts = 0
        if isinstance(existing_raw, dict):
            try:
                previous_attempts = EmailDeliveryStatus.from_dict(existing_raw).attempts
            except Exception:  # pragma: no cover - defensive
                previous_attempts = int(existing_raw.get("attempts", 0))

        if status.status is EmailDeliveryState.QUEUED:
            status.attempts = previous_attempts
        else:
            status.attempts = max(status.attempts, previous_attempts + 1)

        data["_email_delivery"] = status.to_dict()
        notification.data = data

        delivered = set(notification.delivered_channels or [])
        errors = dict(notification.delivery_errors or {})
        if status.status is EmailDeliveryState.SENT:
            delivered.add(NotificationChannel.EMAIL.value)
            errors.pop(NotificationChannel.EMAIL.value, None)
        elif status.status is EmailDeliveryState.QUEUED:
            errors.pop(NotificationChannel.EMAIL.value, None)
        else:
            delivered.discard(NotificationChannel.EMAIL.value)
            errors[NotificationChannel.EMAIL.value] = status.error or "Email delivery failed"

        notification.delivered_channels = list(delivered)
        notification.delivery_errors = errors

    def _build_email_context(
        self,
        *,
        subject: str,
        message: str,
        base_context: Optional[dict[str, Any]],
        metadata: Optional[dict[str, Any]],
        user: User,
    ) -> dict[str, Any]:
        context: dict[str, Any] = {
            "subject": subject,
            "message": message,
            "recipient_name": getattr(user, "full_name", None) or user.username,
        }
        if metadata:
            context.update(metadata)
        if base_context:
            context.update(base_context)
        return context

    def _serialise_notification(self, notification: Notification) -> dict[str, Any]:
        return {
            "id": notification.id,
            "user_id": notification.user_id,
            "title": notification.title,
            "message": notification.message,
            "category": notification.category,
            "data": notification.data,
            "read_at": notification.read_at.isoformat() if notification.read_at else None,
            "delivered_channels": notification.delivered_channels,
            "delivery_errors": notification.delivery_errors,
            "created_at": notification.created_at.isoformat()
            if notification.created_at
            else None,
        }


__all__ = [
    "NotificationBroadcaster",
    "NotificationService",
    "notification_broadcaster",
    "queue_email_notification",
]
