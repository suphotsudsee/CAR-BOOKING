from __future__ import annotations

from datetime import date, datetime, time, timedelta, timezone

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.assignment import Assignment
from app.models.booking import BookingRequest, BookingStatus
from app.models.driver import Driver, DriverStatus
from app.models.user import UserRole
from app.models.vehicle import FuelType, VehicleType
from app.schemas import (
    DriverAvailabilitySchedule,
    DriverCreate,
    UserCreate,
    VehicleCreate,
)
from app.services import (
    create_driver,
    create_user,
    create_vehicle,
    get_driver_conflicting_assignments,
    is_driver_available,
    is_driver_available_by_schedule,
)


def _monday_schedule() -> DriverAvailabilitySchedule:
    return DriverAvailabilitySchedule(
        {"monday": {"start": time(8, 0), "end": time(17, 0), "available": True}}
    )


@pytest.mark.asyncio
async def test_schedule_allows_within_window(async_session: AsyncSession) -> None:
    driver = await create_driver(
        async_session,
        DriverCreate(
            employee_code="DRV900",
            full_name="Schedule Tester",
            phone_number="0812345670",
            license_number="LIC900",
            license_type="B",
            license_expiry_date=date.today() + timedelta(days=365),
            availability_schedule=_monday_schedule(),
        ),
    )

    start = datetime(2024, 3, 4, 9, 0, tzinfo=timezone.utc)
    end = datetime(2024, 3, 4, 11, 0, tzinfo=timezone.utc)

    assert is_driver_available_by_schedule(driver, start, end)


@pytest.mark.asyncio
async def test_schedule_blocks_outside_hours(async_session: AsyncSession) -> None:
    driver = await create_driver(
        async_session,
        DriverCreate(
            employee_code="DRV901",
            full_name="Early Bird",
            phone_number="0812345671",
            license_number="LIC901",
            license_type="B",
            license_expiry_date=date.today() + timedelta(days=365),
            availability_schedule=_monday_schedule(),
        ),
    )

    start = datetime(2024, 3, 4, 7, 0, tzinfo=timezone.utc)
    end = datetime(2024, 3, 4, 9, 30, tzinfo=timezone.utc)

    assert not is_driver_available_by_schedule(driver, start, end)


@pytest.mark.asyncio
async def test_schedule_blocks_day_off(async_session: AsyncSession) -> None:
    driver = await create_driver(
        async_session,
        DriverCreate(
            employee_code="DRV902",
            full_name="Day Off",
            phone_number="0812345672",
            license_number="LIC902",
            license_type="B",
            license_expiry_date=date.today() + timedelta(days=365),
            availability_schedule=_monday_schedule(),
        ),
    )

    start = datetime(2024, 3, 5, 10, 0, tzinfo=timezone.utc)
    end = datetime(2024, 3, 5, 12, 0, tzinfo=timezone.utc)

    assert not is_driver_available_by_schedule(driver, start, end)


async def _setup_conflict_environment(
    async_session: AsyncSession,
) -> tuple[Driver, BookingRequest]:
    driver = await create_driver(
        async_session,
        DriverCreate(
            employee_code="DRV903",
            full_name="Conflict Driver",
            phone_number="0812345673",
            license_number="LIC903",
            license_type="B",
            license_expiry_date=date.today() + timedelta(days=365),
            availability_schedule=_monday_schedule(),
        ),
    )

    admin = await create_user(
        async_session,
        UserCreate(
            username="admin_user",
            email="admin@example.com",
            full_name="Admin User",
            department="Logistics",
            role=UserRole.FLEET_ADMIN,
            password="Password123",
        ),
    )

    requester = await create_user(
        async_session,
        UserCreate(
            username="requester_user",
            email="requester@example.com",
            full_name="Requester User",
            department="Operations",
            role=UserRole.REQUESTER,
            password="Password123",
        ),
    )

    vehicle = await create_vehicle(
        async_session,
        VehicleCreate(
            registration_number="B 1234 CD",
            vehicle_type=VehicleType.SEDAN,
            brand="Toyota",
            model="Camry",
            seating_capacity=4,
            fuel_type=FuelType.GASOLINE,
        ),
    )

    start = datetime(2024, 3, 4, 9, 0, tzinfo=timezone.utc)
    end = datetime(2024, 3, 4, 11, 0, tzinfo=timezone.utc)

    booking = BookingRequest(
        requester_id=requester.id,
        department="Operations",
        purpose="Morning trip",
        passenger_count=1,
        start_datetime=start,
        end_datetime=end,
        pickup_location="Head Office",
        dropoff_location="Branch Office",
        status=BookingStatus.ASSIGNED,
    )
    async_session.add(booking)
    await async_session.commit()

    assignment = Assignment(
        booking_request_id=booking.id,
        vehicle_id=vehicle.id,
        driver_id=driver.id,
        assigned_by=admin.id,
        assigned_at=start - timedelta(hours=1),
    )
    async_session.add(assignment)
    await async_session.commit()

    await async_session.refresh(driver)
    await async_session.refresh(booking)

    return driver, booking


@pytest.mark.asyncio
async def test_driver_conflict_detection(async_session: AsyncSession) -> None:
    driver, booking = await _setup_conflict_environment(async_session)

    overlap_start = datetime(2024, 3, 4, 10, 0, tzinfo=timezone.utc)
    overlap_end = datetime(2024, 3, 4, 12, 0, tzinfo=timezone.utc)

    conflicts = await get_driver_conflicting_assignments(
        async_session,
        driver_id=driver.id,
        start=overlap_start,
        end=overlap_end,
    )

    assert len(conflicts) == 1
    assert conflicts[0].booking_request_id == booking.id

    assert not await is_driver_available(
        async_session, driver=driver, start=overlap_start, end=overlap_end
    )

    non_overlap_start = datetime(2024, 3, 4, 12, 0, tzinfo=timezone.utc)
    non_overlap_end = datetime(2024, 3, 4, 14, 0, tzinfo=timezone.utc)

    assert await is_driver_available(
        async_session, driver=driver, start=non_overlap_start, end=non_overlap_end
    )

    conflicts_ignored = await get_driver_conflicting_assignments(
        async_session,
        driver_id=driver.id,
        start=overlap_start,
        end=overlap_end,
        exclude_booking_id=booking.id,
    )

    assert conflicts_ignored == []

    assert await is_driver_available(
        async_session,
        driver=driver,
        start=overlap_start,
        end=overlap_end,
        exclude_booking_id=booking.id,
    )


@pytest.mark.asyncio
async def test_driver_availability_respects_status(async_session: AsyncSession) -> None:
    driver = await create_driver(
        async_session,
        DriverCreate(
            employee_code="DRV904",
            full_name="Leave Driver",
            phone_number="0812345674",
            license_number="LIC904",
            license_type="B",
            license_expiry_date=date.today() + timedelta(days=365),
            status=DriverStatus.ON_LEAVE,
            availability_schedule=_monday_schedule(),
        ),
    )

    start = datetime(2024, 3, 4, 9, 0, tzinfo=timezone.utc)
    end = datetime(2024, 3, 4, 11, 0, tzinfo=timezone.utc)

    assert is_driver_available_by_schedule(driver, start, end)
    assert not await is_driver_available(
        async_session, driver=driver, start=start, end=end
    )
