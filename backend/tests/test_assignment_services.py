from __future__ import annotations

from datetime import date, datetime, timedelta, timezone

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.assignment_history import AssignmentChangeReason, AssignmentHistory
from app.models.booking import BookingStatus, VehiclePreference
from app.models.driver import DriverStatus
from app.models.user import User, UserRole
from app.models.vehicle import FuelType, VehicleStatus, VehicleType
from app.schemas import (
    AssignmentCreate,
    AssignmentUpdate,
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
    get_booking_request_by_id,
    suggest_assignment_options,
    transition_booking_status,
    update_assignment,
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


async def _create_driver(
    session: AsyncSession,
    *,
    employee_code: str,
    full_name: str,
    status: DriverStatus = DriverStatus.ACTIVE,
) -> int:
    driver = await create_driver(
        session,
        DriverCreate(
            employee_code=employee_code,
            full_name=full_name,
            phone_number="+62111111111",
            license_number=f"LIC-{employee_code}",
            license_type="B",
            license_expiry_date=date.today() + timedelta(days=365),
            status=status,
        ),
    )
    return driver.id


async def _create_vehicle(
    session: AsyncSession,
    *,
    registration: str,
    vehicle_type: VehicleType,
    seating_capacity: int,
    status: VehicleStatus = VehicleStatus.ACTIVE,
) -> int:
    vehicle = await create_vehicle(
        session,
        VehicleCreate(
            registration_number=registration,
            vehicle_type=vehicle_type,
            brand="Brand",
            model="Model",
            seating_capacity=seating_capacity,
            fuel_type=FuelType.GASOLINE,
            status=status,
        ),
    )
    return vehicle.id


async def _create_approved_booking(
    session: AsyncSession,
    *,
    requester_id: int,
    preference: VehiclePreference = VehiclePreference.ANY,
    passengers: int = 4,
    hours_from_now: int = 1,
    duration_hours: int = 2,
) -> int:
    start, end = _future_window(hours_from_now=hours_from_now, duration_hours=duration_hours)
    booking = await create_booking_request(
        session,
        BookingRequestCreate(
            requester_id=requester_id,
            purpose="Client visit",
            passenger_count=passengers,
            start_datetime=start,
            end_datetime=end,
            pickup_location="Head Office",
            dropoff_location="Client Site",
            vehicle_preference=preference,
            status=BookingStatus.REQUESTED,
        ),
    )

    booking = await transition_booking_status(
        session, booking_request=booking, new_status=BookingStatus.APPROVED
    )
    return booking.id


@pytest.mark.asyncio
async def test_suggest_assignments_prioritises_preference(
    async_session: AsyncSession,
) -> None:
    manager = await _create_manager(async_session)
    sedan_vehicle_id = await _create_vehicle(
        async_session,
        registration="B 1000 XYZ",
        vehicle_type=VehicleType.SEDAN,
        seating_capacity=4,
    )
    van_vehicle_id = await _create_vehicle(
        async_session,
        registration="B 2000 XYZ",
        vehicle_type=VehicleType.VAN,
        seating_capacity=8,
    )
    await _create_driver(async_session, employee_code="DRV1", full_name="Driver One")
    await _create_driver(async_session, employee_code="DRV2", full_name="Driver Two")

    booking_id = await _create_approved_booking(
        async_session,
        requester_id=manager.id,
        preference=VehiclePreference.SEDAN,
    )
    booking = await get_booking_request_by_id(async_session, booking_id)
    assert booking is not None

    suggestions = await suggest_assignment_options(
        async_session, booking_request=booking, limit=5
    )

    assert suggestions
    top = suggestions[0]
    assert top.vehicle.id == sedan_vehicle_id
    assert top.vehicle.matches_preference is True
    assert top.vehicle.vehicle_type == VehicleType.SEDAN


@pytest.mark.asyncio
async def test_suggest_assignments_handles_preference_fallback(
    async_session: AsyncSession,
) -> None:
    manager = await _create_manager(async_session)
    await _create_vehicle(
        async_session,
        registration="B 2100 XYZ",
        vehicle_type=VehicleType.VAN,
        seating_capacity=12,
    )
    await _create_vehicle(
        async_session,
        registration="B 2200 XYZ",
        vehicle_type=VehicleType.PICKUP,
        seating_capacity=2,
    )
    await _create_driver(async_session, employee_code="DRV10", full_name="Driver Ten")
    await _create_driver(async_session, employee_code="DRV11", full_name="Driver Eleven")

    booking_id = await _create_approved_booking(
        async_session,
        requester_id=manager.id,
        preference=VehiclePreference.BUS,
    )

    booking = await get_booking_request_by_id(async_session, booking_id)
    assert booking is not None

    suggestions = await suggest_assignment_options(
        async_session, booking_request=booking, limit=5
    )

    assert suggestions
    top = suggestions[0]
    assert top.vehicle.vehicle_type == VehicleType.VAN
    assert top.vehicle.matches_preference is False
    assert any("Closest available type" in reason for reason in top.reasons)


@pytest.mark.asyncio
async def test_create_assignment_auto_assigns_resources(
    async_session: AsyncSession,
) -> None:
    manager = await _create_manager(async_session)
    vehicle_id = await _create_vehicle(
        async_session,
        registration="B 3000 XYZ",
        vehicle_type=VehicleType.SEDAN,
        seating_capacity=4,
    )
    driver_id = await _create_driver(async_session, employee_code="DRV3", full_name="Driver Three")

    booking_id = await _create_approved_booking(
        async_session, requester_id=manager.id, preference=VehiclePreference.ANY
    )

    assignment = await create_assignment(
        async_session,
        AssignmentCreate(booking_request_id=booking_id),
        assigned_by=manager,
    )

    assert assignment.vehicle_id == vehicle_id
    assert assignment.driver_id == driver_id
    assert assignment.assigned_by == manager.id

    booking = await get_booking_request_by_id(async_session, booking_id)
    assert booking is not None and booking.status == BookingStatus.ASSIGNED


@pytest.mark.asyncio
async def test_auto_assign_balances_driver_workload(
    async_session: AsyncSession,
) -> None:
    manager = await _create_manager(async_session)
    primary_vehicle_id = await _create_vehicle(
        async_session,
        registration="B 3050 XYZ",
        vehicle_type=VehicleType.SEDAN,
        seating_capacity=4,
    )
    supporting_vehicle_id = await _create_vehicle(
        async_session,
        registration="B 3060 XYZ",
        vehicle_type=VehicleType.SEDAN,
        seating_capacity=4,
    )
    busy_driver_id = await _create_driver(
        async_session, employee_code="DRV7", full_name="Driver Seven"
    )
    balanced_driver_id = await _create_driver(
        async_session, employee_code="DRV8", full_name="Driver Eight"
    )

    booking_busy_one = await _create_approved_booking(
        async_session,
        requester_id=manager.id,
        hours_from_now=2,
    )
    await create_assignment(
        async_session,
        AssignmentCreate(
            booking_request_id=booking_busy_one,
            vehicle_id=supporting_vehicle_id,
            driver_id=busy_driver_id,
            auto_assign=False,
        ),
        assigned_by=manager,
    )

    booking_busy_two = await _create_approved_booking(
        async_session,
        requester_id=manager.id,
        hours_from_now=6,
    )
    await create_assignment(
        async_session,
        AssignmentCreate(
            booking_request_id=booking_busy_two,
            vehicle_id=supporting_vehicle_id,
            driver_id=busy_driver_id,
            auto_assign=False,
        ),
        assigned_by=manager,
    )

    target_booking_id = await _create_approved_booking(
        async_session,
        requester_id=manager.id,
        hours_from_now=12,
    )

    assignment = await create_assignment(
        async_session,
        AssignmentCreate(
            booking_request_id=target_booking_id,
            vehicle_id=primary_vehicle_id,
        ),
        assigned_by=manager,
    )

    assert assignment.driver_id == balanced_driver_id


@pytest.mark.asyncio
async def test_assignment_conflict_prevention(async_session: AsyncSession) -> None:
    manager = await _create_manager(async_session)
    vehicle_id = await _create_vehicle(
        async_session,
        registration="B 4000 XYZ",
        vehicle_type=VehicleType.VAN,
        seating_capacity=10,
    )
    driver_id = await _create_driver(async_session, employee_code="DRV4", full_name="Driver Four")

    booking_one_id = await _create_approved_booking(
        async_session,
        requester_id=manager.id,
        preference=VehiclePreference.ANY,
    )
    booking_two_id = await _create_approved_booking(
        async_session,
        requester_id=manager.id,
        preference=VehiclePreference.ANY,
    )

    await create_assignment(
        async_session,
        AssignmentCreate(booking_request_id=booking_one_id),
        assigned_by=manager,
    )

    with pytest.raises(ValueError):
        await create_assignment(
            async_session,
            AssignmentCreate(
                booking_request_id=booking_two_id,
                vehicle_id=vehicle_id,
                driver_id=driver_id,
                auto_assign=False,
            ),
            assigned_by=manager,
        )


@pytest.mark.asyncio
async def test_update_assignment_allows_manual_override(
    async_session: AsyncSession,
) -> None:
    manager = await _create_manager(async_session)
    vehicle_one_id = await _create_vehicle(
        async_session,
        registration="B 5000 XYZ",
        vehicle_type=VehicleType.SEDAN,
        seating_capacity=4,
    )
    vehicle_two_id = await _create_vehicle(
        async_session,
        registration="B 6000 XYZ",
        vehicle_type=VehicleType.VAN,
        seating_capacity=8,
    )
    driver_one_id = await _create_driver(
        async_session, employee_code="DRV5", full_name="Driver Five"
    )
    driver_two_id = await _create_driver(
        async_session, employee_code="DRV6", full_name="Driver Six"
    )

    booking_id = await _create_approved_booking(
        async_session, requester_id=manager.id, preference=VehiclePreference.ANY
    )

    assignment = await create_assignment(
        async_session,
        AssignmentCreate(booking_request_id=booking_id),
        assigned_by=manager,
    )

    assert assignment.vehicle_id == vehicle_one_id
    assert assignment.driver_id == driver_one_id

    updated = await update_assignment(
        async_session,
        assignment=assignment,
        assignment_update=AssignmentUpdate(
            vehicle_id=vehicle_two_id,
            driver_id=driver_two_id,
            auto_assign=False,
        ),
        assigned_by=manager,
    )

    assert updated.vehicle_id == vehicle_two_id
    assert updated.driver_id == driver_two_id
    assert updated.assigned_by == manager.id
    assert updated.assigned_at >= assignment.assigned_at


@pytest.mark.asyncio
async def test_assignment_history_records_changes(
    async_session: AsyncSession,
) -> None:
    manager = await _create_manager(async_session)
    vehicle_one_id = await _create_vehicle(
        async_session,
        registration="B 6100 XYZ",
        vehicle_type=VehicleType.SEDAN,
        seating_capacity=4,
    )
    vehicle_two_id = await _create_vehicle(
        async_session,
        registration="B 6200 XYZ",
        vehicle_type=VehicleType.VAN,
        seating_capacity=8,
    )
    driver_one_id = await _create_driver(
        async_session, employee_code="DRV9", full_name="Driver Nine"
    )
    driver_two_id = await _create_driver(
        async_session, employee_code="DRV12", full_name="Driver Twelve"
    )

    booking_id = await _create_approved_booking(
        async_session, requester_id=manager.id, preference=VehiclePreference.ANY
    )

    assignment = await create_assignment(
        async_session,
        AssignmentCreate(
            booking_request_id=booking_id,
            vehicle_id=vehicle_one_id,
            driver_id=driver_one_id,
            auto_assign=False,
            notes="Initial assignment",
        ),
        assigned_by=manager,
    )

    result = await async_session.execute(
        select(AssignmentHistory)
        .where(AssignmentHistory.assignment_id == assignment.id)
        .order_by(AssignmentHistory.created_at)
    )
    history_entries = list(result.scalars().all())
    assert len(history_entries) == 1

    created_entry = history_entries[0]
    assert created_entry.change_reason == AssignmentChangeReason.CREATED
    assert created_entry.previous_vehicle_id is None
    assert created_entry.vehicle_id == vehicle_one_id
    assert created_entry.previous_driver_id is None
    assert created_entry.driver_id == driver_one_id
    assert created_entry.notes == "Initial assignment"

    updated = await update_assignment(
        async_session,
        assignment=assignment,
        assignment_update=AssignmentUpdate(
            vehicle_id=vehicle_two_id,
            driver_id=driver_two_id,
            notes="Updated assignment",
            auto_assign=False,
        ),
        assigned_by=manager,
    )

    result = await async_session.execute(
        select(AssignmentHistory)
        .where(AssignmentHistory.assignment_id == assignment.id)
        .order_by(AssignmentHistory.created_at)
    )
    history_entries = list(result.scalars().all())
    assert len(history_entries) == 2

    change_entry = history_entries[-1]
    assert change_entry.change_reason == AssignmentChangeReason.UPDATED
    assert change_entry.previous_vehicle_id == vehicle_one_id
    assert change_entry.vehicle_id == vehicle_two_id
    assert change_entry.previous_driver_id == driver_one_id
    assert change_entry.driver_id == driver_two_id
    assert change_entry.previous_notes == "Initial assignment"
    assert change_entry.notes == "Updated assignment"

    assert updated.vehicle_id == vehicle_two_id
    assert updated.driver_id == driver_two_id
