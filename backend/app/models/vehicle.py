"""Vehicle model for fleet management"""

from enum import Enum
from typing import Optional
from datetime import date
from sqlalchemy import Date, Enum as SQLAlchemyEnum, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin


class VehicleType(str, Enum):
    """Vehicle type enumeration"""
    SEDAN = "SEDAN"
    VAN = "VAN"
    PICKUP = "PICKUP"
    BUS = "BUS"
    OTHER = "OTHER"


class VehicleStatus(str, Enum):
    """Vehicle status enumeration"""
    ACTIVE = "ACTIVE"
    MAINTENANCE = "MAINTENANCE"
    INACTIVE = "INACTIVE"


class FuelType(str, Enum):
    """Fuel type enumeration"""
    GASOLINE = "GASOLINE"
    DIESEL = "DIESEL"
    HYBRID = "HYBRID"
    ELECTRIC = "ELECTRIC"


class VehicleDocumentType(str, Enum):
    """Vehicle document categories supported by the system."""

    TAX = "tax"
    INSURANCE = "insurance"
    INSPECTION = "inspection"


class Vehicle(Base, TimestampMixin):
    """Vehicle model for fleet management"""

    __tablename__ = "vehicles"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    registration_number: Mapped[str] = mapped_column(
        String(20), unique=True, nullable=False, index=True
    )
    vehicle_type: Mapped[VehicleType] = mapped_column(
        SQLAlchemyEnum(VehicleType, name="vehicletype"), nullable=False, index=True
    )
    brand: Mapped[str] = mapped_column(String(60), nullable=False)
    model: Mapped[str] = mapped_column(String(60), nullable=False)
    year_manufactured: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    seating_capacity: Mapped[int] = mapped_column(Integer, nullable=False)
    fuel_type: Mapped[FuelType] = mapped_column(
        SQLAlchemyEnum(FuelType, name="fueltype"),
        default=FuelType.GASOLINE,
        nullable=False,
    )
    status: Mapped[VehicleStatus] = mapped_column(
        SQLAlchemyEnum(VehicleStatus, name="vehiclestatus"),
        default=VehicleStatus.ACTIVE,
        nullable=False,
        index=True,
    )
    current_mileage: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    
    # Document tracking
    tax_expiry_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True, index=True)
    insurance_expiry_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True, index=True)
    inspection_expiry_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True, index=True)
    tax_document_path: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    insurance_document_path: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    inspection_document_path: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    # Additional info
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Relationships
    assignments = relationship("Assignment", back_populates="vehicle")

    def __repr__(self) -> str:
        return (
            f"<Vehicle(id={self.id}, registration='{self.registration_number}',"
            f" type='{self.vehicle_type}')>"
        )
