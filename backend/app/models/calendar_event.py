"""Calendar event models for resource scheduling."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Optional

from sqlalchemy import DateTime, Enum as SQLAlchemyEnum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin


class CalendarResourceType(str, Enum):
    """Resource types supported by the calendar."""

    VEHICLE = "vehicle"
    DRIVER = "driver"


class CalendarEventType(str, Enum):
    """Classification of calendar events."""

    BOOKING = "booking"
    CUSTOM = "custom"
    MAINTENANCE = "maintenance"
    BLOCKED = "blocked"


class ResourceCalendarEvent(Base, TimestampMixin):
    """Manual calendar events attached to vehicles or drivers."""

    __tablename__ = "resource_calendar_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    resource_type: Mapped[CalendarResourceType] = mapped_column(
        SQLAlchemyEnum(CalendarResourceType, name="calendarresourcetype"),
        nullable=False,
        index=True,
    )
    resource_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    start_datetime: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
    end_datetime: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
    event_type: Mapped[CalendarEventType] = mapped_column(
        SQLAlchemyEnum(CalendarEventType, name="calendareventtype"),
        nullable=False,
        default=CalendarEventType.CUSTOM,
    )
    created_by_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("users.id"), nullable=True, index=True
    )
    booking_request_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("booking_requests.id"), nullable=True, index=True
    )

    created_by = relationship("User")

    def __repr__(self) -> str:
        return (
            f"<ResourceCalendarEvent(id={self.id}, resource_type={self.resource_type}, "
            f"resource_id={self.resource_id}, title='{self.title}')>"
        )
