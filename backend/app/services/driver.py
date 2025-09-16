"""Service layer for driver management."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from typing import Any, Optional

from sqlalchemy import Select, func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

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
