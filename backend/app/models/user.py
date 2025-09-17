"""User model for authentication and role management"""

from enum import Enum
from typing import Optional
from sqlalchemy import Boolean, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin


class UserRole(str, Enum):
    """User roles in the system"""
    REQUESTER = "requester"
    MANAGER = "manager" 
    FLEET_ADMIN = "fleet_admin"
    DRIVER = "driver"
    AUDITOR = "auditor"


class User(Base, TimestampMixin):
    """User model for system authentication and authorization"""
    
    __tablename__ = "users"
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    email: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    full_name: Mapped[str] = mapped_column(String(120), nullable=False)
    department: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    role: Mapped[UserRole] = mapped_column(nullable=False, index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    two_fa_enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    password_hash: Mapped[str] = mapped_column(Text, nullable=False)
    
    # Relationships
    booking_requests = relationship("BookingRequest", back_populates="requester")
    approvals = relationship(
        "Approval",
        back_populates="approver",
        foreign_keys="Approval.approver_id",
    )
    assignments_created = relationship("Assignment", back_populates="assigned_by_user")
    driver_profile = relationship("Driver", back_populates="user", uselist=False)
    reviewed_job_runs = relationship(
        "JobRun",
        back_populates="expense_reviewer",
        foreign_keys="JobRun.expense_reviewed_by_id",
    )
    notifications = relationship(
        "Notification",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    notification_preferences = relationship(
        "NotificationPreference",
        back_populates="user",
        cascade="all, delete-orphan",
        uselist=False,
    )

    def __repr__(self) -> str:
        return f"<User(id={self.id}, username='{self.username}', role='{self.role}')>"