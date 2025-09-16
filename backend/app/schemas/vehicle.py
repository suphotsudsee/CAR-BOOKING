"""Pydantic schemas for vehicle management."""

from __future__ import annotations

from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, ValidationInfo, field_validator

from app.models.vehicle import FuelType, VehicleStatus, VehicleType


def _normalise_basic_text(value: str, field_display: str) -> str:
    """Strip and validate that *value* contains non-whitespace characters."""
    trimmed = value.strip()
    if not trimmed:
        raise ValueError(f"{field_display.capitalize()} must not be empty")
    return trimmed


def _normalise_registration(value: str) -> str:
    """Normalise the registration number for consistent storage."""
    normalised = " ".join(value.strip().upper().split())
    if not normalised:
        raise ValueError("Registration number must not be empty")
    return normalised


def _validate_year(year: Optional[int]) -> Optional[int]:
    """Ensure the manufacturing year is within a sensible range."""
    if year is None:
        return None

    current_year = date.today().year + 1
    if year < 1980 or year > current_year:
        raise ValueError(
            "Year manufactured must be between 1980 and one year beyond the current year"
        )
    return year


class VehicleBase(BaseModel):
    """Shared fields for vehicle operations."""

    vehicle_type: VehicleType
    brand: str = Field(..., max_length=60)
    model: str = Field(..., max_length=60)
    year_manufactured: Optional[int] = None
    seating_capacity: int = Field(..., ge=1, le=100)
    fuel_type: FuelType = FuelType.GASOLINE
    status: VehicleStatus = VehicleStatus.ACTIVE
    current_mileage: int = Field(0, ge=0)
    tax_expiry_date: Optional[date] = None
    insurance_expiry_date: Optional[date] = None
    inspection_expiry_date: Optional[date] = None
    notes: Optional[str] = None

    @field_validator("brand", "model")
    @classmethod
    def _validate_text_fields(
        cls, value: str, info: ValidationInfo
    ) -> str:
        return _normalise_basic_text(value, info.field_name.replace("_", " "))

    @field_validator("notes")
    @classmethod
    def _normalise_notes(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        trimmed = value.strip()
        return trimmed or None

    @field_validator("year_manufactured")
    @classmethod
    def _check_year(cls, value: Optional[int]) -> Optional[int]:
        return _validate_year(value)


class VehicleCreate(VehicleBase):
    """Schema for creating new vehicles."""

    registration_number: str = Field(..., min_length=1, max_length=20)

    @field_validator("registration_number")
    @classmethod
    def _normalise_registration_number(cls, value: str) -> str:
        return _normalise_registration(value)


class VehicleUpdate(BaseModel):
    """Schema for updating vehicle details."""

    registration_number: Optional[str] = Field(None, min_length=1, max_length=20)
    vehicle_type: Optional[VehicleType] = None
    brand: Optional[str] = Field(None, max_length=60)
    model: Optional[str] = Field(None, max_length=60)
    year_manufactured: Optional[int] = None
    seating_capacity: Optional[int] = Field(None, ge=1, le=100)
    fuel_type: Optional[FuelType] = None
    status: Optional[VehicleStatus] = None
    current_mileage: Optional[int] = Field(None, ge=0)
    tax_expiry_date: Optional[date] = None
    insurance_expiry_date: Optional[date] = None
    inspection_expiry_date: Optional[date] = None
    notes: Optional[str] = None

    @field_validator("registration_number")
    @classmethod
    def _normalise_registration_number(
        cls, value: Optional[str]
    ) -> Optional[str]:
        if value is None:
            return None
        return _normalise_registration(value)

    @field_validator("brand", "model")
    @classmethod
    def _normalise_optional_text(
        cls, value: Optional[str], info: ValidationInfo
    ) -> Optional[str]:
        if value is None:
            return None
        return _normalise_basic_text(value, info.field_name.replace("_", " "))

    @field_validator("notes")
    @classmethod
    def _normalise_optional_notes(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        trimmed = value.strip()
        return trimmed or None

    @field_validator("year_manufactured")
    @classmethod
    def _check_year(cls, value: Optional[int]) -> Optional[int]:
        return _validate_year(value)


class VehicleStatusUpdate(BaseModel):
    """Schema for updating only the vehicle status."""

    status: VehicleStatus


class VehicleRead(VehicleBase):
    """Schema for returning vehicle data via the API."""

    id: int
    registration_number: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
