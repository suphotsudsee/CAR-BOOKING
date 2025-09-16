from __future__ import annotations

from datetime import date, datetime, timedelta, timezone

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.assignment import Assignment
from app.models.booking import BookingRequest, BookingStatus
from app.models.driver import Driver, DriverStatus
from app.models.user import UserRole
from app.models.vehicle import FuelType, Vehicle, VehicleType
from app.schemas import DriverCreate, UserCreate, VehicleCreate
from app.services import (
    create_driver,
    create_user,
    create_vehicle,
    ensure_driver_available,
    get_conflicting_booking_requests,
    get_vehicle_conflicting_assignments,
    is_vehicle_available,
    suggest_alternative_bookings,
)


def _create_user_payload(username: str, role: UserRole) -> UserCreate:
    return UserCreate(
        username=username,
        email=f"{username}@example.com",
        full_name=f"{username.title()} User",
        department="Operations",
        role=role,
        password="Password123",
    )


def _create_driver_payload(code: str) -> DriverCreate:
    return DriverCreate(
        employee_code=code,
        full_name=f"Driver {code}",
        phone_number="0800000000",
        license_number=f"LIC{code}",
        license_type="B",
        license_expiry_date=date.today() + timedelta(days=365),
        status=DriverStatus.ACTIVE,
    )


def _create_vehicle_payload(registration: str) -> VehicleCreate:
    return VehicleCreate(
        registration_number=registration,
        vehicle_type=VehicleType.SEDAN,
        brand="Toyota",
        model="Camry",
        seating_capacity=4,
        fuel_type=FuelType.GASOLINE,
    )


@pytest.mark.asyncio
async def test_get_conflicting_booking_requests(async_session: AsyncSession) -> None:
    requester = await create_user(
        async_session,
        _create_user_payload("requester_conflict", UserRole.REQUESTER),
    )

    other_user = await create_user(
        async_session,
        _create_user_payload("other_requester", UserRole.REQUESTER),
    )

    base_start = datetime(2024, 3, 4, 9, 0, tzinfo=timezone.utc)
    base_end = base_start + timedelta(hours=2)

    booking_1 = BookingRequest(
        requester_id=requester.id,
        purpose="Morning trip",
        passenger_count=1,
        start_datetime=base_start,
        end_datetime=base_end,
        pickup_location="HQ",
        dropoff_location="Client Site",
        status=BookingStatus.REQUESTED,
    )

    booking_2 = BookingRequest(
        requester_id=requester.id,
        purpose="Overlap",
        passenger_count=1,
        start_datetime=base_start + timedelta(hours=1),
        end_datetime=base_end + timedelta(hours=1),
        pickup_location="HQ",
        dropoff_location="Airport",
        status=BookingStatus.APPROVED,
    )

    booking_3 = BookingRequest(
        requester_id=requester.id,
        purpose="Non overlapping",
        passenger_count=1,
        start_datetime=base_end + timedelta(hours=1),
        end_datetime=base_end + timedelta(hours=2),
        pickup_location="HQ",
        dropoff_location="Warehouse",
        status=BookingStatus.APPROVED,
    )

    cancelled = BookingRequest(
        requester_id=requester.id,
        purpose="Cancelled",
        passenger_count=1,
        start_datetime=base_start + timedelta(hours=1),
        end_datetime=base_end + timedelta(hours=1),
        pickup_location="HQ",
        dropoff_location="Warehouse",
        status=BookingStatus.CANCELLED,
    )

    other_user_booking = BookingRequest(
        requester_id=other_user.id,
        purpose="Other user",
        passenger_count=1,
        start_datetime=base_start + timedelta(hours=1),
        end_datetime=base_end + timedelta(hours=1),
        pickup_location="HQ",
        dropoff_location="Branch",
        status=BookingStatus.REQUESTED,
    )

    for record in (booking_1, booking_2, booking_3, cancelled, other_user_booking):
        async_session.add(record)
    await async_session.commit()

    window_start = base_start + timedelta(minutes=30)
    window_end = base_end + timedelta(minutes=30)

    conflicts = await get_conflicting_booking_requests(
        async_session, start=window_start, end=window_end
    )

    assert {booking.id for booking in conflicts} == {booking_1.id, booking_2.id, other_user_booking.id}

    requester_conflicts = await get_conflicting_booking_requests(
        async_session,
        start=window_start,
        end=window_end,
        requester_id=requester.id,
    )

    assert {booking.id for booking in requester_conflicts} == {booking_1.id, booking_2.id}

    excluded = await get_conflicting_booking_requests(
        async_session,
        start=window_start,
        end=window_end,
        exclude_booking_id=booking_1.id,
    )

    assert {booking.id for booking in excluded} == {booking_2.id, other_user_booking.id}


async def _setup_vehicle_conflict_environment(
    async_session: AsyncSession,
) -> tuple[Assignment, BookingRequest, Vehicle, Vehicle, Driver]:
    admin = await create_user(
        async_session,
        _create_user_payload("vehicle_admin", UserRole.FLEET_ADMIN),
    )

    requester = await create_user(
        async_session,
        _create_user_payload("vehicle_requester", UserRole.REQUESTER),
    )

    driver = await create_driver(async_session, _create_driver_payload("900"))

    vehicle_busy = await create_vehicle(async_session, _create_vehicle_payload("B 1000 XX"))
    vehicle_free = await create_vehicle(async_session, _create_vehicle_payload("B 2000 XX"))

    start = datetime(2024, 3, 4, 9, 0, tzinfo=timezone.utc)
    end = start + timedelta(hours=2)

    booking = BookingRequest(
        requester_id=requester.id,
        purpose="Morning assignment",
        passenger_count=1,
        start_datetime=start,
        end_datetime=end,
        pickup_location="HQ",
        dropoff_location="Branch",
        status=BookingStatus.ASSIGNED,
    )
    async_session.add(booking)
    await async_session.commit()

    assignment = Assignment(
        booking_request_id=booking.id,
        vehicle_id=vehicle_busy.id,
        driver_id=driver.id,
        assigned_by=admin.id,
        assigned_at=start - timedelta(hours=1),
    )
    async_session.add(assignment)
    await async_session.commit()

    await async_session.refresh(assignment)
    await async_session.refresh(booking)

    return assignment, booking, vehicle_busy, vehicle_free, driver


@pytest.mark.asyncio
async def test_vehicle_availability_conflicts(async_session: AsyncSession) -> None:
    assignment, booking, vehicle_busy, vehicle_free, _ = await _setup_vehicle_conflict_environment(async_session)

    overlap_start = booking.start_datetime + timedelta(minutes=30)
    overlap_end = booking.end_datetime + timedelta(minutes=30)

    conflicts = await get_vehicle_conflicting_assignments(
        async_session,
        vehicle_id=vehicle_busy.id,
        start=overlap_start,
        end=overlap_end,
    )

    assert [conflict.id for conflict in conflicts] == [assignment.id]

    assert not await is_vehicle_available(
        async_session,
        vehicle=vehicle_busy,
        start=overlap_start,
        end=overlap_end,
    )

    assert await is_vehicle_available(
        async_session,
        vehicle=vehicle_busy,
        start=booking.end_datetime + timedelta(hours=1),
        end=booking.end_datetime + timedelta(hours=2),
    )

    assert await is_vehicle_available(
        async_session,
        vehicle=vehicle_busy,
        start=overlap_start,
        end=overlap_end,
        exclude_booking_id=booking.id,
    )

    assert await is_vehicle_available(
        async_session,
        vehicle=vehicle_free,
        start=overlap_start,
        end=overlap_end,
    )


@pytest.mark.asyncio
async def test_ensure_driver_available_validation(async_session: AsyncSession) -> None:
    assignment, booking, vehicle_busy, _, driver = await _setup_vehicle_conflict_environment(async_session)

    overlap_start = booking.start_datetime + timedelta(minutes=15)
    overlap_end = booking.end_datetime - timedelta(minutes=15)

    with pytest.raises(ValueError):
        await ensure_driver_available(
            async_session,
            driver=driver,
            start=overlap_start,
            end=overlap_end,
        )

    await ensure_driver_available(
        async_session,
        driver=driver,
        start=booking.end_datetime + timedelta(hours=1),
        end=booking.end_datetime + timedelta(hours=2),
    )

    await ensure_driver_available(
        async_session,
        driver=driver,
        start=overlap_start,
        end=overlap_end,
        exclude_booking_id=booking.id,
    )


@pytest.mark.asyncio
async def test_suggest_alternative_bookings(async_session: AsyncSession) -> None:
    assignment, booking, vehicle_busy, vehicle_free, _ = await _setup_vehicle_conflict_environment(async_session)

    requested_start = booking.start_datetime + timedelta(hours=1)
    requested_end = requested_start + timedelta(hours=2)

    suggestions = await suggest_alternative_bookings(
        async_session,
        start=requested_start,
        end=requested_end,
        vehicle_type=VehicleType.SEDAN,
        limit=2,
    )

    assert len(suggestions) == 2

    by_vehicle = {suggestion.vehicle_id: suggestion for suggestion in suggestions}
    assert set(by_vehicle) == {vehicle_busy.id, vehicle_free.id}

    free_option = by_vehicle[vehicle_free.id]
    assert free_option.start_datetime == requested_start
    assert free_option.end_datetime == requested_end
    assert "requested" in free_option.reason.lower()

    busy_option = by_vehicle[vehicle_busy.id]
    expected_start = booking.end_datetime
    expected_end = expected_start + (requested_end - requested_start)
    assert busy_option.start_datetime == expected_start
    assert busy_option.end_datetime == expected_end
    assert "alternative" in busy_option.reason.lower()

    limited = await suggest_alternative_bookings(
        async_session,
        start=requested_start,
        end=requested_end,
        vehicle_type=VehicleType.SEDAN,
        limit=1,
    )

    assert len(limited) == 1
    limited_option = limited[0]
    assert limited_option.vehicle_id == vehicle_busy.id
    assert limited_option.start_datetime == booking.end_datetime

    excluded = await suggest_alternative_bookings(
        async_session,
        start=requested_start,
        end=requested_end,
        vehicle_type=VehicleType.SEDAN,
        exclude_vehicle_ids=[vehicle_free.id],
        limit=1,
    )

    assert len(excluded) == 1
    assert excluded[0].vehicle_id == vehicle_busy.id
    assert excluded[0].start_datetime == booking.end_datetime

    excluded_busy = await suggest_alternative_bookings(
        async_session,
        start=requested_start,
        end=requested_end,
        vehicle_type=VehicleType.SEDAN,
        exclude_vehicle_ids=[vehicle_busy.id],
        limit=1,
    )

    assert len(excluded_busy) == 1
    assert excluded_busy[0].vehicle_id == vehicle_free.id
    assert excluded_busy[0].start_datetime == requested_start

