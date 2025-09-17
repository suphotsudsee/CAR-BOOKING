from __future__ import annotations

from datetime import datetime, timedelta, timezone
from time import perf_counter

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.booking import BookingStatus, VehiclePreference
from app.models.driver import DriverStatus
from app.models.user import UserRole
from app.models.vehicle import FuelType, VehicleStatus, VehicleType
from app.schemas import (
    AssignmentCreate,
    BookingRequestCreate,
    DriverCreate,
    UserCreate,
    VehicleCreate,
)
from app.services import (
    create_assignment,
    create_booking_request,
    create_driver,
    create_user,
    create_vehicle,
    suggest_assignment_options,
    transition_booking_status,
)


def _window_for_index(index: int) -> tuple[datetime, datetime]:
    start = datetime.now(timezone.utc) + timedelta(hours=1 + index * 3)
    end = start + timedelta(hours=2)
    return start, end


async def _bootstrap_manager(session: AsyncSession):
    return await create_user(
        session,
        UserCreate(
            username=f"perf_manager",
            email="perf_manager@example.com",
            full_name="Performance Manager",
            department="Operations",
            role=UserRole.FLEET_ADMIN,
            password="Password123",
        ),
    )


async def _bootstrap_resources(session: AsyncSession, count: int) -> None:
    expiry_date = datetime.now(timezone.utc).date() + timedelta(days=365)
    vehicle_types = tuple(VehicleType)
    for idx in range(count):
        await create_vehicle(
            session,
            VehicleCreate(
                registration_number=f"PERF-{idx:04d}",
                vehicle_type=vehicle_types[idx % len(vehicle_types)],
                brand="Brand",
                model="Model",
                seating_capacity=4 + (idx % 4),
                fuel_type=FuelType.GASOLINE,
                status=VehicleStatus.ACTIVE,
            ),
        )
        await create_driver(
            session,
            DriverCreate(
                employee_code=f"PERFDRV{idx:03d}",
                full_name=f"Performance Driver {idx}",
                phone_number="+6200000000",
                license_number=f"PERF-LIC-{idx:03d}",
                license_type="B",
                license_expiry_date=expiry_date,
                status=DriverStatus.ACTIVE,
            ),
        )


@pytest.mark.asyncio
async def test_suggest_assignment_options_scales(async_session: AsyncSession) -> None:
    manager = await _bootstrap_manager(async_session)
    await _bootstrap_resources(async_session, count=40)

    start, end = _window_for_index(0)
    booking = await create_booking_request(
        async_session,
        BookingRequestCreate(
            requester_id=manager.id,
            purpose="Site visit",
            passenger_count=4,
            start_datetime=start,
            end_datetime=end,
            pickup_location="HQ",
            dropoff_location="Branch",
            vehicle_preference=VehiclePreference.ANY,
            status=BookingStatus.REQUESTED,
        ),
    )
    booking = await transition_booking_status(
        async_session, booking_request=booking, new_status=BookingStatus.APPROVED
    )

    started = perf_counter()
    suggestions = await suggest_assignment_options(
        async_session, booking_request=booking, limit=10
    )
    duration = perf_counter() - started

    assert suggestions
    assert duration < 1.0


@pytest.mark.asyncio
async def test_bulk_auto_assign_performance(async_session: AsyncSession) -> None:
    manager = await _bootstrap_manager(async_session)
    await _bootstrap_resources(async_session, count=50)

    started = perf_counter()
    for idx in range(15):
        start, end = _window_for_index(idx)
        booking = await create_booking_request(
            async_session,
            BookingRequestCreate(
                requester_id=manager.id,
                purpose=f"Performance booking {idx}",
                passenger_count=4 + (idx % 3),
                start_datetime=start,
                end_datetime=end,
                pickup_location="HQ",
                dropoff_location="Client",
                vehicle_preference=VehiclePreference.ANY,
                status=BookingStatus.REQUESTED,
            ),
        )
        booking = await transition_booking_status(
            async_session, booking_request=booking, new_status=BookingStatus.APPROVED
        )
        assignment = await create_assignment(
            async_session,
            AssignmentCreate(booking_request_id=booking.id),
            assigned_by=manager,
        )
        assert assignment is not None

    duration = perf_counter() - started
    assert duration < 2.5
