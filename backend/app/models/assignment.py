"""Assignment model for vehicle and driver allocation."""

from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from .base import Base


class Assignment(Base):
    """Assignment model for vehicle and driver allocation to booking requests."""

    __tablename__ = "assignments"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    booking_request_id: Mapped[int] = mapped_column(
        ForeignKey("booking_requests.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True,
    )
    vehicle_id: Mapped[int] = mapped_column(
        ForeignKey("vehicles.id"), nullable=False, index=True
    )
    driver_id: Mapped[int] = mapped_column(
        ForeignKey("drivers.id"), nullable=False, index=True
    )
    assigned_by: Mapped[int] = mapped_column(
        ForeignKey("users.id"), nullable=False, index=True
    )
    assigned_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships
    booking_request = relationship("BookingRequest", back_populates="assignment")
    vehicle = relationship("Vehicle", back_populates="assignments")
    driver = relationship("Driver", back_populates="assignments")
    assigned_by_user = relationship("User", back_populates="assignments_created")
    history_entries = relationship(
        "AssignmentHistory",
        back_populates="assignment",
        cascade="all, delete-orphan",
        order_by="AssignmentHistory.created_at",
    )

    def __repr__(self) -> str:
        return (
            "<Assignment(id={self.id}, booking_id={self.booking_request_id}, "
            "vehicle_id={self.vehicle_id}, driver_id={self.driver_id})>"
        )
