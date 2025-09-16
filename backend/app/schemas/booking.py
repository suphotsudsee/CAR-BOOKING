"""Pydantic schemas for booking request operations."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.models.booking import BookingStatus, VehiclePreference


def _normalise_required_text(value: str, field_display: str) -> str:
    """Strip and validate that *value* is not empty."""

    normalised = " ".join(value.split())
    if not normalised:
        raise ValueError(f"{field_display} must not be empty")
    return normalised


def _normalise_optional_text(value: Optional[str]) -> Optional[str]:
    """Strip whitespace and return ``None`` for empty strings."""

    if value is None:
        return None
    trimmed = value.strip()
    return trimmed or None


def _validate_datetime_window(start: datetime, end: datetime) -> None:
    """Ensure the booking window represented by *start* and *end* is valid."""

    if start >= end:
        msg = "End datetime must be after the start datetime"
        raise ValueError(msg)

    if (start.tzinfo is None) != (end.tzinfo is None):
        msg = "Start and end datetimes must both be naive or both timezone-aware"
        raise ValueError(msg)


class BookingRequestBase(BaseModel):
    """Fields shared by booking request create and read schemas."""

    department: Optional[str] = Field(default=None, max_length=100)
    purpose: str = Field(..., max_length=500)
    passenger_count: int = Field(1, ge=1, le=100)
    start_datetime: datetime
    end_datetime: datetime
    pickup_location: str = Field(..., max_length=500)
    dropoff_location: str = Field(..., max_length=500)
    vehicle_preference: VehiclePreference = VehiclePreference.ANY
    special_requirements: Optional[str] = Field(default=None, max_length=2000)

    model_config = ConfigDict(extra="forbid")

    @field_validator("purpose")
    @classmethod
    def _normalise_purpose(cls, value: str) -> str:
        return _normalise_required_text(value, "Purpose")

    @field_validator("pickup_location")
    @classmethod
    def _normalise_pickup(cls, value: str) -> str:
        return _normalise_required_text(value, "Pickup location")

    @field_validator("dropoff_location")
    @classmethod
    def _normalise_dropoff(cls, value: str) -> str:
        return _normalise_required_text(value, "Drop-off location")

    @field_validator("department")
    @classmethod
    def _normalise_department(
        cls, value: Optional[str]
    ) -> Optional[str]:
        return _normalise_optional_text(value)

    @field_validator("special_requirements")
    @classmethod
    def _normalise_special_requirements(
        cls, value: Optional[str]
    ) -> Optional[str]:
        return _normalise_optional_text(value)

    @model_validator(mode="after")
    def _validate_window(self) -> "BookingRequestBase":
        _validate_datetime_window(self.start_datetime, self.end_datetime)
        return self


class BookingRequestCreate(BookingRequestBase):
    """Schema for creating booking requests."""

    requester_id: Optional[int] = Field(default=None, ge=1)
    status: BookingStatus = BookingStatus.DRAFT

    @model_validator(mode="after")
    def _validate_initial_status(self) -> "BookingRequestCreate":
        if self.status not in {BookingStatus.DRAFT, BookingStatus.REQUESTED}:
            msg = "Booking requests can only be created in DRAFT or REQUESTED status"
            raise ValueError(msg)
        return self


class BookingRequestUpdate(BaseModel):
    """Schema for updating booking request details."""

    department: Optional[str] = Field(default=None, max_length=100)
    purpose: Optional[str] = Field(default=None, max_length=500)
    passenger_count: Optional[int] = Field(default=None, ge=1, le=100)
    start_datetime: Optional[datetime] = None
    end_datetime: Optional[datetime] = None
    pickup_location: Optional[str] = Field(default=None, max_length=500)
    dropoff_location: Optional[str] = Field(default=None, max_length=500)
    vehicle_preference: Optional[VehiclePreference] = None
    special_requirements: Optional[str] = Field(default=None, max_length=2000)

    model_config = ConfigDict(extra="forbid")

    @field_validator("department")
    @classmethod
    def _normalise_department(
        cls, value: Optional[str]
    ) -> Optional[str]:
        return _normalise_optional_text(value)

    @field_validator("purpose")
    @classmethod
    def _normalise_purpose(
        cls, value: Optional[str]
    ) -> Optional[str]:
        if value is None:
            return None
        return _normalise_required_text(value, "Purpose")

    @field_validator("pickup_location")
    @classmethod
    def _normalise_pickup(
        cls, value: Optional[str]
    ) -> Optional[str]:
        if value is None:
            return None
        return _normalise_required_text(value, "Pickup location")

    @field_validator("dropoff_location")
    @classmethod
    def _normalise_dropoff(
        cls, value: Optional[str]
    ) -> Optional[str]:
        if value is None:
            return None
        return _normalise_required_text(value, "Drop-off location")

    @field_validator("special_requirements")
    @classmethod
    def _normalise_special_requirements(
        cls, value: Optional[str]
    ) -> Optional[str]:
        return _normalise_optional_text(value)

    @model_validator(mode="after")
    def _validate_partial_window(self) -> "BookingRequestUpdate":
        start = self.start_datetime
        end = self.end_datetime
        if start is not None and end is not None:
            _validate_datetime_window(start, end)
        return self


class BookingStatusUpdate(BaseModel):
    """Schema for updating the booking request status."""

    status: BookingStatus

    model_config = ConfigDict(extra="forbid")


class BookingRequestRead(BookingRequestBase):
    """Response schema for booking requests."""

    id: int
    requester_id: int
    status: BookingStatus
    submitted_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

