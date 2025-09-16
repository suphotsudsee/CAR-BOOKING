"""Pydantic schemas for driver management."""

from __future__ import annotations

from datetime import date, datetime, time
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field, RootModel, field_validator, model_validator

from app.models.driver import DriverStatus

_WEEKDAY_NAMES = {
    "monday",
    "tuesday",
    "wednesday",
    "thursday",
    "friday",
    "saturday",
    "sunday",
}


class DriverAvailabilityWindow(BaseModel):
    """Represents a single day's availability window."""

    start: Optional[time] = None
    end: Optional[time] = None
    available: bool = True

    @model_validator(mode="after")
    def _validate_window(self) -> "DriverAvailabilityWindow":
        """Ensure availability windows include sensible start and end times."""

        if not self.available:
            return self

        if self.start is None or self.end is None:
            msg = "Available slots must define both start and end times"
            raise ValueError(msg)

        if self.start >= self.end:
            msg = "Availability end time must be after the start time"
            raise ValueError(msg)

        return self


class DriverAvailabilitySchedule(RootModel[dict[str, DriverAvailabilityWindow]]):
    """A weekly schedule keyed by weekday names."""

    @model_validator(mode="before")
    @classmethod
    def _coerce_dict(
        cls, value: Any
    ) -> dict[str, DriverAvailabilityWindow]:
        """Accept mappings and normalise weekday keys."""

        if value is None:
            msg = "Availability schedule cannot be null"
            raise TypeError(msg)

        if isinstance(value, DriverAvailabilitySchedule):
            return value.root

        if not isinstance(value, dict):
            msg = "Availability schedule must be a mapping"
            raise TypeError(msg)

        normalised: dict[str, DriverAvailabilityWindow] = {}
        for raw_day, details in value.items():
            if not isinstance(raw_day, str):
                msg = "Weekday keys must be strings"
                raise TypeError(msg)

            day = raw_day.strip().lower()
            if day not in _WEEKDAY_NAMES:
                msg = f"Unknown weekday '{raw_day}'"
                raise ValueError(msg)

            normalised[day] = details

        return normalised

    @model_validator(mode="after")
    def _ensure_serialisable(self) -> "DriverAvailabilitySchedule":
        """Force evaluation of nested models for validation."""

        # Accessing the values ensures nested models are validated
        for slot in self.root.values():
            _ = slot
        return self

    def as_dict(self) -> dict[str, Any]:
        """Return a JSON-serialisable representation of the schedule."""

        return {day: slot.model_dump(mode="json") for day, slot in self.root.items()}


class _DriverCommon(BaseModel):
    """Shared validations for driver input schemas."""

    full_name: str = Field(..., max_length=120)
    phone_number: Optional[str] = Field(default=None, max_length=30)
    license_type: str = Field(default="B", max_length=20)
    license_expiry_date: date
    status: DriverStatus = DriverStatus.ACTIVE
    user_id: Optional[int] = None
    availability_schedule: Optional[DriverAvailabilitySchedule] = None

    @field_validator("full_name")
    @classmethod
    def _normalise_full_name(cls, value: str) -> str:
        trimmed = " ".join(value.split())
        if not trimmed:
            msg = "Full name must not be empty"
            raise ValueError(msg)
        return trimmed

    @field_validator("phone_number")
    @classmethod
    def _validate_phone(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        trimmed = value.strip()
        if not trimmed:
            return None
        allowed_chars = set("+0123456789 -")
        if any(char not in allowed_chars for char in trimmed):
            msg = "Phone number may only contain digits, spaces, '+', or '-'"
            raise ValueError(msg)
        if len(trimmed) < 6:
            msg = "Phone number must be at least 6 characters long"
            raise ValueError(msg)
        return trimmed

    @field_validator("license_type")
    @classmethod
    def _normalise_license_type(cls, value: str) -> str:
        trimmed = value.strip().upper()
        if not trimmed:
            msg = "License type must not be empty"
            raise ValueError(msg)
        return trimmed

    @field_validator("license_expiry_date")
    @classmethod
    def _validate_expiry(cls, value: date) -> date:
        if value < date.today():
            msg = "License expiry date cannot be in the past"
            raise ValueError(msg)
        return value


class DriverCreate(_DriverCommon):
    """Input schema for registering a new driver."""

    employee_code: str = Field(..., max_length=30)
    license_number: str = Field(..., max_length=60)

    @field_validator("employee_code")
    @classmethod
    def _normalise_employee_code(cls, value: str) -> str:
        trimmed = "".join(value.split()).upper()
        if not trimmed:
            msg = "Employee code must not be empty"
            raise ValueError(msg)
        return trimmed

    @field_validator("license_number")
    @classmethod
    def _normalise_license_number(cls, value: str) -> str:
        trimmed = " ".join(value.split()).upper()
        if not trimmed:
            msg = "License number must not be empty"
            raise ValueError(msg)
        return trimmed


class DriverUpdate(BaseModel):
    """Schema for updating driver profile information."""

    employee_code: Optional[str] = Field(default=None, max_length=30)
    full_name: Optional[str] = Field(default=None, max_length=120)
    phone_number: Optional[str] = Field(default=None, max_length=30)
    license_number: Optional[str] = Field(default=None, max_length=60)
    license_type: Optional[str] = Field(default=None, max_length=20)
    license_expiry_date: Optional[date] = None
    status: Optional[DriverStatus] = None
    user_id: Optional[int] = None
    availability_schedule: Optional[DriverAvailabilitySchedule] = None

    model_config = ConfigDict(extra="forbid")

    @field_validator("employee_code")
    @classmethod
    def _normalise_employee_code(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        trimmed = "".join(value.split()).upper()
        if not trimmed:
            msg = "Employee code must not be empty"
            raise ValueError(msg)
        return trimmed

    @field_validator("full_name")
    @classmethod
    def _normalise_full_name(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        trimmed = " ".join(value.split())
        if not trimmed:
            msg = "Full name must not be empty"
            raise ValueError(msg)
        return trimmed

    @field_validator("phone_number")
    @classmethod
    def _validate_phone(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        trimmed = value.strip()
        if not trimmed:
            return None
        allowed_chars = set("+0123456789 -")
        if any(char not in allowed_chars for char in trimmed):
            msg = "Phone number may only contain digits, spaces, '+', or '-'"
            raise ValueError(msg)
        if len(trimmed) < 6:
            msg = "Phone number must be at least 6 characters long"
            raise ValueError(msg)
        return trimmed

    @field_validator("license_number")
    @classmethod
    def _normalise_license_number(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        trimmed = " ".join(value.split()).upper()
        if not trimmed:
            msg = "License number must not be empty"
            raise ValueError(msg)
        return trimmed

    @field_validator("license_type")
    @classmethod
    def _normalise_license_type(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        trimmed = value.strip().upper()
        if not trimmed:
            msg = "License type must not be empty"
            raise ValueError(msg)
        return trimmed

    @field_validator("license_expiry_date")
    @classmethod
    def _validate_expiry(cls, value: Optional[date]) -> Optional[date]:
        if value is None:
            return None
        if value < date.today():
            msg = "License expiry date cannot be in the past"
            raise ValueError(msg)
        return value


class DriverStatusUpdate(BaseModel):
    """Schema for updating only the driver's status."""

    status: DriverStatus


class DriverAvailabilityUpdate(BaseModel):
    """Schema dedicated to updating driver availability schedules."""

    availability_schedule: DriverAvailabilitySchedule


class DriverRead(_DriverCommon):
    """Schema returned via the API for driver records."""

    id: int
    employee_code: str
    license_number: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DriverLicenseExpiryNotification(BaseModel):
    """Payload describing a driver whose license is expiring soon."""

    driver_id: int
    employee_code: str
    full_name: str
    license_number: str
    license_expiry_date: date
    days_until_expiry: int
