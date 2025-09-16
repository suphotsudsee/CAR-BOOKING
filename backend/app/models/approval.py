"""Approval models for booking request workflow."""

from enum import Enum
from typing import Optional
from datetime import datetime
from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base


class ApprovalDecision(str, Enum):
    """Approval decision enumeration"""

    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


class Approval(Base):
    """Approval model for booking request workflow"""

    __tablename__ = "approvals"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    booking_request_id: Mapped[int] = mapped_column(
        ForeignKey("booking_requests.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    approver_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"), nullable=False, index=True
    )
    approval_level: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    decision: Mapped[ApprovalDecision] = mapped_column(nullable=False)
    reason: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    delegated_from_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("users.id"), nullable=True, index=True
    )
    decided_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    # Relationships
    booking_request = relationship("BookingRequest", back_populates="approvals")
    approver = relationship("User", back_populates="approvals", foreign_keys=[approver_id])
    delegated_from = relationship("User", foreign_keys=[delegated_from_id])

    def __repr__(self) -> str:
        return (
            "<Approval(id={0}, booking_id={1}, level={2}, decision='{3}')>".format(
                self.id, self.booking_request_id, self.approval_level, self.decision
            )
        )


class ApprovalDelegation(Base):
    """Delegation allowing an alternate approver to act on behalf of a manager."""

    __tablename__ = "approval_delegations"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    delegator_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    delegate_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    department: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    start_datetime: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    end_datetime: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    delegator = relationship("User", foreign_keys=[delegator_id])
    delegate = relationship("User", foreign_keys=[delegate_id])

    def __repr__(self) -> str:
        return (
            "<ApprovalDelegation(id={0}, delegator_id={1}, delegate_id={2})>".format(
                self.id, self.delegator_id, self.delegate_id
            )
        )