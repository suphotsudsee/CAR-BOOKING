"""Service layer for driver management."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, time, timedelta, tzinfo
from typing import Any, Iterable, Optional

from sqlalchemy import Select, func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.assignment import Assignment
from app.models.booking import BookingRequest, BookingStatus
from app.models.driver import Driver, DriverStatus
from app.models.user import User
from app.schemas.driver import (
    DriverAvailabilitySchedule,
    DriverAvailabilityUpdate,
    DriverCreate,
    DriverStatusUpdate,
    DriverUpdate,
)


@dataclass(slots=True)
class DriverLicenseReminder:
    """Lightweight representation of an upcoming driver license expiry."""

    driver_id: int
    employee_code: str
    full_name: str
    license_number: str
    license_expiry_date: date
    days_until_expiry: int


async def get_driver_by_id(session: AsyncSession, driver_id: int) -> Optional[Driver]:
    """Return the driver associated with *driver_id*, if present."""

    result = await session.execute(select(Driver).where(Driver.id == driver_id))
    return result.scalar_one_or_none()


async def get_driver_by_employee_code(
    session: AsyncSession, employee_code: str
) -> Optional[Driver]:
    """Return the driver associated with the supplied employee code, if any."""

    code = employee_code.strip().upper()
    result = await session.execute(
        select(Driver).where(func.upper(Driver.employee_code) == code)
    )
    return result.scalar_one_or_none()


async def get_driver_by_license_number(
    session: AsyncSession, license_number: str
) -> Optional[Driver]:
    """Return the driver matching *license_number*, if present."""

    normalised = " ".join(license_number.strip().upper().split())
    result = await session.execute(
        select(Driver).where(func.upper(Driver.license_number) == normalised)
    )
    return result.scalar_one_or_none()


async def get_driver_by_user_id(
    session: AsyncSession, user_id: int
) -> Optional[Driver]:
    """Return the driver linked to *user_id*, if any."""

    result = await session.execute(select(Driver).where(Driver.user_id == user_id))
    return result.scalar_one_or_none()


def _prepare_schedule(
    schedule: Optional[DriverAvailabilitySchedule],
) -> Optional[dict[str, Any]]:
    if schedule is None:
        return None
    data = schedule.as_dict()
    return data or {}


_WEEKDAY_NAMES = {
    "monday",
    "tuesday",
    "wednesday",
    "thursday",
    "friday",
    "saturday",
    "sunday",
}

_NON_BLOCKING_BOOKING_STATUSES = {
    BookingStatus.CANCELLED,
    BookingStatus.COMPLETED,
    BookingStatus.REJECTED,
}


def _ensure_booking_window(start: datetime, end: datetime) -> None:
    """Validate the temporal window used for availability checks."""

    if start >= end:
        msg = "Start datetime must be before end datetime"
        raise ValueError(msg)

    if (start.tzinfo is None) != (end.tzinfo is None):
        msg = "Start and end datetimes must both be naive or timezone-aware"
        raise ValueError(msg)


def _normalise_schedule_data(schedule: Optional[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    """Return a lower-cased copy of the stored availability schedule."""

    if schedule is None:
        return {}

    if not isinstance(schedule, dict):
        msg = "Availability schedule must be a mapping"
        raise TypeError(msg)

    normalised: dict[str, dict[str, Any]] = {}
    for raw_day, raw_details in schedule.items():
        if not isinstance(raw_day, str):
            msg = "Weekday keys must be strings"
            raise TypeError(msg)

        day = raw_day.strip().lower()
        if day not in _WEEKDAY_NAMES:
            msg = f"Unknown weekday '{raw_day}' in availability schedule"
            raise ValueError(msg)

        details: dict[str, Any]
        if raw_details is None:
            details = {}
        elif isinstance(raw_details, dict):
            details = raw_details
        else:
            msg = "Availability entry must be a mapping"
            raise TypeError(msg)

        normalised[day] = {
            "available": bool(details.get("available", False)),
            "start": details.get("start"),
            "end": details.get("end"),
        }

    return normalised


def _coerce_time(value: Any) -> time:
    """Return *value* as a :class:`time` instance."""

    if isinstance(value, time):
        return value

    if isinstance(value, str):
        try:
            return time.fromisoformat(value)
        except ValueError as exc:
            msg = f"Invalid time value '{value}' in availability schedule"
            raise ValueError(msg) from exc

    msg = "Availability window times must be ISO strings or time objects"
    raise TypeError(msg)


def _combine(date_value: date, time_value: time, tz: tzinfo | None) -> datetime:
    """Create a datetime using *date_value*, *time_value*, and optional timezone."""

    combined = datetime.combine(date_value, time_value)
    if tz is not None:
        combined = combined.replace(tzinfo=tz)
    return combined


def _iter_booking_days(start: datetime, end: datetime) -> Iterable[date]:
    """Yield each calendar date touched by the booking window."""

    current = start.date()
    yield current

    last = end.date()
    while current < last:
        current += timedelta(days=1)
        yield current


def is_schedule_available_for_window(
    schedule: Optional[dict[str, Any]],
    start: datetime,
    end: datetime,
) -> bool:
    """Return ``True`` if *schedule* allows the booking window."""

    _ensure_booking_window(start, end)

    if schedule is None:
        return True

    normalised = _normalise_schedule_data(schedule)
    if not normalised:
        return False

    tz = start.tzinfo

    for day in _iter_booking_days(start, end):
        day_start = _combine(day, time.min, tz)
        day_end = _combine(day, time.max, tz)

        window_start = max(start, day_start)
        window_end = min(end, day_end)

        if window_start >= window_end:
            continue

        weekday = day.strftime("%A").lower()
        details = normalised.get(weekday)
        if not details or not details.get("available", False):
            return False

        start_raw = details.get("start")
        end_raw = details.get("end")
        if start_raw is None or end_raw is None:
            return False

        slot_start = _combine(day, _coerce_time(start_raw), tz)
        slot_end = _combine(day, _coerce_time(end_raw), tz)

        if not (slot_start <= window_start and slot_end >= window_end):
            return False

    return True


def is_driver_available_by_schedule(
    driver: Driver, start: datetime, end: datetime
) -> bool:
    """Check whether *driver*'s stored schedule allows the time window."""

    return is_schedule_available_for_window(driver.availability_schedule, start, end)


async def get_driver_conflicting_assignments(
    session: AsyncSession,
    *,
    driver_id: int,
    start: datetime,
    end: datetime,
    exclude_booking_id: Optional[int] = None,
) -> list[Assignment]:
    """Return assignments that clash with the supplied booking window."""

    _ensure_booking_window(start, end)

    stmt = (
        select(Assignment)
        .options(selectinload(Assignment.booking_request))
        .join(BookingRequest)
        .where(Assignment.driver_id == driver_id)
        .where(BookingRequest.start_datetime < end)
        .where(BookingRequest.end_datetime > start)
        .where(BookingRequest.status.notin_(_NON_BLOCKING_BOOKING_STATUSES))
        .order_by(BookingRequest.start_datetime, Assignment.id)
    )

    if exclude_booking_id is not None:
        stmt = stmt.where(Assignment.booking_request_id != exclude_booking_id)

    result = await session.execute(stmt)
    return list(result.scalars().all())


async def is_driver_available(
    session: AsyncSession,
    *,
    driver: Driver,
    start: datetime,
    end: datetime,
    exclude_booking_id: Optional[int] = None,
) -> bool:
    """Return ``True`` when the driver can be allocated to the booking window."""

    if driver.status != DriverStatus.ACTIVE:
        return False

    if not is_driver_available_by_schedule(driver, start, end):
        return False

    conflicts = await get_driver_conflicting_assignments(
        session,
        driver_id=driver.id,
        start=start,
        end=end,
        exclude_booking_id=exclude_booking_id,
    )
    return not conflicts


async def ensure_driver_available(
    session: AsyncSession,
    *,
    driver: Driver,
    start: datetime,
    end: datetime,
    exclude_booking_id: Optional[int] = None,
) -> None:
    """Validate that *driver* can be allocated to the requested window."""

    available = await is_driver_available(
        session,
        driver=driver,
        start=start,
        end=end,
        exclude_booking_id=exclude_booking_id,
    )

    if not available:
        msg = "Driver is not available for the requested time window"
        raise ValueError(msg)


async def create_driver(session: AsyncSession, driver_in: DriverCreate) -> Driver:
    """Persist a new driver record after validating constraints."""

    if await get_driver_by_employee_code(session, driver_in.employee_code) is not None:
        raise ValueError("Driver with this employee code already exists")

    if await get_driver_by_license_number(session, driver_in.license_number) is not None:
        raise ValueError("Driver with this license number already exists")

    if driver_in.user_id is not None:
        user_exists = await session.execute(
            select(User.id).where(User.id == driver_in.user_id)
        )
        if user_exists.scalar_one_or_none() is None:
            raise ValueError("Associated user not found")

        linked = await get_driver_by_user_id(session, driver_in.user_id)
        if linked is not None:
            raise ValueError("User already linked to another driver profile")

    data = driver_in.model_dump(exclude={"availability_schedule"})
    data["availability_schedule"] = _prepare_schedule(driver_in.availability_schedule)

    driver = Driver(**data)
    session.add(driver)

    try:
        await session.commit()
    except IntegrityError as exc:
        await session.rollback()
        raise ValueError("Driver with this employee code or license already exists") from exc

    await session.refresh(driver)
    return driver


async def list_drivers(
    session: AsyncSession,
    *,
    skip: int = 0,
    limit: Optional[int] = None,
    status: Optional[DriverStatus] = None,
    search: Optional[str] = None,
) -> list[Driver]:
    """Return a collection of drivers filtered by the supplied parameters."""

    stmt: Select[tuple[Driver]] = select(Driver).order_by(Driver.id)

    if status is not None:
        stmt = stmt.where(Driver.status == status)

    if search:
        pattern = f"%{search.lower()}%"
        stmt = stmt.where(
            or_(
                func.lower(Driver.employee_code).like(pattern),
                func.lower(Driver.full_name).like(pattern),
                func.lower(Driver.license_number).like(pattern),
            )
        )

    if skip:
        stmt = stmt.offset(skip)

    if limit is not None:
        stmt = stmt.limit(limit)

    result = await session.execute(stmt)
    return list(result.scalars().all())


async def update_driver(
    session: AsyncSession, *, driver: Driver, driver_update: DriverUpdate
) -> Driver:
    """Update *driver* with the supplied profile information."""

    data = driver_update.model_dump(exclude_unset=True, exclude={"availability_schedule"})

    if "employee_code" in data:
        existing = await get_driver_by_employee_code(session, data["employee_code"])
        if existing is not None and existing.id != driver.id:
            raise ValueError("Driver with this employee code already exists")

    if "license_number" in data:
        existing = await get_driver_by_license_number(session, data["license_number"])
        if existing is not None and existing.id != driver.id:
            raise ValueError("Driver with this license number already exists")

    if "user_id" in data:
        user_id = data["user_id"]
        if user_id is not None:
            user_exists = await session.execute(select(User.id).where(User.id == user_id))
            if user_exists.scalar_one_or_none() is None:
                raise ValueError("Associated user not found")

            linked = await get_driver_by_user_id(session, user_id)
            if linked is not None and linked.id != driver.id:
                raise ValueError("User already linked to another driver profile")

    if "availability_schedule" in driver_update.model_fields_set:
        schedule = driver_update.availability_schedule
        data["availability_schedule"] = _prepare_schedule(schedule)

    for field, value in data.items():
        setattr(driver, field, value)

    try:
        await session.commit()
    except IntegrityError as exc:
        await session.rollback()
        raise ValueError("Driver with this employee code or license already exists") from exc

    await session.refresh(driver)
    return driver


async def update_driver_status(
    session: AsyncSession, *, driver: Driver, status_update: DriverStatusUpdate
) -> Driver:
    """Update only the status field for *driver*."""

    driver.status = status_update.status
    await session.commit()
    await session.refresh(driver)
    return driver


async def update_driver_availability(
    session: AsyncSession,
    *,
    driver: Driver,
    availability_update: DriverAvailabilityUpdate,
) -> Driver:
    """Replace the driver's availability schedule."""

    driver.availability_schedule = _prepare_schedule(
        availability_update.availability_schedule
    )
    await session.commit()
    await session.refresh(driver)
    return driver


async def delete_driver(session: AsyncSession, *, driver: Driver) -> None:
    """Remove *driver* from the database."""

    await session.delete(driver)
    await session.commit()


async def get_expiring_driver_licenses(
    session: AsyncSession, *, within_days: int = 30
) -> list[DriverLicenseReminder]:
    """Return drivers whose licenses expire within the provided timeframe."""

    if within_days < 0:
        msg = "within_days must be non-negative"
        raise ValueError(msg)

    today = date.today()
    threshold = today + timedelta(days=within_days)

    stmt = select(Driver).where(Driver.license_expiry_date <= threshold)
    stmt = stmt.order_by(Driver.license_expiry_date, Driver.id)

    result = await session.execute(stmt)
    drivers = result.scalars().all()

    reminders: list[DriverLicenseReminder] = []
    for record in drivers:
        days_until_expiry = (record.license_expiry_date - today).days
        reminders.append(
            DriverLicenseReminder(
                driver_id=record.id,
                employee_code=record.employee_code,
                full_name=record.full_name,
                license_number=record.license_number,
                license_expiry_date=record.license_expiry_date,
                days_until_expiry=days_until_expiry,
            )
        )

    return reminders
