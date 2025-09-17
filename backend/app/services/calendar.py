"""Service layer for resource calendar operations."""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime
from typing import Iterable, Optional, Sequence

from sqlalchemy import Select, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import (
    Assignment,
    BookingRequest,
    BookingStatus,
    CalendarEventType,
    CalendarResourceType,
    Driver,
    ResourceCalendarEvent,
    Vehicle,
)
from app.schemas import (
    CalendarConflictView,
    CalendarEventCreate,
    CalendarEventSource,
    CalendarEventUpdate,
    CalendarEventView,
    CalendarResourceView,
)

_RELEVANT_ASSIGNMENT_STATUSES: frozenset[BookingStatus] = frozenset(
    {
        BookingStatus.APPROVED,
        BookingStatus.ASSIGNED,
        BookingStatus.IN_PROGRESS,
        BookingStatus.COMPLETED,
    }
)


def _ensure_window(start: datetime, end: datetime) -> None:
    if start >= end:
        msg = "End datetime must be after the start datetime"
        raise ValueError(msg)


def _ensure_timezone(value: datetime, field_name: str) -> None:
    if value.tzinfo is None or value.tzinfo.utcoffset(value) is None:
        msg = f"{field_name} must be timezone-aware"
        raise ValueError(msg)


async def _ensure_resource_exists(
    session: AsyncSession, resource_type: CalendarResourceType, resource_id: int
) -> None:
    if resource_type == CalendarResourceType.VEHICLE:
        stmt: Select[tuple[int]] = select(Vehicle.id).where(Vehicle.id == resource_id)
    else:
        stmt = select(Driver.id).where(Driver.id == resource_id)

    result = await session.execute(stmt)
    if result.scalar_one_or_none() is None:
        msg = f"{resource_type.value.capitalize()} with id {resource_id} not found"
        raise ValueError(msg)


async def get_calendar_event_by_id(
    session: AsyncSession, event_id: int
) -> Optional[ResourceCalendarEvent]:
    """Return the manual calendar event identified by *event_id*, if any."""

    result = await session.execute(
        select(ResourceCalendarEvent).where(ResourceCalendarEvent.id == event_id)
    )
    return result.scalar_one_or_none()


async def create_calendar_event(
    session: AsyncSession,
    event_in: CalendarEventCreate,
    *,
    created_by_id: Optional[int] = None,
) -> ResourceCalendarEvent:
    """Create a new manual calendar event."""

    if event_in.event_type == CalendarEventType.BOOKING:
        raise ValueError("Manual calendar events cannot use the booking event type")

    _ensure_timezone(event_in.start, "start")
    _ensure_timezone(event_in.end, "end")
    await _ensure_resource_exists(session, event_in.resource_type, event_in.resource_id)

    event = ResourceCalendarEvent(
        resource_type=event_in.resource_type,
        resource_id=event_in.resource_id,
        title=event_in.title,
        description=event_in.description,
        start_datetime=event_in.start,
        end_datetime=event_in.end,
        event_type=event_in.event_type,
        created_by_id=created_by_id,
        booking_request_id=event_in.booking_request_id,
    )
    session.add(event)
    await session.commit()
    await session.refresh(event)
    return event


async def update_calendar_event(
    session: AsyncSession,
    event: ResourceCalendarEvent,
    event_update: CalendarEventUpdate,
) -> ResourceCalendarEvent:
    """Update *event* with the supplied data."""

    if event_update.event_type == CalendarEventType.BOOKING:
        raise ValueError("Manual calendar events cannot use the booking event type")

    update_data = event_update.model_dump(exclude_unset=True)

    start = update_data.get("start", event.start_datetime)
    end = update_data.get("end", event.end_datetime)
    _ensure_window(start, end)
    _ensure_timezone(start, "start")
    _ensure_timezone(end, "end")

    if "title" in update_data:
        event.title = update_data["title"]
    if "description" in update_data:
        event.description = update_data["description"]
    if "start" in update_data:
        event.start_datetime = update_data["start"]
    if "end" in update_data:
        event.end_datetime = update_data["end"]
    if "event_type" in update_data:
        event.event_type = update_data["event_type"]
    if "booking_request_id" in update_data:
        event.booking_request_id = update_data["booking_request_id"]

    await session.commit()
    await session.refresh(event)
    return event


async def delete_calendar_event(
    session: AsyncSession, event: ResourceCalendarEvent
) -> None:
    """Remove the supplied manual calendar event."""

    await session.delete(event)
    await session.commit()


async def list_calendar_events(
    session: AsyncSession,
    *,
    resource_type: CalendarResourceType,
    start: datetime,
    end: datetime,
    resource_ids: Optional[Sequence[int]] = None,
) -> list[ResourceCalendarEvent]:
    """Return manual events overlapping the supplied window."""

    _ensure_window(start, end)
    _ensure_timezone(start, "start")
    _ensure_timezone(end, "end")

    stmt = select(ResourceCalendarEvent).where(
        ResourceCalendarEvent.resource_type == resource_type,
        ResourceCalendarEvent.start_datetime < end,
        ResourceCalendarEvent.end_datetime > start,
    )
    if resource_ids:
        stmt = stmt.where(ResourceCalendarEvent.resource_id.in_(tuple(resource_ids)))

    stmt = stmt.order_by(ResourceCalendarEvent.start_datetime)
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def _load_resource_names(
    session: AsyncSession,
    resource_type: CalendarResourceType,
    resource_ids: Iterable[int],
) -> dict[int, str]:
    identifiers = tuple({rid for rid in resource_ids if rid})
    if not identifiers:
        return {}

    if resource_type == CalendarResourceType.VEHICLE:
        stmt = select(Vehicle.id, Vehicle.registration_number).where(
            Vehicle.id.in_(identifiers)
        )
    else:
        stmt = select(Driver.id, Driver.full_name).where(Driver.id.in_(identifiers))

    result = await session.execute(stmt)
    return {row[0]: row[1] for row in result.all()}


def _manual_event_to_view(event: ResourceCalendarEvent) -> CalendarEventView:
    return CalendarEventView(
        reference_id=f"manual:{event.id}",
        resource_type=event.resource_type,
        resource_id=event.resource_id,
        title=event.title,
        start=event.start_datetime,
        end=event.end_datetime,
        event_type=event.event_type,
        source=CalendarEventSource.MANUAL,
        description=event.description,
        booking_request_id=event.booking_request_id,
        calendar_event_id=event.id,
    )


async def _list_assignment_events(
    session: AsyncSession,
    *,
    resource_type: CalendarResourceType,
    start: datetime,
    end: datetime,
    resource_ids: Optional[Sequence[int]] = None,
) -> list[CalendarEventView]:
    stmt = (
        select(
            Assignment.id,
            Assignment.vehicle_id,
            Assignment.driver_id,
            BookingRequest.id,
            BookingRequest.purpose,
            BookingRequest.start_datetime,
            BookingRequest.end_datetime,
            BookingRequest.status,
        )
        .join(BookingRequest, Assignment.booking_request_id == BookingRequest.id)
        .where(BookingRequest.start_datetime < end)
        .where(BookingRequest.end_datetime > start)
        .where(BookingRequest.status.in_(_RELEVANT_ASSIGNMENT_STATUSES))
        .order_by(BookingRequest.start_datetime)
    )

    if resource_type == CalendarResourceType.VEHICLE:
        stmt = stmt.where(Assignment.vehicle_id.is_not(None))
        if resource_ids:
            stmt = stmt.where(Assignment.vehicle_id.in_(tuple(resource_ids)))
    else:
        stmt = stmt.where(Assignment.driver_id.is_not(None))
        if resource_ids:
            stmt = stmt.where(Assignment.driver_id.in_(tuple(resource_ids)))

    result = await session.execute(stmt)
    events: list[CalendarEventView] = []
    for (
        assignment_id,
        vehicle_id,
        driver_id,
        booking_id,
        purpose,
        start_dt,
        end_dt,
        status,
    ) in result.all():
        resource_id = (
            vehicle_id if resource_type == CalendarResourceType.VEHICLE else driver_id
        )
        if resource_id is None:
            continue

        events.append(
            CalendarEventView(
                reference_id=f"assignment:{assignment_id}",
                resource_type=resource_type,
                resource_id=resource_id,
                title=purpose,
                start=start_dt,
                end=end_dt,
                event_type=CalendarEventType.BOOKING,
                source=CalendarEventSource.ASSIGNMENT,
                booking_request_id=booking_id,
                booking_status=status,
                assignment_id=assignment_id,
            )
        )

    return events


def _build_conflicts(events: Sequence[CalendarEventView]) -> list[CalendarConflictView]:
    conflicts: dict[tuple[str, str], CalendarConflictView] = {}
    sorted_events = sorted(events, key=lambda item: item.start)

    for index, event in enumerate(sorted_events):
        for other in sorted_events[index + 1 :]:
            if other.start >= event.end:
                break
            overlap_start = max(event.start, other.start)
            overlap_end = min(event.end, other.end)
            if overlap_start >= overlap_end:
                continue
            refs = tuple(sorted((event.reference_id, other.reference_id)))
            conflicts[refs] = CalendarConflictView(
                start=overlap_start,
                end=overlap_end,
                event_reference_ids=list(refs),
            )

    return list(conflicts.values())


async def build_resource_calendar_view(
    session: AsyncSession,
    *,
    resource_type: CalendarResourceType,
    start: datetime,
    end: datetime,
    resource_ids: Optional[Sequence[int]] = None,
) -> list[CalendarResourceView]:
    """Return calendar entries grouped by resource."""

    _ensure_window(start, end)
    _ensure_timezone(start, "start")
    _ensure_timezone(end, "end")

    manual_events = await list_calendar_events(
        session,
        resource_type=resource_type,
        start=start,
        end=end,
        resource_ids=resource_ids,
    )
    assignment_events = await _list_assignment_events(
        session,
        resource_type=resource_type,
        start=start,
        end=end,
        resource_ids=resource_ids,
    )

    resource_pool: set[int] = set(resource_ids or [])
    resource_pool.update(event.resource_id for event in manual_events)
    resource_pool.update(event.resource_id for event in assignment_events)

    resource_names = await _load_resource_names(session, resource_type, resource_pool)
    if resource_ids:
        missing = [rid for rid in resource_ids if rid not in resource_names]
        if missing:
            missing_str = ", ".join(str(item) for item in missing)
            msg = f"Unknown {resource_type.value} ids: {missing_str}"
            raise ValueError(msg)

    for rid in resource_pool:
        resource_names.setdefault(
            rid, f"{resource_type.value.title()} #{rid}"
        )

    grouped_events: dict[int, list[CalendarEventView]] = defaultdict(list)
    for event in manual_events:
        grouped_events[event.resource_id].append(_manual_event_to_view(event))
    for event in assignment_events:
        grouped_events[event.resource_id].append(event)

    views: list[CalendarResourceView] = []
    for resource_id in sorted(resource_pool, key=lambda rid: resource_names.get(rid, "")):
        events = sorted(grouped_events.get(resource_id, []), key=lambda item: item.start)
        conflicts = _build_conflicts(events)
        views.append(
            CalendarResourceView(
                resource_type=resource_type,
                resource_id=resource_id,
                resource_name=resource_names.get(resource_id, str(resource_id)),
                events=events,
                conflicts=conflicts,
            )
        )

    return views


__all__ = [
    "build_resource_calendar_view",
    "create_calendar_event",
    "delete_calendar_event",
    "get_calendar_event_by_id",
    "list_calendar_events",
    "update_calendar_event",
]
