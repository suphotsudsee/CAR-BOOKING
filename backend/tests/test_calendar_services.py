from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import (
    CalendarEventType,
    CalendarResourceType,
    UserRole,
    VehicleType,
    BookingStatus,
)
from app.schemas import (
    AssignmentCreate,
    BookingRequestCreate,
    CalendarEventCreate,
    DriverCreate,
    UserCreate,
    VehicleCreate,
)
from app.services import (
    build_resource_calendar_view,
    create_assignment,
    create_booking_request,
    create_calendar_event,
    create_driver,
    create_user,
    create_vehicle,
    get_calendar_event_by_id,
    transition_booking_status,
)


@pytest.mark.asyncio
async def test_create_manual_calendar_event(async_session: AsyncSession) -> None:
    manager = await create_user(
        async_session,
        UserCreate(
            username="calendar_manager",
            email="calendar_manager@example.com",
            full_name="Calendar Manager",
            department="Operations",
            role=UserRole.FLEET_ADMIN,
            password="Password123",
        ),
    )

    vehicle = await create_vehicle(
        async_session,
        VehicleCreate(
            registration_number="B 9991 XYZ",
            vehicle_type=VehicleType.SEDAN,
            brand="Brand",
            model="Model",
            seating_capacity=4,
        ),
    )

    start = datetime.now(timezone.utc) + timedelta(hours=1)
    end = start + timedelta(hours=2)

    event = await create_calendar_event(
        async_session,
        CalendarEventCreate(
            resource_type=CalendarResourceType.VEHICLE,
            resource_id=vehicle.id,
            title="Scheduled maintenance",
            start=start,
            end=end,
            event_type=CalendarEventType.MAINTENANCE,
        ),
        created_by_id=manager.id,
    )

    stored = await get_calendar_event_by_id(async_session, event.id)
    assert stored is not None
    assert stored.created_by_id == manager.id
    assert stored.resource_id == vehicle.id
    assert stored.event_type == CalendarEventType.MAINTENANCE


@pytest.mark.asyncio
async def test_calendar_view_highlights_conflicts(async_session: AsyncSession) -> None:
    manager = await create_user(
        async_session,
        UserCreate(
            username="calendar_admin",
            email="calendar_admin@example.com",
            full_name="Calendar Admin",
            department="Operations",
            role=UserRole.FLEET_ADMIN,
            password="Password123",
        ),
    )

    driver = await create_driver(
        async_session,
        DriverCreate(
            employee_code="DRV-CAL",
            full_name="Calendar Driver",
            phone_number="+621111111",
            license_number="LIC-CAL",
            license_type="B",
            license_expiry_date=datetime.now(timezone.utc).date() + timedelta(days=365),
        ),
    )

    vehicle = await create_vehicle(
        async_session,
        VehicleCreate(
            registration_number="B 9000 CAL",
            vehicle_type=VehicleType.VAN,
            brand="Brand",
            model="Model",
            seating_capacity=8,
        ),
    )

    booking_window_start = datetime.now(timezone.utc) + timedelta(hours=4)
    booking_window_end = booking_window_start + timedelta(hours=3)

    booking = await create_booking_request(
        async_session,
        BookingRequestCreate(
            requester_id=manager.id,
            purpose="Client visit",
            passenger_count=4,
            start_datetime=booking_window_start,
            end_datetime=booking_window_end,
            pickup_location="HQ",
            dropoff_location="Client",
            status=BookingStatus.REQUESTED,
        ),
    )

    booking = await transition_booking_status(
        async_session,
        booking_request=booking,
        new_status=BookingStatus.APPROVED,
    )

    assignment = await create_assignment(
        async_session,
        AssignmentCreate(
            booking_request_id=booking.id,
            vehicle_id=vehicle.id,
            driver_id=driver.id,
            auto_assign=False,
        ),
        assigned_by=manager,
    )

    manual_start = booking_window_start + timedelta(hours=1)
    manual_end = manual_start + timedelta(hours=2)

    manual_event = await create_calendar_event(
        async_session,
        CalendarEventCreate(
            resource_type=CalendarResourceType.VEHICLE,
            resource_id=vehicle.id,
            title="Tyre replacement",
            start=manual_start,
            end=manual_end,
            event_type=CalendarEventType.MAINTENANCE,
        ),
        created_by_id=manager.id,
    )

    calendar_window_start = booking_window_start - timedelta(hours=1)
    calendar_window_end = booking_window_end + timedelta(hours=1)

    views = await build_resource_calendar_view(
        async_session,
        resource_type=CalendarResourceType.VEHICLE,
        start=calendar_window_start,
        end=calendar_window_end,
    )

    assert len(views) == 1
    view = views[0]
    assert view.resource_id == vehicle.id
    assert len(view.events) == 2

    event_refs = {event.reference_id for event in view.events}
    assert f"assignment:{assignment.id}" in event_refs
    assert f"manual:{manual_event.id}" in event_refs

    assert view.conflicts, "Expected overlapping events to be flagged"
    conflict_refs = {ref for conflict in view.conflicts for ref in conflict.event_reference_ids}
    assert f"assignment:{assignment.id}" in conflict_refs
    assert f"manual:{manual_event.id}" in conflict_refs


@pytest.mark.asyncio
async def test_calendar_view_rejects_unknown_resources(async_session: AsyncSession) -> None:
    start = datetime.now(timezone.utc) + timedelta(hours=1)
    end = start + timedelta(hours=2)

    with pytest.raises(ValueError):
        await build_resource_calendar_view(
            async_session,
            resource_type=CalendarResourceType.VEHICLE,
            start=start,
            end=end,
            resource_ids=[999],
        )
