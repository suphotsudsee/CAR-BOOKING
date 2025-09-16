"""Booking request management API endpoints."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import RoleBasedAccess, get_current_user
from app.core.config import settings
from app.db import get_async_session
from app.models.booking import BookingRequest, BookingStatus, VehiclePreference
from app.models.user import User, UserRole
from app.schemas import (
    BookingRequestCreate,
    BookingRequestRead,
    BookingRequestUpdate,
    BookingStatusUpdate,
)
from app.services import (
    create_booking_request,
    delete_booking_request,
    get_booking_request_by_id,
    list_booking_requests,
    transition_booking_status,
    update_booking_request,
)

router = APIRouter()

_MANAGEMENT_ROLES = (UserRole.MANAGER, UserRole.FLEET_ADMIN)
_manage_bookings = RoleBasedAccess(_MANAGEMENT_ROLES)


def _is_management(user: User) -> bool:
    return user.role in _MANAGEMENT_ROLES


def _ensure_can_access(booking: BookingRequest, user: User) -> None:
    if booking.requester_id != user.id and not _is_management(user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to access this booking",
        )


@router.post("/", response_model=BookingRequestRead, status_code=status.HTTP_201_CREATED)
async def create_booking(
    booking_in: BookingRequestCreate,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user),
) -> BookingRequestRead:
    """Create a new booking request for the authenticated user."""

    target_requester_id = booking_in.requester_id or current_user.id
    if (
        booking_in.requester_id is not None
        and booking_in.requester_id != current_user.id
        and not _is_management(current_user)
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to create bookings for other users",
        )

    payload = booking_in.model_copy(update={"requester_id": target_requester_id})

    try:
        booking = await create_booking_request(session, payload)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    return booking


@router.get("/", response_model=list[BookingRequestRead])
async def list_bookings(
    skip: int = Query(0, ge=0),
    limit: int = Query(
        default=settings.DEFAULT_PAGE_SIZE,
        ge=1,
        le=settings.MAX_PAGE_SIZE,
    ),
    status: Optional[BookingStatus] = None,
    requester_id: Optional[int] = Query(default=None, ge=1),
    department: Optional[str] = Query(default=None, min_length=1, max_length=100),
    vehicle_preference: Optional[VehiclePreference] = None,
    start_from: Optional[datetime] = None,
    start_to: Optional[datetime] = None,
    search: Optional[str] = Query(default=None, min_length=1),
    session: AsyncSession = Depends(get_async_session),
    _: User = Depends(_manage_bookings),
) -> list[BookingRequestRead]:
    """List booking requests with optional filters. Restricted to management roles."""

    department_filter = department.strip() if department else None
    search_term = search.strip() if search else None

    return await list_booking_requests(
        session,
        skip=skip,
        limit=limit,
        status=status,
        requester_id=requester_id,
        department=department_filter,
        vehicle_preference=vehicle_preference,
        start_from=start_from,
        start_to=start_to,
        search=search_term,
    )


@router.get("/me", response_model=list[BookingRequestRead])
async def list_own_bookings(
    skip: int = Query(0, ge=0),
    limit: int = Query(
        default=settings.DEFAULT_PAGE_SIZE,
        ge=1,
        le=settings.MAX_PAGE_SIZE,
    ),
    status: Optional[BookingStatus] = None,
    start_from: Optional[datetime] = None,
    start_to: Optional[datetime] = None,
    search: Optional[str] = Query(default=None, min_length=1),
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user),
) -> list[BookingRequestRead]:
    """List the authenticated user's booking requests."""

    search_term = search.strip() if search else None

    return await list_booking_requests(
        session,
        skip=skip,
        limit=limit,
        status=status,
        requester_id=current_user.id,
        start_from=start_from,
        start_to=start_to,
        search=search_term,
    )


@router.get("/{booking_id}", response_model=BookingRequestRead)
async def get_booking_detail(
    booking_id: int,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user),
) -> BookingRequestRead:
    """Retrieve a single booking request."""

    booking = await get_booking_request_by_id(session, booking_id)
    if booking is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Booking not found")

    _ensure_can_access(booking, current_user)
    return booking


@router.patch("/{booking_id}", response_model=BookingRequestRead)
async def update_booking(
    booking_id: int,
    booking_update: BookingRequestUpdate,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user),
) -> BookingRequestRead:
    """Update details of an existing booking request."""

    booking = await get_booking_request_by_id(session, booking_id)
    if booking is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Booking not found")

    _ensure_can_access(booking, current_user)

    try:
        return await update_booking_request(
            session, booking_request=booking, booking_update=booking_update
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc


@router.delete("/{booking_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_booking(
    booking_id: int,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user),
) -> None:
    """Delete a booking request."""

    booking = await get_booking_request_by_id(session, booking_id)
    if booking is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Booking not found")

    _ensure_can_access(booking, current_user)

    try:
        await delete_booking_request(session, booking_request=booking)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc


@router.patch("/{booking_id}/status", response_model=BookingRequestRead)
async def update_booking_status(
    booking_id: int,
    status_update: BookingStatusUpdate,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user),
) -> BookingRequestRead:
    """Update the workflow status of a booking request."""

    booking = await get_booking_request_by_id(session, booking_id)
    if booking is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Booking not found")

    new_status = status_update.status

    is_management = _is_management(current_user)
    is_owner = booking.requester_id == current_user.id

    if new_status == BookingStatus.REQUESTED and not (is_owner or is_management):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the requester or management can submit a booking",
        )

    if new_status == BookingStatus.CANCELLED and not (is_owner or is_management):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the requester or management can cancel a booking",
        )

    if new_status not in {BookingStatus.REQUESTED, BookingStatus.CANCELLED} and not is_management:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only management can perform this status update",
        )

    try:
        return await transition_booking_status(
            session, booking_request=booking, new_status=new_status
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

