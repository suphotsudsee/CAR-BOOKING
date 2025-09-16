"""Driver model for driver management"""

from enum import Enum
from typing import Optional
from datetime import date
from sqlalchemy import String, Integer, Date, Text, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin


class DriverStatus(str, Enum):
    """Driver status enumeration"""
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    ON_LEAVE = "ON_LEAVE"


class Driver(Base, TimestampMixin):
    """Driver model for managing company drivers"""
    
    __tablename__ = "drivers"
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    employee_code: Mapped[str] = mapped_column(String(30), unique=True, nullable=False, index=True)
    user_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    full_name: Mapped[str] = mapped_column(String(120), nullable=False)
    phone_number: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    license_number: Mapped[str] = mapped_column(String(60), nullable=False, index=True)
    license_type: Mapped[str] = mapped_column(String(20), default="B", nullable=False)
    license_expiry_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    status: Mapped[DriverStatus] = mapped_column(default=DriverStatus.ACTIVE, nullable=False, index=True)
    
    # Availability settings stored as JSON
    # Format: {"monday": {"start": "08:00", "end": "17:00", "available": true}, ...}
    availability_schedule: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="driver_profile")
    assignments = relationship("Assignment", back_populates="driver")
    
    def __repr__(self) -> str:
        return f"<Driver(id={self.id}, employee_code='{self.employee_code}', name='{self.full_name}')>"