"""Administrative system management models."""

from __future__ import annotations

from datetime import date, time
from typing import Any, Optional

from sqlalchemy import Boolean, Date, ForeignKey, Integer, JSON, String, Text, Time
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class SystemConfiguration(Base, TimestampMixin):
    """Singleton-style configuration for global system settings."""

    __tablename__ = "system_configurations"

    id: Mapped[int] = mapped_column(primary_key=True)
    maintenance_mode: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )
    maintenance_message: Mapped[Optional[str]] = mapped_column(String(255))
    require_booking_approval: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False
    )
    max_pending_bookings_per_user: Mapped[int] = mapped_column(
        Integer, default=3, nullable=False
    )
    max_active_bookings_per_user: Mapped[int] = mapped_column(
        Integer, default=2, nullable=False
    )
    auto_cancel_pending_hours: Mapped[int] = mapped_column(
        Integer, default=48, nullable=False
    )
    working_day_start: Mapped[time] = mapped_column(
        Time, default=time(8, 0), nullable=False
    )
    working_day_end: Mapped[time] = mapped_column(
        Time, default=time(18, 0), nullable=False
    )
    working_days: Mapped[list[str]] = mapped_column(
        JSON,
        default=lambda: [
            "monday",
            "tuesday",
            "wednesday",
            "thursday",
            "friday",
        ],
        nullable=False,
    )
    approval_escalation_hours: Mapped[int] = mapped_column(
        Integer, default=24, nullable=False
    )
    booking_lead_time_hours: Mapped[int] = mapped_column(
        Integer, default=4, nullable=False
    )

    holidays: Mapped[list[SystemHoliday]] = relationship(
        "SystemHoliday", back_populates="configuration", cascade="all, delete-orphan"
    )
    working_hours: Mapped[list[SystemWorkingHour]] = relationship(
        "SystemWorkingHour",
        back_populates="configuration",
        cascade="all, delete-orphan",
    )


class SystemHoliday(Base, TimestampMixin):
    """Represents an organisation-wide holiday."""

    __tablename__ = "system_holidays"

    id: Mapped[int] = mapped_column(primary_key=True)
    configuration_id: Mapped[int] = mapped_column(
        ForeignKey("system_configurations.id", ondelete="CASCADE"),
        nullable=False,
    )
    date: Mapped[date] = mapped_column(Date, nullable=False)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)

    configuration: Mapped[SystemConfiguration] = relationship(
        "SystemConfiguration", back_populates="holidays"
    )


class SystemWorkingHour(Base, TimestampMixin):
    """Configurable working hour window for a given weekday."""

    __tablename__ = "system_working_hours"

    id: Mapped[int] = mapped_column(primary_key=True)
    configuration_id: Mapped[int] = mapped_column(
        ForeignKey("system_configurations.id", ondelete="CASCADE"),
        nullable=False,
    )
    day_of_week: Mapped[str] = mapped_column(String(9), nullable=False)
    start_time: Mapped[time] = mapped_column(Time, nullable=False)
    end_time: Mapped[time] = mapped_column(Time, nullable=False)

    configuration: Mapped[SystemConfiguration] = relationship(
        "SystemConfiguration", back_populates="working_hours"
    )


class AuditLog(Base, TimestampMixin):
    """Audit trail of user initiated actions within the platform."""

    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"), index=True)
    action: Mapped[str] = mapped_column(String(120), nullable=False)
    resource: Mapped[str] = mapped_column(String(255), nullable=False)
    status_code: Mapped[int] = mapped_column(Integer, nullable=False, default=200)
    ip_address: Mapped[Optional[str]] = mapped_column(String(45))
    user_agent: Mapped[Optional[str]] = mapped_column(String(255))
    context: Mapped[dict[str, Any] | None] = mapped_column(JSON)


class SystemHealthRecord(Base, TimestampMixin):
    """Stores periodic system health information for monitoring."""

    __tablename__ = "system_health_records"

    id: Mapped[int] = mapped_column(primary_key=True)
    component: Mapped[str] = mapped_column(String(100), nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False)
    severity: Mapped[str] = mapped_column(String(20), default="info", nullable=False)
    details: Mapped[Optional[str]] = mapped_column(Text)
    extra: Mapped[dict[str, Any] | None] = mapped_column(JSON)


__all__ = [
    "SystemConfiguration",
    "SystemHoliday",
    "SystemWorkingHour",
    "AuditLog",
    "SystemHealthRecord",
]
