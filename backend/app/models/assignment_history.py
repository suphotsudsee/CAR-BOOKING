"""Historical audit entries for assignment changes."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Optional

from sqlalchemy import DateTime, Enum as SQLAlchemyEnum, ForeignKey, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin


class AssignmentChangeReason(str, Enum):
    """Enumerates the reasons an assignment history entry can exist."""

    CREATED = "CREATED"
    UPDATED = "UPDATED"


class AssignmentHistory(Base, TimestampMixin):
    """Immutable record describing the evolution of an assignment."""

    __tablename__ = "assignment_history"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    assignment_id: Mapped[int] = mapped_column(
        ForeignKey("assignments.id", ondelete="CASCADE"), nullable=False, index=True
    )

    previous_vehicle_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    previous_driver_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    previous_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    vehicle_id: Mapped[int] = mapped_column(ForeignKey("vehicles.id"), nullable=False)
    driver_id: Mapped[int] = mapped_column(ForeignKey("drivers.id"), nullable=False)
    assigned_by: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    assigned_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    change_reason: Mapped[AssignmentChangeReason] = mapped_column(
        SQLAlchemyEnum(AssignmentChangeReason, name="assignment_change_reason"),
        nullable=False,
    )

    assignment = relationship("Assignment", back_populates="history_entries")


__all__ = ["AssignmentChangeReason", "AssignmentHistory"]
