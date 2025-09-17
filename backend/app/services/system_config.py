"""System configuration management services."""

from __future__ import annotations

from datetime import date, time
from typing import Iterable

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.system import (
    SystemConfiguration,
    SystemHoliday,
    SystemWorkingHour,
)

_DEFAULT_CONFIG_ID = 1


async def get_system_configuration(session: AsyncSession) -> SystemConfiguration:
    """Return the singleton system configuration, creating defaults when absent."""

    result = await session.execute(select(SystemConfiguration).limit(1))
    config = result.scalar_one_or_none()
    if config is None:
        config = SystemConfiguration(id=_DEFAULT_CONFIG_ID)
        session.add(config)
        await session.commit()
        await session.refresh(config)
    return config


async def update_system_configuration(
    session: AsyncSession,
    *,
    maintenance_mode: bool | None = None,
    maintenance_message: str | None = None,
    require_booking_approval: bool | None = None,
    max_pending_bookings_per_user: int | None = None,
    max_active_bookings_per_user: int | None = None,
    auto_cancel_pending_hours: int | None = None,
    working_day_start: time | None = None,
    working_day_end: time | None = None,
    working_days: Iterable[str] | None = None,
    approval_escalation_hours: int | None = None,
    booking_lead_time_hours: int | None = None,
) -> SystemConfiguration:
    """Update the global system configuration with provided values."""

    config = await get_system_configuration(session)
    update_data = {
        "maintenance_mode": maintenance_mode,
        "maintenance_message": maintenance_message,
        "require_booking_approval": require_booking_approval,
        "max_pending_bookings_per_user": max_pending_bookings_per_user,
        "max_active_bookings_per_user": max_active_bookings_per_user,
        "auto_cancel_pending_hours": auto_cancel_pending_hours,
        "working_day_start": working_day_start,
        "working_day_end": working_day_end,
        "approval_escalation_hours": approval_escalation_hours,
        "booking_lead_time_hours": booking_lead_time_hours,
    }

    for field, value in update_data.items():
        if value is not None:
            setattr(config, field, value)

    if working_days is not None:
        config.working_days = [day.lower() for day in working_days]

    await session.commit()
    await session.refresh(config)
    return config


async def list_holidays(session: AsyncSession) -> list[SystemHoliday]:
    """Return configured holidays ordered by date."""

    config = await get_system_configuration(session)
    result = await session.execute(
        select(SystemHoliday)
        .where(SystemHoliday.configuration_id == config.id)
        .order_by(SystemHoliday.date.asc())
    )
    return list(result.scalars().all())


async def add_holiday(
    session: AsyncSession,
    *,
    date: date,
    name: str,
    description: str | None = None,
) -> SystemHoliday:
    """Create a new holiday linked to the global configuration."""

    config = await get_system_configuration(session)
    holiday = SystemHoliday(
        configuration_id=config.id,
        date=date,
        name=name,
        description=description,
    )
    session.add(holiday)
    await session.commit()
    await session.refresh(holiday)
    return holiday


async def remove_holiday(session: AsyncSession, holiday_id: int) -> bool:
    """Delete a holiday by identifier."""

    result = await session.execute(
        select(SystemHoliday).where(SystemHoliday.id == holiday_id)
    )
    holiday = result.scalar_one_or_none()
    if holiday is None:
        return False

    await session.delete(holiday)
    await session.commit()
    return True


async def list_working_hours(session: AsyncSession) -> list[SystemWorkingHour]:
    """Return working hours ordered by day of week."""

    config = await get_system_configuration(session)
    result = await session.execute(
        select(SystemWorkingHour)
        .where(SystemWorkingHour.configuration_id == config.id)
        .order_by(SystemWorkingHour.day_of_week.asc())
    )
    return list(result.scalars().all())


async def upsert_working_hour(
    session: AsyncSession,
    *,
    day_of_week: str,
    start_time: time,
    end_time: time,
) -> SystemWorkingHour:
    """Create or update the working hours for a particular day."""

    config = await get_system_configuration(session)
    normalised_day = day_of_week.lower()

    result = await session.execute(
        select(SystemWorkingHour).where(
            SystemWorkingHour.configuration_id == config.id,
            func.lower(SystemWorkingHour.day_of_week) == normalised_day,
        )
    )
    working_hour = result.scalar_one_or_none()

    if working_hour is None:
        working_hour = SystemWorkingHour(
            configuration_id=config.id,
            day_of_week=normalised_day,
            start_time=start_time,
            end_time=end_time,
        )
        session.add(working_hour)
    else:
        working_hour.start_time = start_time
        working_hour.end_time = end_time

    await session.commit()
    await session.refresh(working_hour)
    return working_hour


async def remove_working_hour(session: AsyncSession, day_of_week: str) -> bool:
    """Remove configured working hours for the specified day."""

    config = await get_system_configuration(session)
    normalised_day = day_of_week.lower()
    result = await session.execute(
        select(SystemWorkingHour).where(
            SystemWorkingHour.configuration_id == config.id,
            func.lower(SystemWorkingHour.day_of_week) == normalised_day,
        )
    )
    working_hour = result.scalar_one_or_none()
    if working_hour is None:
        return False

    await session.delete(working_hour)
    await session.commit()
    return True
