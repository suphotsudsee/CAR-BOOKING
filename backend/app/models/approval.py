"""Approval model for booking request workflow"""

from enum import Enum
from typing import Optional
from datetime import datetime
from sqlalchemy import String, Integer, DateTime, ForeignKey
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
    booking_request_id: Mapped[int] = mapped_column(ForeignKey("booking_requests.id", ondelete="CASCADE"), nullable=False, index=True)
    approver_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    approval_level: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    decision: Mapped[ApprovalDecision] = mapped_column(nullable=False)
    reason: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    decided_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default="CURRENT_TIMESTAMP")
    
    # Relationships
    booking_request = relationship("BookingRequest", back_populates="approvals")
    approver = relationship("User", back_populates="approvals")
    
    def __repr__(self) -> str:
        return f"<Approval(id={self.id}, booking_id={self.booking_request_id}, decision='{self.decision}')>"