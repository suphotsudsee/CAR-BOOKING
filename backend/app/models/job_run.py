"""Job run model for tracking actual trip execution"""

from enum import Enum
from typing import Optional
from datetime import datetime
from decimal import Decimal
from sqlalchemy import String, Integer, DateTime, Text, ForeignKey, JSON, DECIMAL
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin


class JobRunStatus(str, Enum):
    """Job run status enumeration"""
    SCHEDULED = "SCHEDULED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


class ExpenseStatus(str, Enum):
    """Workflow states for recorded expenses."""

    NOT_SUBMITTED = "NOT_SUBMITTED"
    PENDING_REVIEW = "PENDING_REVIEW"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


class JobRun(Base, TimestampMixin):
    """Job run model for tracking actual trip execution and expenses"""

    __tablename__ = "job_runs"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    booking_request_id: Mapped[int] = mapped_column(ForeignKey("booking_requests.id", ondelete="CASCADE"), unique=True, nullable=False, index=True)
    
    # Check-in data
    checkin_datetime: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    checkin_mileage: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    checkin_images: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)  # List of image URLs
    checkin_location: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    
    # Check-out data
    checkout_datetime: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    checkout_mileage: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    checkout_images: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)  # List of image URLs
    checkout_location: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    
    # Expenses
    fuel_cost: Mapped[Decimal] = mapped_column(DECIMAL(10, 2), default=0.00, nullable=False)
    toll_cost: Mapped[Decimal] = mapped_column(DECIMAL(10, 2), default=0.00, nullable=False)
    other_expenses: Mapped[Decimal] = mapped_column(DECIMAL(10, 2), default=0.00, nullable=False)
    expense_receipts: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)  # List of receipt image URLs
    expense_status: Mapped[ExpenseStatus] = mapped_column(
        default=ExpenseStatus.NOT_SUBMITTED,
        nullable=False,
        index=True,
    )
    expense_reviewed_by_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    expense_reviewed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    expense_review_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Incident reporting
    incident_report: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    incident_images: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)  # List of incident image URLs

    # Status
    status: Mapped[JobRunStatus] = mapped_column(default=JobRunStatus.SCHEDULED, nullable=False, index=True)

    # Relationships
    booking_request = relationship("BookingRequest", back_populates="job_run")
    expense_reviewer = relationship(
        "User",
        back_populates="reviewed_job_runs",
        foreign_keys=[expense_reviewed_by_id],
    )
    
    @property
    def total_distance(self) -> Optional[int]:
        """Calculate total distance traveled"""
        if self.checkin_mileage is not None and self.checkout_mileage is not None:
            return self.checkout_mileage - self.checkin_mileage
        return None
    
    @property
    def total_expenses(self) -> Decimal:
        """Calculate total expenses"""
        return self.fuel_cost + self.toll_cost + self.other_expenses

    def __repr__(self) -> str:
        return f"<JobRun(id={self.id}, booking_id={self.booking_request_id}, status='{self.status}')>"