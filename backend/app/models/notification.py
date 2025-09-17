"""Notification-related database models and helper dataclasses."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional

from sqlalchemy import JSON, DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin


class NotificationChannel(str, Enum):
    """Supported delivery channels for notifications."""

    IN_APP = "in_app"
    EMAIL = "email"
    LINE = "line"


class Notification(Base, TimestampMixin):
    """Persistent notification message for a user."""

    __tablename__ = "notifications"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    message: Mapped[str] = mapped_column(String(2000), nullable=False)
    category: Mapped[str] = mapped_column(String(50), nullable=False, default="general")
    data: Mapped[Optional[dict[str, Any]]] = mapped_column(JSON, nullable=True)
    read_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    delivered_channels: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    delivery_errors: Mapped[dict[str, str]] = mapped_column(JSON, nullable=False, default=dict)

    user = relationship("User", back_populates="notifications")

    def mark_read(self, timestamp: Optional[datetime] = None) -> None:
        """Mark the notification as read at *timestamp* (defaults to now)."""

        if self.read_at is not None:
            return
        self.read_at = timestamp or datetime.now(timezone.utc)


class NotificationPreference(Base, TimestampMixin):
    """User-specific notification delivery preferences."""

    __tablename__ = "notification_preferences"

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    in_app_enabled: Mapped[bool] = mapped_column(default=True, nullable=False)
    email_enabled: Mapped[bool] = mapped_column(default=False, nullable=False)
    line_enabled: Mapped[bool] = mapped_column(default=False, nullable=False)
    line_access_token: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    user = relationship("User", back_populates="notification_preferences")

    def allow_channel(self, channel: NotificationChannel) -> bool:
        """Return whether *channel* is enabled under this preference."""

        if channel is NotificationChannel.IN_APP:
            return self.in_app_enabled
        if channel is NotificationChannel.EMAIL:
            return self.email_enabled
        if channel is NotificationChannel.LINE:
            return self.line_enabled and bool(self.line_access_token)
        return False


class EmailDeliveryState(str, Enum):
    """High level states representing email delivery progress."""

    QUEUED = "queued"
    RETRYING = "retrying"
    SENT = "sent"
    FAILED = "failed"


@dataclass(slots=True)
class EmailDeliveryStatus:
    """Details recorded for an email delivery attempt."""

    status: EmailDeliveryState
    status_code: Optional[int] = None
    status_text: Optional[str] = None
    message_id: Optional[str] = None
    error: Optional[str] = None
    attempts: int = 0

    def to_dict(self) -> dict[str, Any]:
        """Serialise the status to a JSON-compatible dictionary."""

        return {
            "status": self.status.value,
            "status_code": self.status_code,
            "status_text": self.status_text,
            "message_id": self.message_id,
            "error": self.error,
            "attempts": self.attempts,
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "EmailDeliveryStatus":
        """Create a status instance from a stored dictionary."""

        status_value = payload.get("status", EmailDeliveryState.QUEUED.value)
        return cls(
            status=EmailDeliveryState(status_value),
            status_code=payload.get("status_code"),
            status_text=payload.get("status_text"),
            message_id=payload.get("message_id"),
            error=payload.get("error"),
            attempts=int(payload.get("attempts", 0)),
        )


@dataclass(slots=True)
class EmailNotification:
    """Payload describing an email notification to be delivered."""

    to_email: str
    subject: str
    template_name: str
    context: Optional[dict[str, Any]] = None
    cc: Optional[list[str]] = None
    bcc: Optional[list[str]] = None
    reply_to: Optional[str] = None
    notification_id: Optional[int] = None
    user_id: Optional[int] = None
    metadata: Optional[dict[str, Any]] = None

    def to_payload(self) -> dict[str, Any]:
        """Serialise the notification for Celery task transport."""

        return {
            "to_email": self.to_email,
            "subject": self.subject,
            "template_name": self.template_name,
            "context": self.context or {},
            "cc": self.cc or [],
            "bcc": self.bcc or [],
            "reply_to": self.reply_to,
            "notification_id": self.notification_id,
            "user_id": self.user_id,
            "metadata": self.metadata or {},
        }

    @classmethod
    def from_payload(cls, payload: dict[str, Any]) -> "EmailNotification":
        """Rehydrate a notification from a Celery payload."""

        return cls(
            to_email=payload["to_email"],
            subject=payload["subject"],
            template_name=payload["template_name"],
            context=payload.get("context") or {},
            cc=list(payload.get("cc") or []),
            bcc=list(payload.get("bcc") or []),
            reply_to=payload.get("reply_to"),
            notification_id=payload.get("notification_id"),
            user_id=payload.get("user_id"),
            metadata=payload.get("metadata") or {},
        )


__all__ = [
    "EmailDeliveryState",
    "EmailDeliveryStatus",
    "EmailNotification",
    "Notification",
    "NotificationChannel",
    "NotificationPreference",
]
