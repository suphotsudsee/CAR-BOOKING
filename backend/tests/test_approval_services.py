from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.approval import ApprovalDecision
from app.models.booking import BookingStatus, VehiclePreference
from app.models.user import UserRole
from app.schemas import BookingRequestCreate, UserCreate
from app.services import (
    create_approval_delegation,
    create_booking_request,
    create_user,
    get_booking_request_by_id,
    get_pending_booking_approval_notifications,
    list_booking_approvals,
    record_booking_approval,
)


def _future_window(hours_from_now: int = 1, duration_hours: int = 2) -> tuple[datetime, datetime]:
    start = datetime.now(timezone.utc) + timedelta(hours=hours_from_now)
    end = start + timedelta(hours=duration_hours)
    return start, end


@pytest.mark.asyncio
async def test_record_booking_approval_updates_status(async_session: AsyncSession) -> None:
    manager = await create_user(
        async_session,
        UserCreate(
            username="manager_approval",
            email="manager_approval@example.com",
            full_name="Manager Approver",
            department="Finance",
            role=UserRole.MANAGER,
            password="SecurePass123",
        ),
    )

    requester = await create_user(
        async_session,
        UserCreate(
            username="approval_requester",
            email="approval_requester@example.com",
            full_name="Approval Requester",
            department="Finance",
            role=UserRole.REQUESTER,
            password="SecurePass123",
        ),
    )

    start, end = _future_window()
    booking = await create_booking_request(
        async_session,
        BookingRequestCreate(
            requester_id=requester.id,
            department="Finance",
            purpose="Quarterly review meeting",
            passenger_count=3,
            start_datetime=start,
            end_datetime=end,
            pickup_location="Head Office",
            dropoff_location="City Hall",
            vehicle_preference=VehiclePreference.SEDAN,
            status=BookingStatus.REQUESTED,
        ),
    )

    result = await record_booking_approval(
        async_session,
        booking_request=booking,
        approver=manager,
        decision=ApprovalDecision.APPROVED,
        reason="   Approved for leadership visit   ",
    )

    assert result.booking.status == BookingStatus.APPROVED
    assert result.approval.decision == ApprovalDecision.APPROVED
    assert result.approval.reason == "Approved for leadership visit"
    assert result.notification.reason == "Approved for leadership visit"
    assert "approved" in result.notification.message.lower()

    fetched = await get_booking_request_by_id(async_session, booking.id)
    assert fetched is not None
    assert fetched.status == BookingStatus.APPROVED

    history = await list_booking_approvals(async_session, booking_request_id=booking.id)
    assert len(history) == 1
    assert history[0].decision == ApprovalDecision.APPROVED


@pytest.mark.asyncio
async def test_record_booking_rejection_tracks_reason(async_session: AsyncSession) -> None:
    manager = await create_user(
        async_session,
        UserCreate(
            username="manager_reject",
            email="manager_reject@example.com",
            full_name="Manager Rejector",
            department="Finance",
            role=UserRole.MANAGER,
            password="SecurePass123",
        ),
    )

    requester = await create_user(
        async_session,
        UserCreate(
            username="rejection_requester",
            email="rejection_requester@example.com",
            full_name="Rejection Requester",
            department="Finance",
            role=UserRole.REQUESTER,
            password="SecurePass123",
        ),
    )

    start, end = _future_window(hours_from_now=3)
    booking = await create_booking_request(
        async_session,
        BookingRequestCreate(
            requester_id=requester.id,
            department="Finance",
            purpose="Client site visit",
            passenger_count=2,
            start_datetime=start,
            end_datetime=end,
            pickup_location="Office",
            dropoff_location="Client HQ",
            status=BookingStatus.REQUESTED,
        ),
    )

    result = await record_booking_approval(
        async_session,
        booking_request=booking,
        approver=manager,
        decision=ApprovalDecision.REJECTED,
        reason="  Insufficient lead time  ",
    )

    assert result.booking.status == BookingStatus.REJECTED
    assert result.approval.decision == ApprovalDecision.REJECTED
    assert result.approval.reason == "Insufficient lead time"
    assert "rejected" in result.notification.message.lower()


@pytest.mark.asyncio
async def test_record_booking_approval_requires_manager(async_session: AsyncSession) -> None:
    requester = await create_user(
        async_session,
        UserCreate(
            username="self_approver",
            email="self_approver@example.com",
            full_name="Self Approver",
            department="Finance",
            role=UserRole.REQUESTER,
            password="SecurePass123",
        ),
    )

    start, end = _future_window(hours_from_now=4)
    booking = await create_booking_request(
        async_session,
        BookingRequestCreate(
            requester_id=requester.id,
            purpose="Team workshop",
            passenger_count=5,
            start_datetime=start,
            end_datetime=end,
            pickup_location="Main Office",
            dropoff_location="Retreat Center",
            status=BookingStatus.REQUESTED,
        ),
    )

    with pytest.raises(ValueError):
        await record_booking_approval(
            async_session,
            booking_request=booking,
            approver=requester,
            decision=ApprovalDecision.APPROVED,
        )


@pytest.mark.asyncio
async def test_record_booking_approval_disallows_self_review(
    async_session: AsyncSession,
) -> None:
    manager = await create_user(
        async_session,
        UserCreate(
            username="manager_self",
            email="manager_self@example.com",
            full_name="Manager Self",
            department="Executive",
            role=UserRole.MANAGER,
            password="SecurePass123",
        ),
    )

    start, end = _future_window(hours_from_now=5)
    booking = await create_booking_request(
        async_session,
        BookingRequestCreate(
            requester_id=manager.id,
            purpose="Executive briefing",
            passenger_count=1,
            start_datetime=start,
            end_datetime=end,
            pickup_location="HQ",
            dropoff_location="Airport",
            status=BookingStatus.REQUESTED,
        ),
    )

    with pytest.raises(ValueError):
        await record_booking_approval(
            async_session,
            booking_request=booking,
            approver=manager,
            decision=ApprovalDecision.APPROVED,
        )


@pytest.mark.asyncio
async def test_multi_level_approval_flow_requires_sequence(
    async_session: AsyncSession,
) -> None:
    sales_manager = await create_user(
        async_session,
        UserCreate(
            username="sales_manager",
            email="sales_manager@example.com",
            full_name="Sales Manager",
            department="Sales",
            role=UserRole.MANAGER,
            password="SecurePass123",
        ),
    )

    operations_manager = await create_user(
        async_session,
        UserCreate(
            username="operations_manager",
            email="operations_manager@example.com",
            full_name="Operations Manager",
            department="Operations",
            role=UserRole.MANAGER,
            password="SecurePass123",
        ),
    )

    fleet_admin = await create_user(
        async_session,
        UserCreate(
            username="fleet_admin",
            email="fleet_admin@example.com",
            full_name="Fleet Admin",
            department="Fleet",
            role=UserRole.FLEET_ADMIN,
            password="SecurePass123",
        ),
    )

    requester = await create_user(
        async_session,
        UserCreate(
            username="sales_requester",
            email="sales_requester@example.com",
            full_name="Sales Requester",
            department="Sales",
            role=UserRole.REQUESTER,
            password="SecurePass123",
        ),
    )

    start, end = _future_window(hours_from_now=2, duration_hours=12)
    booking = await create_booking_request(
        async_session,
        BookingRequestCreate(
            requester_id=requester.id,
            department="Sales",
            purpose="International delegation visit",
            passenger_count=9,
            start_datetime=start,
            end_datetime=end,
            pickup_location="Head Office",
            dropoff_location="Airport",
            vehicle_preference=VehiclePreference.BUS,
            status=BookingStatus.REQUESTED,
        ),
    )

    with pytest.raises(ValueError):
        await record_booking_approval(
            async_session,
            booking_request=booking,
            approver=fleet_admin,
            decision=ApprovalDecision.APPROVED,
        )

    first_level = await record_booking_approval(
        async_session,
        booking_request=booking,
        approver=sales_manager,
        decision=ApprovalDecision.APPROVED,
    )
    assert first_level.approval.approval_level == 1
    assert first_level.booking.status == BookingStatus.REQUESTED

    second_level = await record_booking_approval(
        async_session,
        booking_request=booking,
        approver=operations_manager,
        decision=ApprovalDecision.APPROVED,
    )
    assert second_level.approval.approval_level == 2
    assert second_level.booking.status == BookingStatus.REQUESTED

    final_level = await record_booking_approval(
        async_session,
        booking_request=booking,
        approver=fleet_admin,
        decision=ApprovalDecision.APPROVED,
    )
    assert final_level.approval.approval_level == 3
    assert final_level.booking.status == BookingStatus.APPROVED

    history = await list_booking_approvals(async_session, booking_request_id=booking.id)
    assert [approval.approval_level for approval in history] == [1, 2, 3]


@pytest.mark.asyncio
async def test_hierarchical_routing_when_department_manager_missing(
    async_session: AsyncSession,
) -> None:
    operations_manager = await create_user(
        async_session,
        UserCreate(
            username="ops_only_manager",
            email="ops_only_manager@example.com",
            full_name="Operations Only Manager",
            department="Operations",
            role=UserRole.MANAGER,
            password="SecurePass123",
        ),
    )

    requester = await create_user(
        async_session,
        UserCreate(
            username="support_requester",
            email="support_requester@example.com",
            full_name="Support Requester",
            department="Support",
            role=UserRole.REQUESTER,
            password="SecurePass123",
        ),
    )

    start, end = _future_window(hours_from_now=1, duration_hours=4)
    booking = await create_booking_request(
        async_session,
        BookingRequestCreate(
            requester_id=requester.id,
            department="Support",
            purpose="On-site troubleshooting",
            passenger_count=2,
            start_datetime=start,
            end_datetime=end,
            pickup_location="HQ",
            dropoff_location="Client Site",
            status=BookingStatus.REQUESTED,
        ),
    )

    result = await record_booking_approval(
        async_session,
        booking_request=booking,
        approver=operations_manager,
        decision=ApprovalDecision.APPROVED,
    )

    assert result.approval.approval_level == 1
    assert result.booking.status == BookingStatus.APPROVED


@pytest.mark.asyncio
async def test_delegated_approver_records_approval(
    async_session: AsyncSession,
) -> None:
    finance_manager = await create_user(
        async_session,
        UserCreate(
            username="finance_manager",
            email="finance_manager@example.com",
            full_name="Finance Manager",
            department="Finance",
            role=UserRole.MANAGER,
            password="SecurePass123",
        ),
    )

    delegate_manager = await create_user(
        async_session,
        UserCreate(
            username="delegate_manager",
            email="delegate_manager@example.com",
            full_name="Delegate Manager",
            department="Operations",
            role=UserRole.MANAGER,
            password="SecurePass123",
        ),
    )

    requester = await create_user(
        async_session,
        UserCreate(
            username="finance_requester",
            email="finance_requester@example.com",
            full_name="Finance Requester",
            department="Finance",
            role=UserRole.REQUESTER,
            password="SecurePass123",
        ),
    )

    start, end = _future_window(hours_from_now=2, duration_hours=3)
    booking = await create_booking_request(
        async_session,
        BookingRequestCreate(
            requester_id=requester.id,
            department="Finance",
            purpose="Supplier meeting",
            passenger_count=3,
            start_datetime=start,
            end_datetime=end,
            pickup_location="Finance Office",
            dropoff_location="Downtown",
            status=BookingStatus.REQUESTED,
        ),
    )

    with pytest.raises(ValueError):
        await record_booking_approval(
            async_session,
            booking_request=booking,
            approver=delegate_manager,
            decision=ApprovalDecision.APPROVED,
        )

    await create_approval_delegation(
        async_session,
        delegator=finance_manager,
        delegate=delegate_manager,
    )

    delegated_result = await record_booking_approval(
        async_session,
        booking_request=booking,
        approver=delegate_manager,
        decision=ApprovalDecision.APPROVED,
        reason="Covering for finance manager",
    )

    assert delegated_result.approval.delegated_from_id == finance_manager.id
    assert "delegated" in delegated_result.notification.message.lower()
    assert delegated_result.booking.status == BookingStatus.APPROVED


@pytest.mark.asyncio
async def test_get_pending_booking_approval_notifications(
    async_session: AsyncSession,
) -> None:
    requester_one = await create_user(
        async_session,
        UserCreate(
            username="pending_one",
            email="pending_one@example.com",
            full_name="Pending One",
            department="Sales",
            role=UserRole.REQUESTER,
            password="SecurePass123",
        ),
    )

    requester_two = await create_user(
        async_session,
        UserCreate(
            username="pending_two",
            email="pending_two@example.com",
            full_name="Pending Two",
            department="Support",
            role=UserRole.REQUESTER,
            password="SecurePass123",
        ),
    )

    start_one, end_one = _future_window(hours_from_now=1)
    booking_one = await create_booking_request(
        async_session,
        BookingRequestCreate(
            requester_id=requester_one.id,
            purpose="Site inspection",
            passenger_count=3,
            start_datetime=start_one,
            end_datetime=end_one,
            pickup_location="HQ",
            dropoff_location="Factory",
            status=BookingStatus.REQUESTED,
        ),
    )

    start_two, end_two = _future_window(hours_from_now=2)
    booking_two = await create_booking_request(
        async_session,
        BookingRequestCreate(
            requester_id=requester_two.id,
            purpose="Client onboarding",
            passenger_count=2,
            start_datetime=start_two,
            end_datetime=end_two,
            pickup_location="HQ",
            dropoff_location="Client Office",
            status=BookingStatus.REQUESTED,
        ),
    )

    assert booking_one.submitted_at is not None
    assert booking_two.submitted_at is not None

    booking_one.submitted_at = booking_one.submitted_at - timedelta(hours=6)
    booking_two.submitted_at = booking_two.submitted_at - timedelta(hours=2)
    await async_session.commit()
    await async_session.refresh(booking_one)
    await async_session.refresh(booking_two)

    notifications = await get_pending_booking_approval_notifications(async_session)
    assert [notification.booking_id for notification in notifications] == [
        booking_one.id,
        booking_two.id,
    ]

    filtered = await get_pending_booking_approval_notifications(
        async_session, pending_for_hours=4
    )
    assert len(filtered) == 1
    assert filtered[0].booking_id == booking_one.id
    assert filtered[0].hours_pending >= 4

    with pytest.raises(ValueError):
        await get_pending_booking_approval_notifications(
            async_session, pending_for_hours=-1
        )

