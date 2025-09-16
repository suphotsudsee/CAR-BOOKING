"""Unit tests for booking request service functions."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.booking import BookingStatus, VehiclePreference
from app.models.user import UserRole
from app.schemas import (
    BookingRequestCreate,
    BookingRequestUpdate,
    UserCreate,
)
from app.services import (
    create_booking_request,
    create_user,
    delete_booking_request,
    get_booking_request_by_id,
    list_booking_requests,
    transition_booking_status,
    update_booking_request,
)


def _future_window(hours_from_now: int = 1, duration_hours: int = 2) -> tuple[datetime, datetime]:
    start = datetime.now(timezone.utc) + timedelta(hours=hours_from_now)
    end = start + timedelta(hours=duration_hours)
    return start, end


@pytest.mark.asyncio
async def test_create_booking_request(async_session: AsyncSession) -> None:
    user = await create_user(
        async_session,
        UserCreate(
            username="requester1",
            email="requester1@example.com",
            full_name="Requester One",
            department="Sales",
            role=UserRole.REQUESTER,
            password="Password123",
        ),
    )

    start, end = _future_window()
    booking = await create_booking_request(
        async_session,
        BookingRequestCreate(
            requester_id=user.id,
            department="  Finance  ",
            purpose="  Team meeting planning  ",
            passenger_count=3,
            start_datetime=start,
            end_datetime=end,
            pickup_location="  Headquarters  ",
            dropoff_location=" Branch Office ",
            vehicle_preference=VehiclePreference.VAN,
            special_requirements="  Child seat  ",
        ),
    )

    assert booking.id is not None
    assert booking.requester_id == user.id
    assert booking.department == "Finance"
    assert booking.purpose == "Team meeting planning"
    assert booking.pickup_location == "Headquarters"
    assert booking.dropoff_location == "Branch Office"
    assert booking.vehicle_preference == VehiclePreference.VAN
    assert booking.status == BookingStatus.DRAFT
    assert booking.submitted_at is None


@pytest.mark.asyncio
async def test_create_booking_request_submitted(async_session: AsyncSession) -> None:
    user = await create_user(
        async_session,
        UserCreate(
            username="requester2",
            email="requester2@example.com",
            full_name="Requester Two",
            department="Operations",
            role=UserRole.REQUESTER,
            password="Password123",
        ),
    )

    start, end = _future_window(hours_from_now=2)
    booking = await create_booking_request(
        async_session,
        BookingRequestCreate(
            requester_id=user.id,
            purpose="Client visit",
            passenger_count=2,
            start_datetime=start,
            end_datetime=end,
            pickup_location="Office",
            dropoff_location="Airport",
            status=BookingStatus.REQUESTED,
        ),
    )

    assert booking.status == BookingStatus.REQUESTED
    assert booking.submitted_at is not None


@pytest.mark.asyncio
async def test_create_booking_request_requires_requester(async_session: AsyncSession) -> None:
    start, end = _future_window()

    with pytest.raises(ValueError):
        await create_booking_request(
            async_session,
            BookingRequestCreate(
                purpose="Training",
                passenger_count=4,
                start_datetime=start,
                end_datetime=end,
                pickup_location="HQ",
                dropoff_location="Training Center",
            ),
        )


@pytest.mark.asyncio
async def test_update_booking_request(async_session: AsyncSession) -> None:
    user = await create_user(
        async_session,
        UserCreate(
            username="requester3",
            email="requester3@example.com",
            full_name="Requester Three",
            department="Finance",
            role=UserRole.REQUESTER,
            password="Password123",
        ),
    )

    start, end = _future_window()
    booking = await create_booking_request(
        async_session,
        BookingRequestCreate(
            requester_id=user.id,
            department="Finance",
            purpose="Budget review",
            passenger_count=1,
            start_datetime=start,
            end_datetime=end,
            pickup_location="Main HQ",
            dropoff_location="City Hall",
            special_requirements=None,
        ),
    )

    new_start = start + timedelta(hours=1)
    new_end = end + timedelta(hours=1)

    updated = await update_booking_request(
        async_session,
        booking_request=booking,
        booking_update=BookingRequestUpdate(
            department="  Operations  ",
            passenger_count=4,
            start_datetime=new_start,
            end_datetime=new_end,
            pickup_location=" Secondary Office  ",
            special_requirements="  VIP guest  ",
        ),
    )

    assert updated.department == "Operations"
    assert updated.passenger_count == 4
    assert updated.start_datetime == new_start.replace(tzinfo=None)
    assert updated.end_datetime == new_end.replace(tzinfo=None)
    assert updated.pickup_location == "Secondary Office"
    assert updated.special_requirements == "VIP guest"


@pytest.mark.asyncio
async def test_update_booking_request_disallowed(async_session: AsyncSession) -> None:
    user = await create_user(
        async_session,
        UserCreate(
            username="requester4",
            email="requester4@example.com",
            full_name="Requester Four",
            department="Engineering",
            role=UserRole.REQUESTER,
            password="Password123",
        ),
    )

    start, end = _future_window()
    booking = await create_booking_request(
        async_session,
        BookingRequestCreate(
            requester_id=user.id,
            purpose="Site inspection",
            passenger_count=2,
            start_datetime=start,
            end_datetime=end,
            pickup_location="Plant",
            dropoff_location="Warehouse",
        ),
    )

    await transition_booking_status(
        async_session, booking_request=booking, new_status=BookingStatus.CANCELLED
    )

    with pytest.raises(ValueError):
        await update_booking_request(
            async_session,
            booking_request=booking,
            booking_update=BookingRequestUpdate(purpose="Updated purpose"),
        )


@pytest.mark.asyncio
async def test_transition_booking_status_workflow(async_session: AsyncSession) -> None:
    user = await create_user(
        async_session,
        UserCreate(
            username="requester5",
            email="requester5@example.com",
            full_name="Requester Five",
            department="Logistics",
            role=UserRole.REQUESTER,
            password="Password123",
        ),
    )

    start, end = _future_window()
    booking = await create_booking_request(
        async_session,
        BookingRequestCreate(
            requester_id=user.id,
            purpose="Shuttle",
            passenger_count=5,
            start_datetime=start,
            end_datetime=end,
            pickup_location="Office",
            dropoff_location="Convention Center",
        ),
    )

    booking = await transition_booking_status(
        async_session, booking_request=booking, new_status=BookingStatus.REQUESTED
    )
    assert booking.status == BookingStatus.REQUESTED
    assert booking.submitted_at is not None

    booking = await transition_booking_status(
        async_session, booking_request=booking, new_status=BookingStatus.APPROVED
    )
    assert booking.status == BookingStatus.APPROVED

    with pytest.raises(ValueError):
        await transition_booking_status(
            async_session, booking_request=booking, new_status=BookingStatus.COMPLETED
        )


@pytest.mark.asyncio
async def test_list_booking_requests_filters(async_session: AsyncSession) -> None:
    requester_a = await create_user(
        async_session,
        UserCreate(
            username="requester6",
            email="requester6@example.com",
            full_name="Requester Six",
            department="Support",
            role=UserRole.REQUESTER,
            password="Password123",
        ),
    )
    requester_b = await create_user(
        async_session,
        UserCreate(
            username="requester7",
            email="requester7@example.com",
            full_name="Requester Seven",
            department="Support",
            role=UserRole.REQUESTER,
            password="Password123",
        ),
    )

    start1, end1 = _future_window(hours_from_now=3)
    start2, end2 = _future_window(hours_from_now=5)

    booking_a = await create_booking_request(
        async_session,
        BookingRequestCreate(
            requester_id=requester_a.id,
            department="Support",
            purpose="Airport transfer",
            passenger_count=2,
            start_datetime=start1,
            end_datetime=end1,
            pickup_location="HQ",
            dropoff_location="Airport",
            status=BookingStatus.REQUESTED,
        ),
    )

    booking_b = await create_booking_request(
        async_session,
        BookingRequestCreate(
            requester_id=requester_b.id,
            department="Support",
            purpose="Client visit",
            passenger_count=3,
            start_datetime=start2,
            end_datetime=end2,
            pickup_location="Hotel",
            dropoff_location="HQ",
        ),
    )

    requested = await list_booking_requests(
        async_session, status=BookingStatus.REQUESTED
    )
    assert [b.id for b in requested] == [booking_a.id]

    filtered = await list_booking_requests(
        async_session,
        requester_id=requester_b.id,
        search="hotel",
    )
    assert [b.id for b in filtered] == [booking_b.id]


@pytest.mark.asyncio
async def test_delete_booking_request(async_session: AsyncSession) -> None:
    user = await create_user(
        async_session,
        UserCreate(
            username="requester8",
            email="requester8@example.com",
            full_name="Requester Eight",
            department="HR",
            role=UserRole.REQUESTER,
            password="Password123",
        ),
    )

    start, end = _future_window()
    booking = await create_booking_request(
        async_session,
        BookingRequestCreate(
            requester_id=user.id,
            purpose="Orientation",
            passenger_count=1,
            start_datetime=start,
            end_datetime=end,
            pickup_location="HQ",
            dropoff_location="Training Center",
        ),
    )

    await delete_booking_request(async_session, booking_request=booking)
    deleted = await get_booking_request_by_id(async_session, booking.id)
    assert deleted is None

    booking = await create_booking_request(
        async_session,
        BookingRequestCreate(
            requester_id=user.id,
            purpose="Site visit",
            passenger_count=2,
            start_datetime=start,
            end_datetime=end,
            pickup_location="HQ",
            dropoff_location="Plant",
        ),
    )

    await transition_booking_status(
        async_session, booking_request=booking, new_status=BookingStatus.REQUESTED
    )
    await transition_booking_status(
        async_session, booking_request=booking, new_status=BookingStatus.APPROVED
    )

    with pytest.raises(ValueError):
        await delete_booking_request(async_session, booking_request=booking)

