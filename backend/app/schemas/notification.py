"""Pydantic schemas for notification APIs."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from app.models.notification import NotificationChannel


class NotificationRead(BaseModel):
    """Notification payload returned to clients."""

    id: int
    title: str
    message: str
    category: str
    data: dict = Field(default_factory=dict)
    created_at: datetime
    read_at: Optional[datetime] = None
    delivered_channels: list[str] = Field(default_factory=list)
    delivery_errors: dict[str, str] = Field(default_factory=dict)

    model_config = ConfigDict(from_attributes=True)

    @property
    def is_read(self) -> bool:
        return self.read_at is not None


class NotificationMarkReadResponse(BaseModel):
    """Response returned after marking a notification as read."""

    notification: NotificationRead


class NotificationPreferenceRead(BaseModel):
    """Notification preference settings for a user."""

    in_app_enabled: bool
    email_enabled: bool
    line_enabled: bool
    line_token_registered: bool
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class NotificationPreferenceUpdate(BaseModel):
    """Payload for updating notification preferences."""

    in_app_enabled: Optional[bool] = None
    email_enabled: Optional[bool] = None
    line_enabled: Optional[bool] = None
    line_access_token: Optional[str] = Field(default=None, min_length=0, max_length=255)

    model_config = ConfigDict(extra="forbid")


class NotificationCreateRequest(BaseModel):
    """Internal schema for manually triggering notifications (testing/admin)."""

    title: str = Field(..., max_length=200)
    message: str = Field(..., max_length=2000)
    category: str = Field(default="general", max_length=50)
    metadata: Optional[dict] = None
    channels: Optional[list[NotificationChannel]] = None

    model_config = ConfigDict(extra="forbid")


__all__ = [
    "NotificationCreateRequest",
    "NotificationPreferenceRead",
    "NotificationPreferenceUpdate",
    "NotificationRead",
    "NotificationMarkReadResponse",
]

