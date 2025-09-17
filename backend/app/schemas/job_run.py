"""Schemas for job execution tracking."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, computed_field, field_validator

from app.models.job_run import JobRunStatus


def _normalise_optional_text(value: Optional[str]) -> Optional[str]:
    """Return a trimmed version of ``value`` or ``None`` when empty."""

    if value is None:
        return None
    trimmed = value.strip()
    return trimmed or None


def _normalise_string_list(value: Optional[list[str]]) -> Optional[list[str]]:
    """Return a list of non-empty, trimmed strings or ``None``."""

    if value is None:
        return None

    normalised: list[str] = []
    for item in value:
        if item is None:
            continue
        trimmed = item.strip()
        if trimmed:
            normalised.append(trimmed)

    return normalised or None


class JobRunCheckIn(BaseModel):
    """Payload for recording a booking job check-in."""

    checkin_datetime: datetime
    checkin_mileage: int = Field(..., ge=0)
    checkin_location: Optional[str] = Field(default=None, max_length=500)
    checkin_images: Optional[list[str]] = None

    model_config = ConfigDict(extra="forbid")

    @field_validator("checkin_location")
    @classmethod
    def _normalise_location(cls, value: Optional[str]) -> Optional[str]:
        return _normalise_optional_text(value)

    @field_validator("checkin_images")
    @classmethod
    def _normalise_images(
        cls, value: Optional[list[str]]
    ) -> Optional[list[str]]:
        return _normalise_string_list(value)


class JobRunCheckOut(BaseModel):
    """Payload for recording a booking job check-out."""

    checkout_datetime: datetime
    checkout_mileage: int = Field(..., ge=0)
    checkout_location: Optional[str] = Field(default=None, max_length=500)
    checkout_images: Optional[list[str]] = None
    fuel_cost: Decimal = Field(default=Decimal("0.00"), ge=0)
    toll_cost: Decimal = Field(default=Decimal("0.00"), ge=0)
    other_expenses: Decimal = Field(default=Decimal("0.00"), ge=0)
    expense_receipts: Optional[list[str]] = None
    incident_report: Optional[str] = Field(default=None, max_length=2000)
    incident_images: Optional[list[str]] = None

    model_config = ConfigDict(extra="forbid")

    @field_validator("checkout_location", "incident_report")
    @classmethod
    def _normalise_text_fields(
        cls, value: Optional[str]
    ) -> Optional[str]:
        return _normalise_optional_text(value)

    @field_validator(
        "checkout_images", "expense_receipts", "incident_images"
    )
    @classmethod
    def _normalise_lists(
        cls, value: Optional[list[str]]
    ) -> Optional[list[str]]:
        return _normalise_string_list(value)


class JobRunRead(BaseModel):
    """Read model representing a job run record."""

    id: int
    booking_request_id: int
    status: JobRunStatus
    checkin_datetime: Optional[datetime] = None
    checkin_mileage: Optional[int] = None
    checkin_location: Optional[str] = None
    checkin_images: Optional[list[str]] = None
    checkout_datetime: Optional[datetime] = None
    checkout_mileage: Optional[int] = None
    checkout_location: Optional[str] = None
    checkout_images: Optional[list[str]] = None
    fuel_cost: Decimal
    toll_cost: Decimal
    other_expenses: Decimal
    expense_receipts: Optional[list[str]] = None
    incident_report: Optional[str] = None
    incident_images: Optional[list[str]] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

    @computed_field(return_type=Optional[int])
    def total_distance(self) -> Optional[int]:
        """Expose the total distance travelled for API responses."""

        if self.checkin_mileage is None or self.checkout_mileage is None:
            return None
        return self.checkout_mileage - self.checkin_mileage

    @computed_field(return_type=Decimal)
    def total_expenses(self) -> Decimal:
        """Expose the aggregated expenses for API responses."""

        return self.fuel_cost + self.toll_cost + self.other_expenses


__all__ = ["JobRunCheckIn", "JobRunCheckOut", "JobRunRead"]
