"""Schemas for administrative system management."""

from __future__ import annotations

from datetime import date, datetime, time
from typing import Any, Optional

from pydantic import BaseModel, Field, ConfigDict, field_validator, model_validator


class WorkingHourBase(BaseModel):
    """Common fields for working hour representations."""

    day_of_week: str = Field(..., description="Lowercase day of week, e.g. 'monday'")
    start_time: time = Field(..., description="Working window start time")
    end_time: time = Field(..., description="Working window end time")

    @field_validator("day_of_week")
    @classmethod
    def _lowercase_day(cls, value: str) -> str:
        return value.lower()

    @model_validator(mode="after")
    def _validate_time_order(cls, values: "WorkingHourBase") -> "WorkingHourBase":
        if values.end_time <= values.start_time:
            raise ValueError("end_time must be after start_time")
        return values


class WorkingHourCreate(WorkingHourBase):
    """Payload for creating or updating working hours."""


class WorkingHourRead(WorkingHourBase):
    """Working hour representation returned to clients."""

    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class HolidayBase(BaseModel):
    """Common holiday data."""

    date: date
    name: str
    description: Optional[str] = None


class HolidayCreate(HolidayBase):
    """Payload for creating holidays."""


class HolidayRead(HolidayBase):
    """Holiday representation returned to clients."""

    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SystemConfigurationBase(BaseModel):
    """Shared configuration fields."""

    maintenance_mode: bool = False
    maintenance_message: Optional[str] = None
    require_booking_approval: bool = True
    max_pending_bookings_per_user: int = Field(3, ge=0)
    max_active_bookings_per_user: int = Field(2, ge=0)
    auto_cancel_pending_hours: int = Field(48, ge=0)
    working_day_start: time = Field(time(8, 0))
    working_day_end: time = Field(time(18, 0))
    working_days: list[str] = Field(
        default_factory=lambda: [
            "monday",
            "tuesday",
            "wednesday",
            "thursday",
            "friday",
        ]
    )
    approval_escalation_hours: int = Field(24, ge=0)
    booking_lead_time_hours: int = Field(4, ge=0)

    @field_validator("working_days", mode="before")
    @classmethod
    def _normalise_days(cls, value: Any) -> Any:
        if value is None:
            return value
        return [str(day).lower() for day in value]


class SystemConfigurationUpdate(SystemConfigurationBase):
    """Patch payload for system configuration updates."""

    maintenance_mode: Optional[bool] = None
    maintenance_message: Optional[str] = None
    require_booking_approval: Optional[bool] = None
    max_pending_bookings_per_user: Optional[int] = Field(None, ge=0)
    max_active_bookings_per_user: Optional[int] = Field(None, ge=0)
    auto_cancel_pending_hours: Optional[int] = Field(None, ge=0)
    working_day_start: Optional[time] = None
    working_day_end: Optional[time] = None
    working_days: Optional[list[str]] = None
    approval_escalation_hours: Optional[int] = Field(None, ge=0)
    booking_lead_time_hours: Optional[int] = Field(None, ge=0)


class SystemConfigurationRead(SystemConfigurationBase):
    """Full configuration view returned to clients."""

    id: int
    created_at: datetime
    updated_at: datetime
    holidays: list[HolidayRead] = Field(default_factory=list)
    working_hours: list[WorkingHourRead] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class AuditLogRead(BaseModel):
    """Audit log entry representation."""

    id: int
    user_id: Optional[int]
    action: str
    resource: str
    status_code: int
    ip_address: Optional[str]
    user_agent: Optional[str]
    context: Optional[dict[str, Any]]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AuditLogSearchResponse(BaseModel):
    """Envelope for audit log search results."""

    results: list[AuditLogRead]
    total: int


class HealthRecordCreate(BaseModel):
    """Payload to record a health check."""

    component: str
    status: str
    severity: str = Field("info")
    details: Optional[str] = None
    extra: Optional[dict[str, Any]] = None


class HealthRecordRead(BaseModel):
    """Health record representation."""

    id: int
    component: str
    status: str
    severity: str
    details: Optional[str]
    extra: Optional[dict[str, Any]]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class HealthSummary(BaseModel):
    """Aggregated view of system health."""

    overall_status: str
    components: list[dict[str, Any]]


class UserActivityEntry(BaseModel):
    """Aggregated activity metrics for a user."""

    user_id: int
    username: str
    full_name: str
    actions: int
    last_activity: datetime


class UserActivityReport(BaseModel):
    """Activity report response payload."""

    generated_at: datetime = Field(default_factory=datetime.utcnow)
    entries: list[UserActivityEntry]


__all__ = [
    "AuditLogRead",
    "AuditLogSearchResponse",
    "HealthRecordCreate",
    "HealthRecordRead",
    "HealthSummary",
    "HolidayCreate",
    "HolidayRead",
    "SystemConfigurationRead",
    "SystemConfigurationUpdate",
    "UserActivityEntry",
    "UserActivityReport",
    "WorkingHourCreate",
    "WorkingHourRead",
]
