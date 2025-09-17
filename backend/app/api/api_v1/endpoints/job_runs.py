"""API endpoints for job execution tracking."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_storage_service
from app.core.config import settings
from app.db import get_async_session
from app.models.assignment import Assignment
from app.models.booking import BookingRequest, BookingStatus
from app.models.user import User, UserRole
from app.schemas import JobRunCheckIn, JobRunCheckOut, JobRunImageGallery, JobRunRead
from app.services import (
    build_job_run_image_gallery,
    get_assignment_by_booking_id,
    get_booking_request_by_id,
    get_job_run_by_booking_id,
    record_job_check_in,
    record_job_check_out,
)
from app.services.storage import S3StorageService

router = APIRouter()

_MANAGEMENT_ROLES = (UserRole.MANAGER, UserRole.FLEET_ADMIN)


async def _load_booking(session: AsyncSession, booking_id: int) -> BookingRequest:
    booking = await get_booking_request_by_id(session, booking_id)
    if booking is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Booking not found",
        )
    return booking


async def _get_assignment(
    session: AsyncSession,
    booking: BookingRequest,
    *,
    required: bool = False,
) -> Assignment | None:
    assignment = booking.assignment
    if assignment is None:
        assignment = await get_assignment_by_booking_id(session, booking.id)
    if assignment is None and required:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Booking must have an assignment before execution",
        )
    return assignment


async def _ensure_can_view_job(
    session: AsyncSession,
    *,
    booking: BookingRequest,
    user: User,
) -> None:
    if user.role in _MANAGEMENT_ROLES or user.role == UserRole.AUDITOR:
        return

    if booking.requester_id == user.id:
        return

    assignment = await _get_assignment(session, booking, required=False)
    if (
        assignment is not None
        and assignment.driver is not None
        and assignment.driver.user_id == user.id
    ):
        return

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Insufficient permissions to access this job run",
    )


async def _ensure_can_operate_job(
    session: AsyncSession,
    *,
    booking: BookingRequest,
    user: User,
) -> None:
    if user.role in _MANAGEMENT_ROLES:
        return

    if user.role == UserRole.DRIVER:
        assignment = await _get_assignment(session, booking, required=True)
        if assignment.driver is None or assignment.driver.user_id != user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not assigned to this booking",
            )
        return

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Insufficient permissions to update this job",
    )


@router.get("/by-booking/{booking_id}", response_model=JobRunRead)
async def get_job_run(
    booking_id: int,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user),
) -> JobRunRead:
    """Return the job run data associated with a booking."""

    booking = await _load_booking(session, booking_id)
    await _ensure_can_view_job(session, booking=booking, user=current_user)

    job_run = await get_job_run_by_booking_id(session, booking_id)
    if job_run is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job run not found",
        )
    return job_run


@router.post(
    "/by-booking/{booking_id}/check-in",
    response_model=JobRunRead,
)
async def check_in_job(
    booking_id: int,
    payload: JobRunCheckIn,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user),
) -> JobRunRead:
    """Record check-in information for a booking job."""

    booking = await _load_booking(session, booking_id)
    await _ensure_can_operate_job(session, booking=booking, user=current_user)

    if booking.status not in {BookingStatus.ASSIGNED, BookingStatus.IN_PROGRESS}:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Booking is not ready for check-in",
        )

    try:
        job_run = await record_job_check_in(
            session, booking_request=booking, payload=payload
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    return job_run


@router.post(
    "/by-booking/{booking_id}/check-out",
    response_model=JobRunRead,
)
async def check_out_job(
    booking_id: int,
    payload: JobRunCheckOut,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user),
) -> JobRunRead:
    """Record check-out information and expenses for a booking job."""

    booking = await _load_booking(session, booking_id)
    await _ensure_can_operate_job(session, booking=booking, user=current_user)

    try:
        job_run = await record_job_check_out(
            session, booking_request=booking, payload=payload
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    return job_run


@router.get(
    "/by-booking/{booking_id}/image-gallery",
    response_model=JobRunImageGallery,
)
async def get_job_run_image_gallery(
    booking_id: int,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user),
    storage: S3StorageService = Depends(get_storage_service),
) -> JobRunImageGallery:
    """Return presigned URLs for the job's before/after image sets."""

    booking = await _load_booking(session, booking_id)
    await _ensure_can_view_job(session, booking=booking, user=current_user)

    job_run = await get_job_run_by_booking_id(session, booking_id)
    if job_run is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job run not found",
        )

    return await build_job_run_image_gallery(
        job_run,
        storage,
        expires_in=settings.S3_URL_EXPIRATION,
    )


__all__ = [
    "check_in_job",
    "check_out_job",
    "get_job_run",
    "get_job_run_image_gallery",
]
