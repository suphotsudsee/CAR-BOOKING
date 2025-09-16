"""Service layer helpers for booking approval workflow management."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import Select, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.approval import Approval, ApprovalDecision
from app.models.booking import BookingRequest, BookingStatus
from app.models.user import User, UserRole
from app.services.booking import transition_booking_status


@dataclass(slots=True)
class ApprovalNotification:
    """Lightweight representation of a notification for an approval decision."""

    booking_id: int
    requester_id: int
    approver_id: int
    decision: ApprovalDecision
    message: str
    reason: Optional[str]
    decided_at: datetime


@dataclass(slots=True)
class PendingApprovalNotification:
    """Summary of booking requests awaiting managerial approval."""

    booking_id: int
    requester_id: int
    requester_name: str
    department: Optional[str]
    purpose: str
    submitted_at: datetime
    start_datetime: datetime
    end_datetime: datetime
    hours_pending: int


@dataclass(slots=True)
class BookingApprovalResult:
    """Outcome of recording an approval decision."""

    booking: BookingRequest
    approval: Approval
    notification: ApprovalNotification


_MANAGEMENT_ROLES: frozenset[UserRole] = frozenset(
    {UserRole.MANAGER, UserRole.FLEET_ADMIN}
)

_MAX_REASON_LENGTH = 500


def _normalise_reason(reason: Optional[str]) -> Optional[str]:
    if reason is None:
        return None

    trimmed = " ".join(reason.split())
    if not trimmed:
        return None

    if len(trimmed) > _MAX_REASON_LENGTH:
        msg = f"Reason must be at most {_MAX_REASON_LENGTH} characters"
        raise ValueError(msg)

    return trimmed


def _ensure_role_allowed(user: User) -> None:
    if user.role not in _MANAGEMENT_ROLES:
        msg = "Only management users can record approval decisions"
        raise ValueError(msg)


def _ensure_can_review(booking_request: BookingRequest, approver: User) -> None:
    if booking_request.status != BookingStatus.REQUESTED:
        msg = "Only booking requests awaiting approval can be reviewed"
        raise ValueError(msg)

    if booking_request.requester_id == approver.id:
        msg = "Users cannot approve or reject their own booking requests"
        raise ValueError(msg)


async def record_booking_approval(
    session: AsyncSession,
    *,
    booking_request: BookingRequest,
    approver: User,
    decision: ApprovalDecision,
    reason: Optional[str] = None,
) -> BookingApprovalResult:
    """Record the approval *decision* and update the booking workflow state."""

    _ensure_role_allowed(approver)
    _ensure_can_review(booking_request, approver)

    normalised_reason = _normalise_reason(reason)

    approval = Approval(
        booking_request=booking_request,
        approver=approver,
        approval_level=1,
        decision=decision,
        reason=normalised_reason,
    )
    session.add(approval)

    target_status = (
        BookingStatus.APPROVED
        if decision == ApprovalDecision.APPROVED
        else BookingStatus.REJECTED
    )

    updated_booking = await transition_booking_status(
        session, booking_request=booking_request, new_status=target_status
    )

    await session.refresh(approval)

    decided_at = approval.decided_at or datetime.now(timezone.utc)
    verb = "approved" if decision == ApprovalDecision.APPROVED else "rejected"
    message = (
        f"Booking request #{updated_booking.id} {verb} by {approver.full_name}"
    )
    if normalised_reason:
        message = f"{message}: {normalised_reason}"

    notification = ApprovalNotification(
        booking_id=updated_booking.id,
        requester_id=updated_booking.requester_id,
        approver_id=approver.id,
        decision=decision,
        message=message,
        reason=normalised_reason,
        decided_at=decided_at,
    )

    return BookingApprovalResult(
        booking=updated_booking, approval=approval, notification=notification
    )


async def list_booking_approvals(
    session: AsyncSession, *, booking_request_id: int
) -> list[Approval]:
    """Return approval decisions recorded against the supplied booking."""

    stmt: Select[tuple[Approval]] = (
        select(Approval)
        .where(Approval.booking_request_id == booking_request_id)
        .order_by(Approval.decided_at, Approval.id)
    )
    result = await session.execute(stmt)
    return list(result.scalars().all())


def _ensure_aware(value: datetime) -> datetime:
    if value.tzinfo is not None:
        return value
    return value.replace(tzinfo=timezone.utc)


async def get_pending_booking_approval_notifications(
    session: AsyncSession, *, pending_for_hours: Optional[int] = None
) -> list[PendingApprovalNotification]:
    """Return booking requests awaiting approval, optionally filtered by age."""

    if pending_for_hours is not None and pending_for_hours < 0:
        raise ValueError("pending_for_hours must be greater than or equal to zero")

    stmt: Select[tuple[BookingRequest, User]] = (
        select(BookingRequest, User)
        .join(User, BookingRequest.requester_id == User.id)
        .where(BookingRequest.status == BookingStatus.REQUESTED)
        .order_by(BookingRequest.submitted_at, BookingRequest.id)
    )

    result = await session.execute(stmt)
    rows = result.all()

    now = datetime.now(timezone.utc)
    notifications: list[PendingApprovalNotification] = []

    for booking, requester in rows:
        submitted = booking.submitted_at or booking.created_at
        if submitted is None:
            # Fallback to current time if timestamps are unexpectedly missing.
            submitted = now

        submitted_aware = _ensure_aware(submitted)
        hours_pending = max(
            0, int((now - submitted_aware).total_seconds() // 3600)
        )

        if pending_for_hours is not None and hours_pending < pending_for_hours:
            continue

        notifications.append(
            PendingApprovalNotification(
                booking_id=booking.id,
                requester_id=booking.requester_id,
                requester_name=requester.full_name,
                department=booking.department,
                purpose=booking.purpose,
                submitted_at=submitted,
                start_datetime=booking.start_datetime,
                end_datetime=booking.end_datetime,
                hours_pending=hours_pending,
            )
        )

    notifications.sort(
        key=lambda item: (
            _ensure_aware(item.submitted_at),
            item.booking_id,
        )
    )

    return notifications


__all__ = [
    "ApprovalNotification",
    "PendingApprovalNotification",
    "BookingApprovalResult",
    "record_booking_approval",
    "list_booking_approvals",
    "get_pending_booking_approval_notifications",
]

