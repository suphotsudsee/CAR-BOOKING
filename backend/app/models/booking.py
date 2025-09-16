"""Booking request model for vehicle reservations"""

from enum import Enum
from typing import Optional
from datetime import datetime
from sqlalchemy import String, Integer, DateTime, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin
from .vehicle import VehicleType


class BookingStatus(str, Enum):
    """Booking request status enumeration"""
    DRAFT = "DRAFT"
    REQUESTED = "REQUESTED"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    ASSIGNED = "ASSIGNED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


class VehiclePreference(str, Enum):
    """Vehicle preference for booking requests"""
    ANY = "ANY"
    SEDAN = "SEDAN"
    VAN = "VAN"
    PICKUP = "PICKUP"
    BUS = "BUS"
    OTHER = "OTHER"


class BookingRequest(Base, TimestampMixin):
    """Booking request model for vehicle reservations"""
    
    __tablename__ = "booking_requests"
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    requester_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    department: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    purpose: Mapped[str] = mapped_column(String(500), nullable=False)
    passenger_count: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    
    # Trip details
    start_datetime: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    end_datetime: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    pickup_location: Mapped[str] = mapped_column(String(500), nullable=False)
    dropoff_location: Mapped[str] = mapped_column(String(500), nullable=False)
    
    # Vehicle preference
    vehicle_preference: Mapped[VehiclePreference] = mapped_column(default=VehiclePreference.ANY, nullable=False)
    special_requirements: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Status tracking
    status: Mapped[BookingStatus] = mapped_column(default=BookingStatus.DRAFT, nullable=False, index=True)
    submitted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    requester = relationship("User", back_populates="booking_requests")
    approvals = relationship("Approval", back_populates="booking_request", cascade="all, delete-orphan")
    assignment = relationship("Assignment", back_populates="booking_request", uselist=False)
    job_run = relationship("JobRun", back_populates="booking_request", uselist=False)
    
    def __repr__(self) -> str:
        return f"<BookingRequest(id={self.id}, purpose='{self.purpose[:30]}...', status='{self.status}')>"