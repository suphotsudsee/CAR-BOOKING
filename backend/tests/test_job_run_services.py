from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from decimal import Decimal

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.booking import BookingRequest, BookingStatus
from app.models.driver import DriverStatus
from app.models.job_run import JobRunStatus
from app.models.user import User, UserRole
from app.models.vehicle import FuelType, VehicleStatus, VehicleType
from app.schemas import (
    AssignmentCreate,
    BookingRequestCreate,
    DriverCreate,
    JobRunCheckIn,
    JobRunCheckOut,
    UserCreate,
    VehicleCreate,
)
from app.services import (
    create_assignment,
    create_booking_request,
    create_driver,
    create_user,
    create_vehicle,
    get_booking_request_by_id,
    record_job_check_in,
    record_job_check_out,
    transition_booking_status,
)


def _future_window(hours_from_now: int = 1, duration_hours: int = 2) -> tuple[datetime, datetime]:
    start = datetime.now(timezone.utc) + timedelta(hours=hours_from_now)
    end = start + timedelta(hours=duration_hours)
    return start, end


async def _create_manager(session: AsyncSession) -> User:
    return await create_user(
        session,
        UserCreate(
            username="fleet_manager",
            email="fleet_manager@example.com",
            full_name="Fleet Manager",
            department="Operations",
            role=UserRole.FLEET_ADMIN,
            password="Password123",
        ),
    )


async def _create_driver_with_user(
    session: AsyncSession,
    *,
    employee_code: str,
) -> tuple[User, int]:
    driver_user = await create_user(
        session,
        UserCreate(
            username=f"driver_{employee_code.lower()}",
            email=f"driver_{employee_code.lower()}@example.com",
            full_name=f"Driver {employee_code}",
            department="Fleet",
            role=UserRole.DRIVER,
            password="Password123",
        ),
    )

    driver = await create_driver(
        session,
        DriverCreate(
            employee_code=employee_code,
            full_name=f"Driver {employee_code}",
            phone_number="+62123456789",
            license_number=f"LIC-{employee_code}",
            license_type="B",
            license_expiry_date=date.today() + timedelta(days=365),
            status=DriverStatus.ACTIVE,
            user_id=driver_user.id,
        ),
    )

    return driver_user, driver.id


async def _create_vehicle(
    session: AsyncSession,
    *,
    registration: str,
    capacity: int = 4,
) -> int:
    vehicle = await create_vehicle(
        session,
        VehicleCreate(
            registration_number=registration,
            vehicle_type=VehicleType.SEDAN,
            brand="Brand",
            model="Model",
            seating_capacity=capacity,
            fuel_type=FuelType.GASOLINE,
            status=VehicleStatus.ACTIVE,
        ),
    )
    return vehicle.id


async def _prepare_assigned_booking(session: AsyncSession) -> BookingRequest:
    manager = await _create_manager(session)
    _, driver_id = await _create_driver_with_user(session, employee_code="DRV100")
    vehicle_id = await _create_vehicle(session, registration="B 1234 XYZ")

    start, end = _future_window()
    booking = await create_booking_request(
        session,
        BookingRequestCreate(
            requester_id=manager.id,
            purpose="Client visit",
            passenger_count=3,
            start_datetime=start,
            end_datetime=end,
            pickup_location="Head Office",
            dropoff_location="Client Site",
            status=BookingStatus.REQUESTED,
        ),
    )

    booking = await transition_booking_status(
        session, booking_request=booking, new_status=BookingStatus.APPROVED
    )

    await create_assignment(
        session,
        AssignmentCreate(
            booking_request_id=booking.id,
            vehicle_id=vehicle_id,
            driver_id=driver_id,
            notes="Primary assignment",
            auto_assign=False,
        ),
        assigned_by=manager,
    )

    refreshed = await get_booking_request_by_id(session, booking.id)
    assert refreshed is not None
    return refreshed


@pytest.mark.asyncio
async def test_check_in_updates_status_and_details(
    async_session: AsyncSession,
) -> None:
    booking = await _prepare_assigned_booking(async_session)

    check_in_time = datetime.now(timezone.utc)
    job_run = await record_job_check_in(
        async_session,
        booking_request=booking,
        payload=JobRunCheckIn(
            checkin_datetime=check_in_time,
            checkin_mileage=10500,
            checkin_location=" Main Depot  ",
            checkin_images=[
                " https://cdn.example.com/checkin.jpg ",
                "",
            ],
        ),
    )

    assert job_run.status == JobRunStatus.IN_PROGRESS
    assert job_run.checkin_location == "Main Depot"
    assert job_run.checkin_images == ["https://cdn.example.com/checkin.jpg"]
    assert booking.status == BookingStatus.IN_PROGRESS

    stored = await get_booking_request_by_id(async_session, booking.id)
    assert stored is not None
    assert stored.status == BookingStatus.IN_PROGRESS


@pytest.mark.asyncio
async def test_check_out_records_expenses_and_completes(
    async_session: AsyncSession,
) -> None:
    booking = await _prepare_assigned_booking(async_session)

    check_in_time = datetime.now(timezone.utc)
    await record_job_check_in(
        async_session,
        booking_request=booking,
        payload=JobRunCheckIn(
            checkin_datetime=check_in_time,
            checkin_mileage=20500,
            checkin_location="Depot",
        ),
    )

    checkout_time = check_in_time + timedelta(hours=4)
    job_run = await record_job_check_out(
        async_session,
        booking_request=booking,
        payload=JobRunCheckOut(
            checkout_datetime=checkout_time,
            checkout_mileage=20640,
            checkout_location="Depot",
            fuel_cost=Decimal("45.50"),
            toll_cost=Decimal("8.75"),
            other_expenses=Decimal("12.00"),
            expense_receipts=["https://cdn.example.com/receipt.jpg"],
        ),
    )

    assert job_run.status == JobRunStatus.COMPLETED
    assert job_run.checkout_mileage == 20640
    assert job_run.total_distance == 140
    assert job_run.total_expenses == Decimal("66.25")

    stored = await get_booking_request_by_id(async_session, booking.id)
    assert stored is not None
    assert stored.status == BookingStatus.COMPLETED


@pytest.mark.asyncio
async def test_check_out_requires_prior_check_in(
    async_session: AsyncSession,
) -> None:
    booking = await _prepare_assigned_booking(async_session)

    checkout_time = datetime.now(timezone.utc) + timedelta(hours=3)
    with pytest.raises(ValueError):
        await record_job_check_out(
            async_session,
            booking_request=booking,
            payload=JobRunCheckOut(
                checkout_datetime=checkout_time,
                checkout_mileage=12000,
            ),
        )


@pytest.mark.asyncio
async def test_duplicate_check_in_not_allowed(
    async_session: AsyncSession,
) -> None:
    booking = await _prepare_assigned_booking(async_session)
    check_in_time = datetime.now(timezone.utc)

    await record_job_check_in(
        async_session,
        booking_request=booking,
        payload=JobRunCheckIn(
            checkin_datetime=check_in_time,
            checkin_mileage=15000,
        ),
    )

    with pytest.raises(ValueError):
        await record_job_check_in(
            async_session,
            booking_request=booking,
            payload=JobRunCheckIn(
                checkin_datetime=check_in_time + timedelta(minutes=10),
                checkin_mileage=15010,
            ),
        )
