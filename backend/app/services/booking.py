"""Service layer for booking request management."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import Select, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.booking import BookingRequest, BookingStatus, VehiclePreference
from app.schemas.booking import BookingRequestCreate, BookingRequestUpdate

_EDITABLE_STATUSES: frozenset[BookingStatus] = frozenset(
    {BookingStatus.DRAFT, BookingStatus.REQUESTED}
)

_ALLOWED_TRANSITIONS: dict[BookingStatus, frozenset[BookingStatus]] = {
    BookingStatus.DRAFT: frozenset({BookingStatus.REQUESTED, BookingStatus.CANCELLED}),
    BookingStatus.REQUESTED: frozenset(
        {BookingStatus.APPROVED, BookingStatus.REJECTED, BookingStatus.CANCELLED}
    ),
    BookingStatus.APPROVED: frozenset({BookingStatus.ASSIGNED, BookingStatus.CANCELLED}),
    BookingStatus.ASSIGNED: frozenset({BookingStatus.IN_PROGRESS, BookingStatus.CANCELLED}),
    BookingStatus.IN_PROGRESS: frozenset({BookingStatus.COMPLETED, BookingStatus.CANCELLED}),
    BookingStatus.REJECTED: frozenset(),
    BookingStatus.COMPLETED: frozenset(),
    BookingStatus.CANCELLED: frozenset(),
}


def _normalise_search_term(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    trimmed = " ".join(value.split())
    return trimmed or None


def _validate_window(start: datetime, end: datetime) -> None:
    if start >= end:
        msg = "End datetime must be after the start datetime"
        raise ValueError(msg)

    if (start.tzinfo is None) != (end.tzinfo is None):
        msg = "Start and end datetimes must both be naive or both timezone-aware"
        raise ValueError(msg)


async def get_booking_request_by_id(
    session: AsyncSession, booking_request_id: int
) -> Optional[BookingRequest]:
    """Return the booking request with the supplied identifier, if present."""

    stmt: Select[tuple[BookingRequest]] = select(BookingRequest).where(
        BookingRequest.id == booking_request_id
    )
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def list_booking_requests(
    session: AsyncSession,
    *,
    skip: int = 0,
    limit: Optional[int] = None,
    status: Optional[BookingStatus] = None,
    requester_id: Optional[int] = None,
    department: Optional[str] = None,
    vehicle_preference: Optional[VehiclePreference] = None,
    start_from: Optional[datetime] = None,
    start_to: Optional[datetime] = None,
    search: Optional[str] = None,
) -> list[BookingRequest]:
    """Return booking requests filtered by the supplied parameters."""

    stmt: Select[tuple[BookingRequest]] = select(BookingRequest).order_by(
        BookingRequest.start_datetime, BookingRequest.id
    )

    if status is not None:
        stmt = stmt.where(BookingRequest.status == status)

    if requester_id is not None:
        stmt = stmt.where(BookingRequest.requester_id == requester_id)

    if department:
        stmt = stmt.where(func.lower(BookingRequest.department) == department.lower())

    if vehicle_preference is not None:
        stmt = stmt.where(BookingRequest.vehicle_preference == vehicle_preference)

    if start_from is not None:
        stmt = stmt.where(BookingRequest.start_datetime >= start_from)

    if start_to is not None:
        stmt = stmt.where(BookingRequest.start_datetime <= start_to)

    search_term = _normalise_search_term(search)
    if search_term:
        pattern = f"%{search_term.lower()}%"
        stmt = stmt.where(
            or_(
                func.lower(BookingRequest.purpose).like(pattern),
                func.lower(BookingRequest.pickup_location).like(pattern),
                func.lower(BookingRequest.dropoff_location).like(pattern),
            )
        )

    if skip:
        stmt = stmt.offset(skip)

    if limit is not None:
        stmt = stmt.limit(limit)

    result = await session.execute(stmt)
    return list(result.scalars().all())


async def create_booking_request(
    session: AsyncSession, booking_in: BookingRequestCreate
) -> BookingRequest:
    """Create a new booking request after validating business rules."""

    data = booking_in.model_dump()
    requester_id = data.pop("requester_id")
    if requester_id is None:
        msg = "requester_id must be provided"
        raise ValueError(msg)

    start = data["start_datetime"]
    end = data["end_datetime"]
    _validate_window(start, end)

    status = data.pop("status", BookingStatus.DRAFT)
    booking = BookingRequest(requester_id=requester_id, status=status, **data)

    if status == BookingStatus.REQUESTED:
        booking.submitted_at = datetime.now(timezone.utc)

    session.add(booking)
    await session.commit()
    await session.refresh(booking)
    return booking


async def update_booking_request(
    session: AsyncSession,
    *,
    booking_request: BookingRequest,
    booking_update: BookingRequestUpdate,
) -> BookingRequest:
    """Update mutable fields on an existing booking request."""

    if booking_request.status not in _EDITABLE_STATUSES:
        msg = "Only draft or requested bookings can be modified"
        raise ValueError(msg)

    data = booking_update.model_dump(exclude_unset=True)

    if "start_datetime" in data or "end_datetime" in data:
        new_start = data.get("start_datetime", booking_request.start_datetime)
        new_end = data.get("end_datetime", booking_request.end_datetime)
        _validate_window(new_start, new_end)
        booking_request.start_datetime = new_start
        booking_request.end_datetime = new_end
        data.pop("start_datetime", None)
        data.pop("end_datetime", None)

    for field, value in data.items():
        setattr(booking_request, field, value)

    await session.commit()
    await session.refresh(booking_request)
    return booking_request


async def delete_booking_request(
    session: AsyncSession, *, booking_request: BookingRequest
) -> None:
    """Delete the provided booking request if it is still editable."""

    if booking_request.status not in _EDITABLE_STATUSES:
        msg = "Only draft or requested bookings can be deleted"
        raise ValueError(msg)

    await session.delete(booking_request)
    await session.commit()


async def transition_booking_status(
    session: AsyncSession,
    *,
    booking_request: BookingRequest,
    new_status: BookingStatus,
) -> BookingRequest:
    """Transition the booking request to *new_status* following workflow rules."""

    current_status = booking_request.status
    if new_status == current_status:
        return booking_request

    allowed = _ALLOWED_TRANSITIONS.get(current_status, frozenset())
    if new_status not in allowed:
        msg = (
            f"Cannot transition booking from {current_status} to {new_status}"
        )
        raise ValueError(msg)

    booking_request.status = new_status

    if new_status == BookingStatus.REQUESTED and booking_request.submitted_at is None:
        booking_request.submitted_at = datetime.now(timezone.utc)

    await session.commit()
    await session.refresh(booking_request)
    return booking_request


__all__ = [
    "create_booking_request",
    "delete_booking_request",
    "get_booking_request_by_id",
    "list_booking_requests",
    "transition_booking_status",
    "update_booking_request",
]

