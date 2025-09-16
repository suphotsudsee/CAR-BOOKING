"""Service layer helpers for booking approval workflow management."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Optional, Sequence

from sqlalchemy import Select, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.approval import Approval, ApprovalDecision, ApprovalDelegation
from app.models.booking import BookingRequest, BookingStatus, VehiclePreference
from app.models.user import User, UserRole
from app.services.booking import transition_booking_status


class ApprovalStepType(str, Enum):
    """Enumeration describing available approval routing behaviours."""

    DEPARTMENT_MANAGER = "department_manager"
    PARENT_DEPARTMENT_MANAGER = "parent_department_manager"
    FLEET_ADMIN = "fleet_admin"


@dataclass(slots=True)
class ApprovalStep:
    """Represents a single level in the approval workflow."""

    level: int
    step_type: ApprovalStepType
    description: str
    department: Optional[str] = None


@dataclass(slots=True)
class ApprovalNotification:
    """Lightweight representation of a notification for an approval decision."""

    booking_id: int
    requester_id: int
    approver_id: int
    approval_level: int
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

_DEFAULT_TOP_DEPARTMENT = "executive"

_DEPARTMENT_HIERARCHY: dict[str, Optional[str]] = {
    "executive": None,
    "finance": _DEFAULT_TOP_DEPARTMENT,
    "operations": _DEFAULT_TOP_DEPARTMENT,
    "sales": "operations",
    "support": "operations",
    "logistics": "operations",
}

_PARENT_APPROVAL_PASSENGERS = 5
_PARENT_APPROVAL_DURATION_HOURS = 8

_FLEET_APPROVAL_PASSENGERS = 8
_FLEET_APPROVAL_DURATION_HOURS = 12
_FLEET_APPROVAL_VEHICLES = frozenset(
    {VehiclePreference.BUS, VehiclePreference.VAN}
)

_STEP_DESCRIPTIONS: dict[ApprovalStepType, str] = {
    ApprovalStepType.DEPARTMENT_MANAGER: "department manager",
    ApprovalStepType.PARENT_DEPARTMENT_MANAGER: "parent department manager",
    ApprovalStepType.FLEET_ADMIN: "fleet administrator",
}


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


def _normalise_department(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None

    trimmed = value.strip().lower()
    return trimmed or None


def _department_chain(department: Optional[str]) -> list[str]:
    chain: list[str] = []
    visited: set[str] = set()
    current = _normalise_department(department)

    if current is None:
        current = _DEFAULT_TOP_DEPARTMENT

    while current is not None and current not in visited:
        chain.append(current)
        visited.add(current)
        current = _DEPARTMENT_HIERARCHY.get(current)

    if _DEFAULT_TOP_DEPARTMENT not in visited:
        chain.append(_DEFAULT_TOP_DEPARTMENT)

    return chain


def _get_parent_department(department: Optional[str]) -> Optional[str]:
    normalised = _normalise_department(department)
    if normalised is None:
        return None
    return _DEPARTMENT_HIERARCHY.get(normalised)


def _trip_duration_hours(booking_request: BookingRequest) -> float:
    delta = booking_request.end_datetime - booking_request.start_datetime
    return max(delta.total_seconds() / 3600, 0)


def _requires_parent_approval(booking_request: BookingRequest) -> bool:
    return (
        booking_request.passenger_count >= _PARENT_APPROVAL_PASSENGERS
        or _trip_duration_hours(booking_request) >= _PARENT_APPROVAL_DURATION_HOURS
    )


def _requires_fleet_admin_approval(booking_request: BookingRequest) -> bool:
    return (
        booking_request.passenger_count >= _FLEET_APPROVAL_PASSENGERS
        or _trip_duration_hours(booking_request) >= _FLEET_APPROVAL_DURATION_HOURS
        or booking_request.vehicle_preference in _FLEET_APPROVAL_VEHICLES
    )


def _determine_approval_steps(booking_request: BookingRequest) -> list[ApprovalStep]:
    steps: list[ApprovalStep] = []

    department = _normalise_department(booking_request.department)
    steps.append(
        ApprovalStep(
            level=1,
            step_type=ApprovalStepType.DEPARTMENT_MANAGER,
            description=_STEP_DESCRIPTIONS[ApprovalStepType.DEPARTMENT_MANAGER],
            department=department,
        )
    )

    next_level = 2
    if _requires_parent_approval(booking_request):
        parent_department = _get_parent_department(booking_request.department)
        if parent_department is not None:
            steps.append(
                ApprovalStep(
                    level=next_level,
                    step_type=ApprovalStepType.PARENT_DEPARTMENT_MANAGER,
                    description=_STEP_DESCRIPTIONS[
                        ApprovalStepType.PARENT_DEPARTMENT_MANAGER
                    ],
                    department=parent_department,
                )
            )
            next_level += 1

    if _requires_fleet_admin_approval(booking_request):
        steps.append(
            ApprovalStep(
                level=next_level,
                step_type=ApprovalStepType.FLEET_ADMIN,
                description=_STEP_DESCRIPTIONS[ApprovalStepType.FLEET_ADMIN],
            )
        )

    return steps


async def _query_managers_for_department(
    session: AsyncSession, department: str
) -> list[User]:
    stmt: Select[tuple[User]] = (
        select(User)
        .where(User.role == UserRole.MANAGER)
        .where(User.is_active.is_(True))
    )

    if department:
        stmt = stmt.where(func.lower(User.department) == department)
    else:
        stmt = stmt.where(User.department.is_(None))

    stmt = stmt.order_by(User.id)
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def _find_users_by_role(
    session: AsyncSession, roles: Sequence[UserRole]
) -> list[User]:
    if not roles:
        return []

    stmt: Select[tuple[User]] = (
        select(User)
        .where(User.role.in_(tuple(roles)))
        .where(User.is_active.is_(True))
        .order_by(User.id)
    )
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def _resolve_department_managers(
    session: AsyncSession, starting_department: Optional[str]
) -> list[User]:
    for department in _department_chain(starting_department):
        managers = await _query_managers_for_department(session, department)
        if managers:
            return managers

    # Fallback to fleet administrators if no managers are available.
    return await _find_users_by_role(session, (UserRole.FLEET_ADMIN,))


async def _resolve_expected_approvers(
    session: AsyncSession, booking_request: BookingRequest, step: ApprovalStep
) -> list[User]:
    if step.step_type in {
        ApprovalStepType.DEPARTMENT_MANAGER,
        ApprovalStepType.PARENT_DEPARTMENT_MANAGER,
    }:
        return await _resolve_department_managers(session, step.department)

    if step.step_type == ApprovalStepType.FLEET_ADMIN:
        return await _find_users_by_role(session, (UserRole.FLEET_ADMIN,))

    return []


async def _resolve_delegation(
    session: AsyncSession,
    *,
    booking_request: BookingRequest,
    approver: User,
    expected_users: Sequence[User],
) -> Optional[User]:
    candidate_ids = tuple(user.id for user in expected_users)
    if not candidate_ids:
        return None

    now = datetime.now(timezone.utc)
    booking_department = _normalise_department(booking_request.department)

    stmt: Select[tuple[ApprovalDelegation]] = (
        select(ApprovalDelegation)
        .where(ApprovalDelegation.delegate_id == approver.id)
        .where(ApprovalDelegation.delegator_id.in_(candidate_ids))
        .where(ApprovalDelegation.is_active.is_(True))
        .where(ApprovalDelegation.start_datetime <= now)
        .where(
            or_(
                ApprovalDelegation.end_datetime.is_(None),
                ApprovalDelegation.end_datetime >= now,
            )
        )
    )

    if booking_department is not None:
        stmt = stmt.where(
            or_(
                ApprovalDelegation.department.is_(None),
                func.lower(ApprovalDelegation.department) == booking_department,
            )
        )

    result = await session.execute(stmt)
    delegation = result.scalars().first()
    if delegation is None:
        return None

    delegator = next(
        (user for user in expected_users if user.id == delegation.delegator_id),
        None,
    )
    if delegator is not None:
        return delegator

    delegator_result = await session.execute(
        select(User).where(User.id == delegation.delegator_id)
    )
    return delegator_result.scalar_one_or_none()


async def _ensure_authorised_for_step(
    session: AsyncSession,
    *,
    booking_request: BookingRequest,
    approver: User,
    step: ApprovalStep,
) -> tuple[Optional[User], list[User]]:
    expected_users = await _resolve_expected_approvers(session, booking_request, step)
    if not expected_users:
        raise ValueError("No eligible approvers available for this approval level")

    expected_ids = {user.id for user in expected_users}
    if approver.id in expected_ids:
        return None, expected_users

    delegator = await _resolve_delegation(
        session,
        booking_request=booking_request,
        approver=approver,
        expected_users=expected_users,
    )
    if delegator is not None:
        return delegator, expected_users

    raise ValueError("User is not authorised to approve at this level")


async def _fetch_existing_approvals(
    session: AsyncSession, booking_request_id: int
) -> list[Approval]:
    stmt: Select[tuple[Approval]] = (
        select(Approval)
        .where(Approval.booking_request_id == booking_request_id)
        .order_by(Approval.approval_level, Approval.decided_at, Approval.id)
    )
    result = await session.execute(stmt)
    return list(result.scalars().all())


def _determine_next_step(
    existing: Sequence[Approval], steps: Sequence[ApprovalStep]
) -> Optional[ApprovalStep]:
    approvals_by_level = {approval.approval_level: approval for approval in existing}

    for step in steps:
        approval = approvals_by_level.get(step.level)
        if approval is None:
            return step

        if approval.decision == ApprovalDecision.REJECTED:
            msg = (
                "Booking request has already been rejected at approval level "
                f"{step.level}"
            )
            raise ValueError(msg)

        if approval.decision != ApprovalDecision.APPROVED:
            raise ValueError("Invalid approval history for booking request")

    return None


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

    steps = _determine_approval_steps(booking_request)
    existing = await _fetch_existing_approvals(session, booking_request.id)

    next_step = _determine_next_step(existing, steps)
    if next_step is None:
        raise ValueError(
            "All approval levels have already been completed for this booking"
        )

    delegator, _ = await _ensure_authorised_for_step(
        session,
        booking_request=booking_request,
        approver=approver,
        step=next_step,
    )

    normalised_reason = _normalise_reason(reason)

    approval = Approval(
        booking_request=booking_request,
        approver=approver,
        approval_level=next_step.level,
        decision=decision,
        reason=normalised_reason,
        delegated_from=delegator,
    )
    session.add(approval)

    is_final_step = next_step.level == steps[-1].level

    if decision == ApprovalDecision.REJECTED:
        updated_booking = await transition_booking_status(
            session,
            booking_request=booking_request,
            new_status=BookingStatus.REJECTED,
        )
    elif decision == ApprovalDecision.APPROVED and is_final_step:
        updated_booking = await transition_booking_status(
            session,
            booking_request=booking_request,
            new_status=BookingStatus.APPROVED,
        )
    else:
        await session.commit()
        await session.refresh(booking_request)
        updated_booking = booking_request

    await session.refresh(approval)

    decided_at = approval.decided_at or datetime.now(timezone.utc)
    verb = "approved" if decision == ApprovalDecision.APPROVED else "rejected"
    step_description = _STEP_DESCRIPTIONS[next_step.step_type]

    message = (
        f"Booking request #{updated_booking.id} {verb} at level {next_step.level}"
        f" ({step_description}) by {approver.full_name}"
    )

    if delegator is not None:
        message = f"{message} (delegated from {delegator.full_name})"

    if decision == ApprovalDecision.APPROVED and not is_final_step:
        message = f"{message}. Next approval level pending."

    if normalised_reason:
        message = f"{message}: {normalised_reason}"

    notification = ApprovalNotification(
        booking_id=updated_booking.id,
        requester_id=updated_booking.requester_id,
        approver_id=approver.id,
        approval_level=next_step.level,
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
        .order_by(Approval.approval_level, Approval.decided_at, Approval.id)
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


async def create_approval_delegation(
    session: AsyncSession,
    *,
    delegator: User,
    delegate: User,
    start_datetime: Optional[datetime] = None,
    end_datetime: Optional[datetime] = None,
    department: Optional[str] = None,
    is_active: bool = True,
) -> ApprovalDelegation:
    """Create a delegation allowing *delegate* to approve on behalf of *delegator*."""

    if delegator.id == delegate.id:
        raise ValueError("Users cannot delegate approvals to themselves")

    if delegate.role not in _MANAGEMENT_ROLES:
        raise ValueError(
            "Delegated approver must have management permissions"
        )

    start = start_datetime or datetime.now(timezone.utc)
    if end_datetime is not None and end_datetime <= start:
        raise ValueError("Delegation end datetime must be after the start datetime")

    target_department = _normalise_department(department) or _normalise_department(
        delegator.department
    )

    delegation = ApprovalDelegation(
        delegator_id=delegator.id,
        delegate_id=delegate.id,
        department=target_department,
        start_datetime=start,
        end_datetime=end_datetime,
        is_active=is_active,
    )

    session.add(delegation)
    await session.commit()
    await session.refresh(delegation)
    return delegation


__all__ = [
    "ApprovalNotification",
    "PendingApprovalNotification",
    "BookingApprovalResult",
    "record_booking_approval",
    "list_booking_approvals",
    "get_pending_booking_approval_notifications",
    "create_approval_delegation",
]

