"""Database models package"""

from .base import Base, TimestampMixin
from .user import User, UserRole
from .vehicle import (
    Vehicle,
    VehicleType,
    VehicleStatus,
    FuelType,
    VehicleDocumentType,
)
from .driver import Driver, DriverStatus
from .booking import BookingRequest, BookingStatus, VehiclePreference
from .approval import Approval, ApprovalDecision, ApprovalDelegation
from .assignment import Assignment
from .assignment_history import AssignmentChangeReason, AssignmentHistory
from .job_run import JobRun, JobRunStatus, ExpenseStatus
from .notification import Notification, NotificationChannel, NotificationPreference
from .calendar_event import (
    ResourceCalendarEvent,
    CalendarEventType,
    CalendarResourceType,
)
from .notification import EmailDeliveryStatus, EmailNotification
from .system import (
    AuditLog,
    SystemConfiguration,
    SystemHealthRecord,
    SystemHoliday,
    SystemWorkingHour,
)

__all__ = [
    "Base",
    "TimestampMixin",
    "User",
    "UserRole",
    "Vehicle",
    "VehicleType",
    "VehicleStatus",
    "FuelType",
    "VehicleDocumentType",
    "Driver",
    "DriverStatus",
    "BookingRequest",
    "BookingStatus",
    "VehiclePreference",
    "ResourceCalendarEvent",
    "CalendarResourceType",
    "CalendarEventType",
    "Approval",
    "ApprovalDecision",
    "ApprovalDelegation",
    "Assignment",
    "AssignmentChangeReason",
    "AssignmentHistory",
    "JobRun",
    "JobRunStatus",
    "ExpenseStatus",
    "Notification",
    "NotificationChannel",
    "NotificationPreference",
    "AuditLog",
    "SystemConfiguration",
    "SystemHealthRecord",
    "SystemHoliday",
    "SystemWorkingHour",
]
