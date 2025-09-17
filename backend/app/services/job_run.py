"""Service layer for managing job run execution data."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.assignment import Assignment
from app.models.booking import BookingRequest, BookingStatus
from app.models.job_run import JobRun, JobRunStatus
from app.schemas.job_run import JobRunCheckIn, JobRunCheckOut


async def get_job_run_by_booking_id(
    session: AsyncSession, booking_request_id: int
) -> Optional[JobRun]:
    """Return the job run associated with ``booking_request_id`` if present."""

    stmt = select(JobRun).where(JobRun.booking_request_id == booking_request_id)
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def _load_assignment(
    session: AsyncSession, booking_request: BookingRequest
) -> Assignment:
    assignment = booking_request.assignment
    if assignment is not None:
        return assignment

    stmt = select(Assignment).where(
        Assignment.booking_request_id == booking_request.id
    )
    result = await session.execute(stmt)
    assignment = result.scalar_one_or_none()
    if assignment is None:
        msg = "Booking must have an assignment before execution can be tracked"
        raise ValueError(msg)
    return assignment


def _ensure_job_run_instance(booking_request: BookingRequest) -> JobRun:
    job_run = booking_request.job_run
    if job_run is None:
        job_run = JobRun(booking_request_id=booking_request.id)
    return job_run


def _normalise_datetime(value: datetime) -> datetime:
    """Return *value* converted to naive UTC for comparisons."""

    if value.tzinfo is None:
        return value
    return value.astimezone(timezone.utc).replace(tzinfo=None)


async def record_job_check_in(
    session: AsyncSession,
    *,
    booking_request: BookingRequest,
    payload: JobRunCheckIn,
) -> JobRun:
    """Record check-in information for the supplied booking."""

    await _load_assignment(session, booking_request)

    if booking_request.status != BookingStatus.ASSIGNED:
        msg = "Booking must be in ASSIGNED status before check-in"
        raise ValueError(msg)

    job_run = _ensure_job_run_instance(booking_request)

    if job_run.status in {JobRunStatus.IN_PROGRESS, JobRunStatus.COMPLETED}:
        raise ValueError("Job has already been checked in")

    if job_run.checkin_datetime is not None:
        raise ValueError("Check-in details have already been recorded")

    if payload.checkin_datetime is None:
        raise ValueError("Check-in timestamp is required")

    job_run.checkin_datetime = payload.checkin_datetime
    job_run.checkin_mileage = payload.checkin_mileage
    job_run.checkin_location = payload.checkin_location
    job_run.checkin_images = payload.checkin_images
    job_run.status = JobRunStatus.IN_PROGRESS

    booking_request.job_run = job_run
    booking_request.status = BookingStatus.IN_PROGRESS

    session.add(job_run)
    await session.commit()
    await session.refresh(job_run)
    await session.refresh(booking_request)
    return job_run


async def record_job_check_out(
    session: AsyncSession,
    *,
    booking_request: BookingRequest,
    payload: JobRunCheckOut,
) -> JobRun:
    """Record check-out information for the supplied booking."""

    await _load_assignment(session, booking_request)

    if booking_request.status != BookingStatus.IN_PROGRESS:
        msg = "Booking must be in IN_PROGRESS status before check-out"
        raise ValueError(msg)

    job_run = booking_request.job_run
    if job_run is None or job_run.checkin_datetime is None:
        raise ValueError("Job must be checked in before check-out")

    if job_run.status != JobRunStatus.IN_PROGRESS:
        raise ValueError("Job is not currently in progress")

    checkout_time = _normalise_datetime(payload.checkout_datetime)
    checkin_time = _normalise_datetime(job_run.checkin_datetime)

    if checkout_time < checkin_time:
        raise ValueError("Check-out time cannot be before check-in time")

    if (
        job_run.checkin_mileage is not None
        and payload.checkout_mileage < job_run.checkin_mileage
    ):
        raise ValueError("Check-out mileage cannot be less than check-in mileage")

    job_run.checkout_datetime = payload.checkout_datetime
    job_run.checkout_mileage = payload.checkout_mileage
    job_run.checkout_location = payload.checkout_location
    job_run.checkout_images = payload.checkout_images
    job_run.fuel_cost = payload.fuel_cost
    job_run.toll_cost = payload.toll_cost
    job_run.other_expenses = payload.other_expenses
    job_run.expense_receipts = payload.expense_receipts
    job_run.incident_report = payload.incident_report
    job_run.incident_images = payload.incident_images
    job_run.status = JobRunStatus.COMPLETED

    booking_request.status = BookingStatus.COMPLETED

    await session.commit()
    await session.refresh(job_run)
    await session.refresh(booking_request)
    return job_run


__all__ = [
    "get_job_run_by_booking_id",
    "record_job_check_in",
    "record_job_check_out",
]
