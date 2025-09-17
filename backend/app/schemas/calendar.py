"""Pydantic schemas for calendar operations."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.models.booking import BookingStatus
from app.models.calendar_event import CalendarEventType, CalendarResourceType


class CalendarEventSource(str, Enum):
    """Origin of a calendar event entry."""

    ASSIGNMENT = "assignment"
    MANUAL = "manual"


class CalendarRealtimeAction(str, Enum):
    """Action performed on a manual calendar event."""

    CREATED = "created"
    UPDATED = "updated"
    DELETED = "deleted"


class CalendarEventBase(BaseModel):
    """Shared fields for manual calendar events."""

    resource_type: CalendarResourceType
    resource_id: int = Field(..., ge=1)
    title: str = Field(..., max_length=200)
    description: Optional[str] = None
    start: datetime
    end: datetime
    event_type: CalendarEventType = CalendarEventType.CUSTOM
    booking_request_id: Optional[int] = Field(None, ge=1)

    @model_validator(mode="after")
    def _ensure_valid_range(self) -> "CalendarEventBase":
        if self.start >= self.end:
            raise ValueError("Event end time must be after the start time")
        return self


class CalendarEventCreate(CalendarEventBase):
    """Schema for creating manual calendar events."""

    model_config = ConfigDict(from_attributes=True)


class CalendarEventUpdate(BaseModel):
    """Schema for updating manual calendar events."""

    title: Optional[str] = Field(None, max_length=200)
    description: Optional[str] = None
    start: Optional[datetime] = None
    end: Optional[datetime] = None
    event_type: Optional[CalendarEventType] = None
    booking_request_id: Optional[int] = Field(None, ge=1)

    @model_validator(mode="after")
    def _ensure_valid_range(self) -> "CalendarEventUpdate":
        if self.start is not None and self.end is not None and self.start >= self.end:
            raise ValueError("Event end time must be after the start time")
        return self


class CalendarEventRead(CalendarEventBase):
    """Schema returned for manual calendar events."""

    id: int
    created_by_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CalendarEventView(BaseModel):
    """Calendar entry representing either manual events or assignments."""

    reference_id: str
    resource_type: CalendarResourceType
    resource_id: int
    title: str
    start: datetime
    end: datetime
    event_type: CalendarEventType
    source: CalendarEventSource
    description: Optional[str] = None
    booking_request_id: Optional[int] = None
    booking_status: Optional[BookingStatus] = None
    assignment_id: Optional[int] = None
    calendar_event_id: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)


class CalendarConflictView(BaseModel):
    """Conflict window between overlapping events."""

    start: datetime
    end: datetime
    event_reference_ids: list[str]

    model_config = ConfigDict(from_attributes=True)


class CalendarResourceView(BaseModel):
    """Events grouped under a particular resource."""

    resource_type: CalendarResourceType
    resource_id: int
    resource_name: str
    events: list[CalendarEventView]
    conflicts: list[CalendarConflictView]

    model_config = ConfigDict(from_attributes=True)


class CalendarRealtimeEvent(BaseModel):
    """Payload describing a manual calendar event update."""

    action: CalendarRealtimeAction
    event: Optional[CalendarEventView] = None
    calendar_event_id: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)
