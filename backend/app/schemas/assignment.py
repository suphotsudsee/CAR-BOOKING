"""Schemas and helper data structures for booking assignments."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator
from app.models.vehicle import VehicleType


def _normalise_optional_text(value: Optional[str]) -> Optional[str]:
    """Return a stripped version of ``value`` or ``None`` for empty strings."""

    if value is None:
        return None
    trimmed = value.strip()
    return trimmed or None


@dataclass(slots=True)
class AssignmentVehicleSuggestionData:
    """Lightweight representation of a suggested vehicle."""

    id: int
    registration_number: str
    vehicle_type: VehicleType
    seating_capacity: int
    matches_preference: bool
    spare_seats: int


@dataclass(slots=True)
class AssignmentDriverSuggestionData:
    """Lightweight representation of a suggested driver."""

    id: int
    full_name: str
    license_number: str


@dataclass(slots=True)
class AssignmentSuggestionData:
    """Pairing of a vehicle and driver suggestion."""

    vehicle: AssignmentVehicleSuggestionData
    driver: AssignmentDriverSuggestionData
    score: int
    reasons: list[str]


class AssignmentCreate(BaseModel):
    """Payload for creating a new assignment."""

    booking_request_id: int = Field(..., ge=1)
    vehicle_id: Optional[int] = Field(default=None, ge=1)
    driver_id: Optional[int] = Field(default=None, ge=1)
    notes: Optional[str] = Field(default=None, max_length=2000)
    auto_assign: bool = True

    model_config = ConfigDict(extra="forbid")

    @field_validator("notes")
    @classmethod
    def _normalise_notes(cls, value: Optional[str]) -> Optional[str]:
        return _normalise_optional_text(value)

    @model_validator(mode="after")
    def _validate_manual_override(self) -> "AssignmentCreate":
        if not self.auto_assign and (self.vehicle_id is None or self.driver_id is None):
            msg = "Manual assignment requires both vehicle_id and driver_id"
            raise ValueError(msg)
        return self


class AssignmentUpdate(BaseModel):
    """Payload for updating an existing assignment."""

    vehicle_id: Optional[int] = Field(default=None, ge=1)
    driver_id: Optional[int] = Field(default=None, ge=1)
    notes: Optional[str] = Field(default=None, max_length=2000)
    auto_assign: bool = False

    model_config = ConfigDict(extra="forbid")

    @field_validator("notes")
    @classmethod
    def _normalise_notes(cls, value: Optional[str]) -> Optional[str]:
        return _normalise_optional_text(value)


class AssignmentRead(BaseModel):
    """Read model for persisted assignments."""

    id: int
    booking_request_id: int
    vehicle_id: int
    driver_id: int
    assigned_by: int
    assigned_at: datetime
    notes: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class AssignmentVehicleSuggestion(BaseModel):
    """Detailed information about a suggested vehicle."""

    id: int
    registration_number: str
    vehicle_type: VehicleType
    seating_capacity: int
    matches_preference: bool
    spare_seats: int

    model_config = ConfigDict(from_attributes=True)


class AssignmentDriverSuggestion(BaseModel):
    """Detailed information about a suggested driver."""

    id: int
    full_name: str
    license_number: str

    model_config = ConfigDict(from_attributes=True)


class AssignmentSuggestionRead(BaseModel):
    """Response model for assignment suggestions."""

    vehicle: AssignmentVehicleSuggestion
    driver: AssignmentDriverSuggestion
    score: int
    reasons: list[str]

    model_config = ConfigDict(from_attributes=True)


__all__ = [
    "AssignmentCreate",
    "AssignmentDriverSuggestion",
    "AssignmentDriverSuggestionData",
    "AssignmentRead",
    "AssignmentSuggestionData",
    "AssignmentSuggestionRead",
    "AssignmentUpdate",
    "AssignmentVehicleSuggestion",
    "AssignmentVehicleSuggestionData",
]
