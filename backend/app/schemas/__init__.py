"""Pydantic schemas exposed by the application."""

from .auth import (
    LoginRequest,
    RefreshTokenRequest,
    RefreshTokenResponse,
    TokenPayload,
    TokenResponse,
)
from .user import (
    UserCreate,
    UserPasswordChange,
    UserProfileUpdate,
    UserRead,
    UserRoleUpdate,
    UserUpdate,
)
from .driver import (
    DriverAvailabilitySchedule,
    DriverAvailabilityUpdate,
    DriverCreate,
    DriverLicenseExpiryNotification,
    DriverRead,
    DriverStatusUpdate,
    DriverUpdate,
)
from .vehicle import (
    VehicleCreate,
    VehicleDocumentExpiryNotification,
    VehicleDocumentUploadResponse,
    VehicleRead,
    VehicleStatusUpdate,
    VehicleUpdate,
)
from .booking import (
    BookingRequestCreate,
    BookingRequestRead,
    BookingRequestUpdate,
    BookingStatusUpdate,
)
from .approval import (
    ApprovalActionRequest,
    ApprovalNotificationRead,
    ApprovalRead,
    BookingApprovalResponse,
    PendingApprovalNotificationRead,
)

__all__ = [
    "LoginRequest",
    "RefreshTokenRequest",
    "RefreshTokenResponse",
    "TokenPayload",
    "TokenResponse",
    "UserCreate",
    "UserPasswordChange",
    "UserProfileUpdate",
    "UserRead",
    "UserRoleUpdate",
    "UserUpdate",
    "DriverAvailabilityUpdate",
    "DriverAvailabilitySchedule",
    "DriverCreate",
    "DriverLicenseExpiryNotification",
    "DriverRead",
    "DriverStatusUpdate",
    "DriverUpdate",
    "VehicleCreate",
    "VehicleDocumentExpiryNotification",
    "VehicleDocumentUploadResponse",
    "VehicleRead",
    "VehicleStatusUpdate",
    "VehicleUpdate",
    "BookingRequestCreate",
    "BookingRequestRead",
    "BookingRequestUpdate",
    "BookingStatusUpdate",
    "ApprovalActionRequest",
    "ApprovalNotificationRead",
    "ApprovalRead",
    "BookingApprovalResponse",
    "PendingApprovalNotificationRead",
]
