"""Celery tasks responsible for email delivery."""

from __future__ import annotations

import asyncio
from typing import Any

from celery import Task

from app.core.celery_app import celery_app
from app.core.logging import get_logger
from app.db import async_session_factory
from app.models import Notification, NotificationChannel
from app.models.notification import EmailDeliveryState, EmailDeliveryStatus, EmailNotification
from app.services.email import EmailNotConfiguredError, email_service

logger = get_logger(__name__)


async def _update_email_status(notification_id: int, status: EmailDeliveryStatus) -> None:
    async with async_session_factory() as session:
        notification = await session.get(Notification, notification_id)
        if notification is None:
            return

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
        elif status.status is EmailDeliveryState.RETRYING:
            delivered.discard(NotificationChannel.EMAIL.value)
            errors[NotificationChannel.EMAIL.value] = status.error or "Retry scheduled"
        else:
            delivered.discard(NotificationChannel.EMAIL.value)
            errors[NotificationChannel.EMAIL.value] = status.error or "Email delivery failed"

        notification.delivered_channels = list(delivered)
        notification.delivery_errors = errors
        await session.commit()


@celery_app.task(bind=True, name="email.send_notification", max_retries=5, default_retry_delay=60)
def send_email_notification(self: Task, payload: dict[str, Any]) -> dict[str, Any]:
    """Deliver an email notification and record the outcome."""

    email = EmailNotification.from_payload(payload)
    notification_id = email.notification_id

    if notification_id is not None:
        asyncio.run(
            _update_email_status(
                notification_id,
                EmailDeliveryStatus(status=EmailDeliveryState.QUEUED, attempts=0),
            )
        )

    try:
        result = email_service.deliver_notification(email)
    except EmailNotConfiguredError as exc:
        logger.error("email_delivery_not_configured", error=str(exc))
        if notification_id is not None:
            asyncio.run(
                _update_email_status(
                    notification_id,
                    EmailDeliveryStatus(
                        status=EmailDeliveryState.FAILED,
                        error=str(exc),
                    ),
                )
            )
        raise
    except Exception as exc:  # pragma: no cover - Celery handles retries
        logger.exception("email_delivery_error", notification_id=notification_id)
        if notification_id is not None:
            asyncio.run(
                _update_email_status(
                    notification_id,
                    EmailDeliveryStatus(
                        status=EmailDeliveryState.RETRYING,
                        error=str(exc),
                    ),
                )
            )
        raise self.retry(exc=exc)

    if notification_id is not None:
        asyncio.run(
            _update_email_status(
                notification_id,
                EmailDeliveryStatus(
                    status=EmailDeliveryState.SENT,
                    status_code=result.status_code,
                    status_text=result.status_text,
                    message_id=result.message_id,
                ),
            )
        )

    return {
        "status_code": result.status_code,
        "status_text": result.status_text,
        "message_id": result.message_id,
    }


__all__ = ["send_email_notification"]
