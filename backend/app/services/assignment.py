"""Service layer for booking resource assignments."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Iterable, Optional, Sequence

from sqlalchemy import Select, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.assignment import Assignment
from app.models.booking import BookingRequest, BookingStatus, VehiclePreference
from app.models.driver import Driver, DriverStatus
from app.models.user import User
from app.models.vehicle import Vehicle, VehicleStatus, VehicleType
from app.schemas.assignment import (
    AssignmentCreate,
    AssignmentDriverSuggestionData,
    AssignmentSuggestionData,
    AssignmentUpdate,
    AssignmentVehicleSuggestionData,
)
from app.services.driver import ensure_driver_available, get_driver_by_id
from app.services.vehicle import get_vehicle_by_id, is_vehicle_available


@dataclass(slots=True)
class _VehicleCandidate:
    vehicle: Vehicle
    suggestion: AssignmentVehicleSuggestionData
    score: int
    reasons: list[str]


@dataclass(slots=True)
class _DriverCandidate:
    driver: Driver
    suggestion: AssignmentDriverSuggestionData
    score: int
    reasons: list[str]


async def get_assignment_by_id(
    session: AsyncSession, assignment_id: int
) -> Optional[Assignment]:
    """Return the assignment identified by *assignment_id*, if any."""

    result = await session.execute(
        select(Assignment).where(Assignment.id == assignment_id)
    )
    return result.scalar_one_or_none()


async def get_assignment_by_booking_id(
    session: AsyncSession, booking_request_id: int
) -> Optional[Assignment]:
    """Return the assignment attached to the supplied booking request."""

    result = await session.execute(
        select(Assignment).where(Assignment.booking_request_id == booking_request_id)
    )
    return result.scalar_one_or_none()


def _matches_vehicle_preference(
    vehicle_type: VehicleType, preference: VehiclePreference
) -> bool:
    if preference == VehiclePreference.ANY:
        return True
    return vehicle_type.value == preference.value


async def _collect_vehicle_candidates(
    session: AsyncSession,
    *,
    booking_request: BookingRequest,
    limit: int,
    exclude_vehicle_ids: Iterable[int] = (),
    exclude_booking_id: Optional[int] = None,
) -> list[_VehicleCandidate]:
    stmt: Select[tuple[Vehicle]] = select(Vehicle).where(
        Vehicle.status == VehicleStatus.ACTIVE,
        Vehicle.seating_capacity >= booking_request.passenger_count,
    )

    excluded = frozenset(exclude_vehicle_ids)
    if excluded:
        stmt = stmt.where(Vehicle.id.notin_(tuple(excluded)))

    stmt = stmt.order_by(Vehicle.id)
    result = await session.execute(stmt)
    vehicles = result.scalars().all()

    candidates: list[_VehicleCandidate] = []
    preference = booking_request.vehicle_preference

    for vehicle in vehicles:
        available = await is_vehicle_available(
            session,
            vehicle=vehicle,
            start=booking_request.start_datetime,
            end=booking_request.end_datetime,
            exclude_booking_id=exclude_booking_id,
        )
        if not available:
            continue

        matches_preference = _matches_vehicle_preference(vehicle.vehicle_type, preference)
        spare_seats = max(vehicle.seating_capacity - booking_request.passenger_count, 0)

        reasons: list[str] = []
        if preference != VehiclePreference.ANY:
            if matches_preference:
                reasons.append("Matches preferred vehicle type")
            else:
                reasons.append("Vehicle type differs from preference")

        reasons.append(f"{spare_seats} spare seats")

        score = (0 if matches_preference else 1) * 1_000_000
        score += spare_seats * 1_000
        score += vehicle.id

        suggestion = AssignmentVehicleSuggestionData(
            id=vehicle.id,
            registration_number=vehicle.registration_number,
            vehicle_type=vehicle.vehicle_type,
            seating_capacity=vehicle.seating_capacity,
            matches_preference=matches_preference,
            spare_seats=spare_seats,
        )

        candidates.append(
            _VehicleCandidate(
                vehicle=vehicle,
                suggestion=suggestion,
                score=score,
                reasons=reasons,
            )
        )

    candidates.sort(key=lambda item: (item.score, item.suggestion.id))
    return candidates[:limit]


async def _collect_driver_candidates(
    session: AsyncSession,
    *,
    booking_request: BookingRequest,
    limit: int,
    exclude_driver_ids: Iterable[int] = (),
    exclude_booking_id: Optional[int] = None,
) -> list[_DriverCandidate]:
    stmt: Select[tuple[Driver]] = select(Driver).where(
        Driver.status == DriverStatus.ACTIVE
    )

    excluded = frozenset(exclude_driver_ids)
    if excluded:
        stmt = stmt.where(Driver.id.notin_(tuple(excluded)))

    stmt = stmt.order_by(Driver.id)
    result = await session.execute(stmt)
    drivers = result.scalars().all()

    candidates: list[_DriverCandidate] = []

    for driver in drivers:
        try:
            await ensure_driver_available(
                session,
                driver=driver,
                start=booking_request.start_datetime,
                end=booking_request.end_datetime,
                exclude_booking_id=exclude_booking_id,
            )
        except ValueError:
            continue

        reasons = ["Driver available for requested window"]
        if driver.availability_schedule:
            reasons.append("Within configured availability schedule")

        score = driver.id

        suggestion = AssignmentDriverSuggestionData(
            id=driver.id,
            full_name=driver.full_name,
            license_number=driver.license_number,
        )

        candidates.append(
            _DriverCandidate(
                driver=driver,
                suggestion=suggestion,
                score=score,
                reasons=reasons,
            )
        )

    candidates.sort(key=lambda item: (item.score, item.suggestion.id))
    return candidates[:limit]


async def suggest_assignment_options(
    session: AsyncSession,
    *,
    booking_request: BookingRequest,
    limit: int = 5,
    exclude_vehicle_ids: Iterable[int] = (),
    exclude_driver_ids: Iterable[int] = (),
) -> list[AssignmentSuggestionData]:
    """Return ranked combinations of available vehicles and drivers."""

    if limit <= 0:
        return []

    vehicle_candidates = await _collect_vehicle_candidates(
        session,
        booking_request=booking_request,
        limit=max(limit * 2, limit),
        exclude_vehicle_ids=exclude_vehicle_ids,
        exclude_booking_id=booking_request.id,
    )

    driver_candidates = await _collect_driver_candidates(
        session,
        booking_request=booking_request,
        limit=max(limit * 2, limit),
        exclude_driver_ids=exclude_driver_ids,
        exclude_booking_id=booking_request.id,
    )

    suggestions: list[AssignmentSuggestionData] = []

    for vehicle in vehicle_candidates:
        for driver in driver_candidates:
            combined_score = vehicle.score * 1_000_000 + driver.score
            reasons = [*vehicle.reasons, *driver.reasons]
            suggestions.append(
                AssignmentSuggestionData(
                    vehicle=vehicle.suggestion,
                    driver=driver.suggestion,
                    score=combined_score,
                    reasons=reasons,
                )
            )
            if len(suggestions) >= limit:
                break
        if len(suggestions) >= limit:
            break

    return suggestions


async def _load_booking_request(
    session: AsyncSession, booking_request_id: int
) -> Optional[BookingRequest]:
    result = await session.execute(
        select(BookingRequest).where(BookingRequest.id == booking_request_id)
    )
    return result.scalar_one_or_none()


def _ensure_vehicle_suitable(
    vehicle: Vehicle, booking_request: BookingRequest
) -> None:
    if vehicle.status != VehicleStatus.ACTIVE:
        raise ValueError("Vehicle is not available for assignment")

    if vehicle.seating_capacity < booking_request.passenger_count:
        raise ValueError("Vehicle does not meet the passenger capacity requirement")


async def _ensure_vehicle_available(
    session: AsyncSession,
    *,
    vehicle: Vehicle,
    booking_request: BookingRequest,
    exclude_booking_id: Optional[int],
) -> None:
    _ensure_vehicle_suitable(vehicle, booking_request)

    available = await is_vehicle_available(
        session,
        vehicle=vehicle,
        start=booking_request.start_datetime,
        end=booking_request.end_datetime,
        exclude_booking_id=exclude_booking_id,
    )

    if not available:
        raise ValueError("Vehicle is not available for the requested time window")


async def _resolve_resources(
    session: AsyncSession,
    *,
    booking_request: BookingRequest,
    requested_vehicle_id: Optional[int],
    requested_driver_id: Optional[int],
    auto_assign: bool,
    exclude_vehicle_ids: Sequence[int] = (),
    exclude_driver_ids: Sequence[int] = (),
) -> tuple[Vehicle, Driver]:
    vehicle: Optional[Vehicle] = None
    driver: Optional[Driver] = None

    if requested_vehicle_id is not None:
        vehicle = await get_vehicle_by_id(session, requested_vehicle_id)
        if vehicle is None:
            raise ValueError("Selected vehicle not found")

    if requested_driver_id is not None:
        driver = await get_driver_by_id(session, requested_driver_id)
        if driver is None:
            raise ValueError("Selected driver not found")

    if auto_assign:
        if vehicle is None:
            vehicle_candidates = await _collect_vehicle_candidates(
                session,
                booking_request=booking_request,
                limit=1,
                exclude_vehicle_ids=exclude_vehicle_ids,
                exclude_booking_id=booking_request.id,
            )
            if not vehicle_candidates:
                raise ValueError("No available vehicles match the requested window")
            vehicle = vehicle_candidates[0].vehicle

        if driver is None:
            driver_candidates = await _collect_driver_candidates(
                session,
                booking_request=booking_request,
                limit=1,
                exclude_driver_ids=exclude_driver_ids,
                exclude_booking_id=booking_request.id,
            )
            if not driver_candidates:
                raise ValueError("No available drivers match the requested window")
            driver = driver_candidates[0].driver
    else:
        if vehicle is None or driver is None:
            raise ValueError(
                "Manual assignment requires both a vehicle and driver to be provided"
            )

    assert vehicle is not None  # for the type-checker
    assert driver is not None

    await _ensure_vehicle_available(
        session,
        vehicle=vehicle,
        booking_request=booking_request,
        exclude_booking_id=booking_request.id,
    )

    await ensure_driver_available(
        session,
        driver=driver,
        start=booking_request.start_datetime,
        end=booking_request.end_datetime,
        exclude_booking_id=booking_request.id,
    )

    return vehicle, driver


async def create_assignment(
    session: AsyncSession,
    assignment_in: AssignmentCreate,
    *,
    assigned_by: User,
) -> Assignment:
    """Create a new assignment for the supplied booking request."""

    booking = await _load_booking_request(session, assignment_in.booking_request_id)
    if booking is None:
        raise ValueError("Booking request not found")

    if booking.status != BookingStatus.APPROVED:
        raise ValueError("Booking must be approved before resources can be assigned")

    existing = await get_assignment_by_booking_id(session, booking.id)
    if existing is not None:
        raise ValueError("Booking already has an assignment")

    vehicle, driver = await _resolve_resources(
        session,
        booking_request=booking,
        requested_vehicle_id=assignment_in.vehicle_id,
        requested_driver_id=assignment_in.driver_id,
        auto_assign=assignment_in.auto_assign,
    )

    booking.status = BookingStatus.ASSIGNED

    assignment = Assignment(
        booking_request_id=booking.id,
        vehicle_id=vehicle.id,
        driver_id=driver.id,
        assigned_by=assigned_by.id,
        notes=assignment_in.notes,
    )

    session.add(assignment)
    await session.commit()
    await session.refresh(assignment)
    await session.refresh(booking)
    return assignment


async def update_assignment(
    session: AsyncSession,
    *,
    assignment: Assignment,
    assignment_update: AssignmentUpdate,
    assigned_by: User,
) -> Assignment:
    """Reassign resources for an existing booking assignment."""

    booking = await _load_booking_request(session, assignment.booking_request_id)
    if booking is None:
        raise ValueError("Booking request not found")

    if booking.status not in {BookingStatus.APPROVED, BookingStatus.ASSIGNED}:
        raise ValueError("Booking must be approved before resources can be assigned")

    vehicle_id: Optional[int]
    if "vehicle_id" in assignment_update.model_fields_set:
        vehicle_id = assignment_update.vehicle_id
    else:
        vehicle_id = assignment.vehicle_id

    driver_id: Optional[int]
    if "driver_id" in assignment_update.model_fields_set:
        driver_id = assignment_update.driver_id
    else:
        driver_id = assignment.driver_id

    if not assignment_update.auto_assign and (
        vehicle_id is None or driver_id is None
    ):
        raise ValueError(
            "Manual assignment requires both vehicle_id and driver_id to be provided"
        )

    vehicle, driver = await _resolve_resources(
        session,
        booking_request=booking,
        requested_vehicle_id=vehicle_id,
        requested_driver_id=driver_id,
        auto_assign=assignment_update.auto_assign,
        exclude_vehicle_ids=(assignment.vehicle_id,),
        exclude_driver_ids=(assignment.driver_id,),
    )

    assignment.vehicle_id = vehicle.id
    assignment.driver_id = driver.id
    assignment.assigned_by = assigned_by.id
    assignment.assigned_at = datetime.now(timezone.utc)

    if "notes" in assignment_update.model_fields_set:
        assignment.notes = assignment_update.notes

    booking.status = BookingStatus.ASSIGNED

    await session.commit()
    await session.refresh(assignment)
    await session.refresh(booking)
    return assignment


__all__ = [
    "create_assignment",
    "get_assignment_by_booking_id",
    "get_assignment_by_id",
    "suggest_assignment_options",
    "update_assignment",
]
