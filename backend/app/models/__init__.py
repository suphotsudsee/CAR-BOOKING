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
from .approval import Approval, ApprovalDecision
from .assignment import Assignment
from .job_run import JobRun, JobRunStatus

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
    "Approval",
    "ApprovalDecision",
    "Assignment",
    "JobRun",
    "JobRunStatus",
]