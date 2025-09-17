"""Notification-related database models."""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Optional

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
    data: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
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


__all__ = [
    "Notification",
    "NotificationChannel",
    "NotificationPreference",
]

