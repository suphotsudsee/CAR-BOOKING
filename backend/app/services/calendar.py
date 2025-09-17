"""Service layer for resource calendar operations."""

from __future__ import annotations

import asyncio
from collections import defaultdict
from datetime import datetime, timezone
from html import escape
from typing import AsyncIterator, Iterable, Optional, Sequence

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
    CalendarRealtimeAction,
    CalendarRealtimeEvent,
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

_CALENDAR_FETCH_BATCH = 500


class _CalendarUpdateBroadcaster:
    """Lightweight in-memory pub/sub for manual calendar events."""

    def __init__(self) -> None:
        self._subscribers: set[asyncio.Queue[CalendarRealtimeEvent]] = set()
        self._lock = asyncio.Lock()

    async def subscribe(self) -> asyncio.Queue[CalendarRealtimeEvent]:
        queue: asyncio.Queue[CalendarRealtimeEvent] = asyncio.Queue(maxsize=128)
        async with self._lock:
            self._subscribers.add(queue)
        return queue

    async def unsubscribe(self, queue: asyncio.Queue[CalendarRealtimeEvent]) -> None:
        async with self._lock:
            self._subscribers.discard(queue)

    async def publish(self, event: CalendarRealtimeEvent) -> None:
        async with self._lock:
            subscribers = tuple(self._subscribers)

        for queue in subscribers:
            try:
                queue.put_nowait(event)
            except asyncio.QueueFull:
                try:
                    _ = queue.get_nowait()
                except asyncio.QueueEmpty:
                    pass
                await queue.put(event)


_calendar_update_broadcaster = _CalendarUpdateBroadcaster()


async def subscribe_to_calendar_updates() -> asyncio.Queue[CalendarRealtimeEvent]:
    """Register a subscriber for manual calendar event updates."""

    return await _calendar_update_broadcaster.subscribe()


async def unsubscribe_from_calendar_updates(
    queue: asyncio.Queue[CalendarRealtimeEvent],
) -> None:
    """Remove a subscriber from the calendar update stream."""

    await _calendar_update_broadcaster.unsubscribe(queue)


async def publish_calendar_update(event: CalendarRealtimeEvent) -> None:
    """Broadcast *event* to all realtime subscribers."""

    await _calendar_update_broadcaster.publish(event)


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
    await publish_calendar_update(
        CalendarRealtimeEvent(
            action=CalendarRealtimeAction.CREATED,
            event=_manual_event_to_view(event),
            calendar_event_id=event.id,
        )
    )
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

    start_override = update_data.get("start")
    end_override = update_data.get("end")
    start = start_override or event.start_datetime
    end = end_override or event.end_datetime
    _ensure_window(start, end)
    if start_override is not None:
        _ensure_timezone(start_override, "start")
    if end_override is not None:
        _ensure_timezone(end_override, "end")

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
    await publish_calendar_update(
        CalendarRealtimeEvent(
            action=CalendarRealtimeAction.UPDATED,
            event=_manual_event_to_view(event),
            calendar_event_id=event.id,
        )
    )
    return event


async def delete_calendar_event(
    session: AsyncSession, event: ResourceCalendarEvent
) -> None:
    """Remove the supplied manual calendar event."""

    event_view = _manual_event_to_view(event)
    await session.delete(event)
    await session.commit()
    await publish_calendar_update(
        CalendarRealtimeEvent(
            action=CalendarRealtimeAction.DELETED,
            event=event_view,
            calendar_event_id=event.id,
        )
    )


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
    events: list[ResourceCalendarEvent] = []
    offset = 0
    while True:
        batch_stmt = stmt.limit(_CALENDAR_FETCH_BATCH).offset(offset)
        result = await session.execute(batch_stmt)
        batch = list(result.scalars().all())
        if not batch:
            break
        events.extend(batch)
        if len(batch) < _CALENDAR_FETCH_BATCH:
            break
        offset += _CALENDAR_FETCH_BATCH
    return events


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

    events: list[CalendarEventView] = []
    offset = 0
    while True:
        batch_stmt = stmt.limit(_CALENDAR_FETCH_BATCH).offset(offset)
        result = await session.execute(batch_stmt)
        rows = result.all()
        if not rows:
            break
        for (
            assignment_id,
            vehicle_id,
            driver_id,
            booking_id,
            purpose,
            start_dt,
            end_dt,
            status,
        ) in rows:
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

        if len(rows) < _CALENDAR_FETCH_BATCH:
            break
        offset += _CALENDAR_FETCH_BATCH

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


def _format_ics_datetime(value: datetime) -> str:
    return value.astimezone(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _escape_ics_text(value: str) -> str:
    escaped = value.replace("\\", "\\\\").replace(",", "\\,").replace(";", "\\;")
    return escaped.replace("\n", "\\n")


async def export_calendar_to_ical(
    session: AsyncSession,
    *,
    resource_type: CalendarResourceType,
    start: datetime,
    end: datetime,
    resource_ids: Optional[Sequence[int]] = None,
) -> str:
    """Generate an iCalendar feed for the requested window."""

    views = await build_resource_calendar_view(
        session,
        resource_type=resource_type,
        start=start,
        end=end,
        resource_ids=resource_ids,
    )
    timestamp = _format_ics_datetime(datetime.now(timezone.utc))
    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//Office Vehicle Booking//Calendar//EN",
        "CALSCALE:GREGORIAN",
    ]

    for resource in views:
        for event in resource.events:
            lines.append("BEGIN:VEVENT")
            lines.append(f"UID:{_escape_ics_text(event.reference_id)}@car-booking")
            lines.append(f"DTSTAMP:{timestamp}")
            lines.append(f"DTSTART:{_format_ics_datetime(event.start)}")
            lines.append(f"DTEND:{_format_ics_datetime(event.end)}")
            lines.append(f"SUMMARY:{_escape_ics_text(event.title)}")

            description_parts: list[str] = []
            description_parts.append(f"Resource: {resource.resource_name}")
            if event.description:
                description_parts.append(event.description)
            if event.booking_request_id:
                description_parts.append(
                    f"Booking reference #{event.booking_request_id}"
                )

            description = "\n".join(description_parts)
            lines.append(f"DESCRIPTION:{_escape_ics_text(description)}")
            lines.append(f"CATEGORIES:{event.event_type.value.upper()}")
            lines.append("END:VEVENT")

    lines.append("END:VCALENDAR")
    return "\r\n".join(lines) + "\r\n"


async def generate_calendar_print_view(
    session: AsyncSession,
    *,
    resource_type: CalendarResourceType,
    start: datetime,
    end: datetime,
    resource_ids: Optional[Sequence[int]] = None,
) -> str:
    """Build a printer-friendly HTML summary of the calendar."""

    views = await build_resource_calendar_view(
        session,
        resource_type=resource_type,
        start=start,
        end=end,
        resource_ids=resource_ids,
    )

    sections: list[str] = []
    for resource in views:
        sections.append('<section class="resource">')
        sections.append(f"<h2>{escape(resource.resource_name)}</h2>")
        if not resource.events:
            sections.append('<p class="empty">No scheduled events</p>')
        else:
            sections.append("<table>")
            sections.append(
                "<thead><tr><th>Start</th><th>End</th><th>Title</th><th>Details</th></tr></thead>"
            )
            sections.append("<tbody>")
            for event in resource.events:
                details: list[str] = []
                if event.description:
                    details.append(escape(event.description))
                if event.booking_request_id:
                    details.append(
                        f"Booking reference #{escape(str(event.booking_request_id))}"
                    )
                detail_html = "<br/>".join(details) if details else "-"
                sections.append(
                    "<tr>"
                    f"<td>{escape(event.start.isoformat())}</td>"
                    f"<td>{escape(event.end.isoformat())}</td>"
                    f"<td>{escape(event.title)}</td>"
                    f"<td>{detail_html}</td>"
                    "</tr>"
                )
            sections.append("</tbody></table>")
        sections.append("</section>")

    body = "".join(sections)
    return (
        "<!DOCTYPE html><html lang=\"en\"><head><meta charset=\"utf-8\"/>"
        "<title>Calendar Schedule</title>"
        "<style>body{font-family:Arial,sans-serif;padding:1.5rem;}"
        "h1{text-align:center;margin-bottom:1rem;}"
        "section.resource{margin-bottom:2rem;}"
        "table{width:100%;border-collapse:collapse;margin-top:0.75rem;}"
        "th,td{border:1px solid #ccc;padding:0.5rem;text-align:left;font-size:0.9rem;}"
        "thead{background:#f4f4f5;}"
        "p.empty{font-style:italic;color:#666;}"
        "</style></head><body>"
        "<h1>Calendar schedule</h1>"
        f"{body}" "</body></html>"
    )


async def generate_calendar_pdf(
    session: AsyncSession,
    *,
    resource_type: CalendarResourceType,
    start: datetime,
    end: datetime,
    resource_ids: Optional[Sequence[int]] = None,
) -> bytes:
    """Generate a PDF summary of the calendar."""

    views = await build_resource_calendar_view(
        session,
        resource_type=resource_type,
        start=start,
        end=end,
        resource_ids=resource_ids,
    )
    pages = _build_pdf_pages(views)
    return _render_pdf_document(pages)


def _pdf_escape_text(value: str) -> str:
    return value.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def _build_pdf_pages(views: list[CalendarResourceView]) -> list[list[str]]:
    pages: list[list[str]] = []
    current_lines: list[str] = []
    y_position = 760

    def start_new_page() -> None:
        nonlocal current_lines, y_position
        if current_lines:
            pages.append(current_lines)
        current_lines = []
        y_position = 760
        current_lines.append("BT /F1 18 Tf 72 760 Td (Calendar schedule) Tj ET")
        y_position = 736

    def ensure_space(minimum: int, *, repeat_heading: Optional[str] = None) -> None:
        nonlocal y_position
        if y_position < minimum:
            start_new_page()
            if repeat_heading:
                current_lines.append(
                    f"BT /F1 13 Tf 72 {y_position} Td ({_pdf_escape_text(repeat_heading)}) Tj ET"
                )
                y_position -= 18

    start_new_page()

    if not views:
        current_lines.append("BT /F1 11 Tf 72 712 Td (No scheduled events) Tj ET")
        pages.append(current_lines)
        return pages

    for resource in views:
        ensure_space(90)
        current_lines.append(
            f"BT /F1 13 Tf 72 {y_position} Td ({_pdf_escape_text(resource.resource_name)}) Tj ET"
        )
        y_position -= 18

        if not resource.events:
            ensure_space(80)
            current_lines.append(
                f"BT /F1 11 Tf 72 {y_position} Td (No scheduled events) Tj ET"
            )
            y_position -= 14
            continue

        for event in resource.events:
            summary = (
                f"{event.start.isoformat()} - {event.end.isoformat()} | {event.title}"
            )
            ensure_space(90, repeat_heading=resource.resource_name)
            current_lines.append(
                f"BT /F1 11 Tf 72 {y_position} Td ({_pdf_escape_text(summary)}) Tj ET"
            )
            y_position -= 14

            details: list[str] = []
            if event.description:
                details.append(event.description)
            if event.booking_request_id:
                details.append(f"Booking reference #{event.booking_request_id}")

            for detail in details:
                ensure_space(80, repeat_heading=resource.resource_name)
                current_lines.append(
                    f"BT /F1 10 Tf 90 {y_position} Td ({_pdf_escape_text(detail)}) Tj ET"
                )
                y_position -= 12

            y_position -= 4

    if current_lines:
        pages.append(current_lines)

    return pages


def _render_pdf_document(pages: list[list[str]]) -> bytes:
    bodies: list[str] = [
        "<< /Type /Catalog /Pages 2 0 R >>",
        "",  # Placeholder for pages object
        "<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
    ]
    page_ids: list[int] = []

    for page_lines in pages:
        stream_text = "\n".join(page_lines) + "\n"
        encoded = stream_text.encode("latin-1")
        content_body = (
            f"<< /Length {len(encoded)} >>\nstream\n{stream_text}endstream\n"
        )
        bodies.append(content_body)
        content_id = len(bodies)
        page_body = (
            "<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
            "/Resources << /Font << /F1 3 0 R >> >> "
            f"/Contents {content_id} 0 R >>"
        )
        bodies.append(page_body)
        page_ids.append(len(bodies))

    if not page_ids:
        # Ensure at least one empty page exists
        empty_stream = "BT /F1 18 Tf 72 760 Td (Calendar schedule) Tj ET\n"
        bodies.append(
            f"<< /Length {len(empty_stream)} >>\nstream\n{empty_stream}endstream\n"
        )
        content_id = len(bodies)
        bodies.append(
            "<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
            "/Resources << /Font << /F1 3 0 R >> >> "
            f"/Contents {content_id} 0 R >>"
        )
        page_ids.append(len(bodies))

    kids = " ".join(f"{pid} 0 R" for pid in page_ids)
    bodies[1] = f"<< /Type /Pages /Kids [{kids}] /Count {len(page_ids)} >>"

    buffer = bytearray()
    buffer.extend(b"%PDF-1.4\n")

    offsets: list[int] = []
    for index, body in enumerate(bodies, start=1):
        offsets.append(len(buffer))
        obj = f"{index} 0 obj\n{body}\nendobj\n"
        buffer.extend(obj.encode("latin-1"))

    xref_position = len(buffer)
    buffer.extend(f"xref\n0 {len(bodies) + 1}\n".encode("latin-1"))
    buffer.extend(b"0000000000 65535 f \n")
    for offset in offsets:
        buffer.extend(f"{offset:010d} 00000 n \n".encode("latin-1"))

    buffer.extend(
        (
            "trailer\n"
            f"<< /Size {len(bodies) + 1} /Root 1 0 R >>\n"
            f"startxref\n{xref_position}\n"
            "%%EOF\n"
        ).encode("latin-1")
    )

    return bytes(buffer)


__all__ = [
    "build_resource_calendar_view",
    "create_calendar_event",
    "delete_calendar_event",
    "get_calendar_event_by_id",
    "export_calendar_to_ical",
    "generate_calendar_pdf",
    "generate_calendar_print_view",
    "list_calendar_events",
    "publish_calendar_update",
    "subscribe_to_calendar_updates",
    "unsubscribe_from_calendar_updates",
    "update_calendar_event",
]
