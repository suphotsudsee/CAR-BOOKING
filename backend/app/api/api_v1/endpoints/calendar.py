"""Calendar endpoints for resource scheduling."""

from __future__ import annotations

import asyncio
from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import HTMLResponse, PlainTextResponse, Response, StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import RoleBasedAccess
from app.db import get_async_session
from app.models import CalendarResourceType
from app.models.user import User, UserRole
from app.schemas import (
    CalendarEventCreate,
    CalendarEventRead,
    CalendarEventUpdate,
    CalendarResourceView,
)
from app.services import (
    build_resource_calendar_view,
    create_calendar_event,
    delete_calendar_event,
    export_calendar_to_ical,
    generate_calendar_pdf,
    generate_calendar_print_view,
    get_calendar_event_by_id,
    subscribe_to_calendar_updates,
    unsubscribe_from_calendar_updates,
    update_calendar_event,
)

router = APIRouter()

_MANAGEMENT_ROLES = (UserRole.MANAGER, UserRole.FLEET_ADMIN)
_manage_calendar = RoleBasedAccess(_MANAGEMENT_ROLES)


@router.get("/stream")
async def stream_calendar_updates(_: User = Depends(_manage_calendar)) -> StreamingResponse:
    """Stream realtime calendar updates for manual events."""

    async def event_stream():
        queue = await subscribe_to_calendar_updates()
        try:
            while True:
                event = await queue.get()
                yield f"data: {event.model_dump_json()}\n\n"
        except asyncio.CancelledError:
            raise
        finally:
            await unsubscribe_from_calendar_updates(queue)

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@router.get("/{resource_type}", response_model=list[CalendarResourceView])
async def get_resource_calendar(
    resource_type: CalendarResourceType,
    start: datetime = Query(..., description="Start of the calendar window"),
    end: datetime = Query(..., description="End of the calendar window"),
    resource_ids: Annotated[
        list[int] | None, Query(description="Filter by resource ids")
    ] = None,
    session: AsyncSession = Depends(get_async_session),
    _: User = Depends(_manage_calendar),
) -> list[CalendarResourceView]:
    """Return calendar entries grouped by resource."""

    try:
        return await build_resource_calendar_view(
            session,
            resource_type=resource_type,
            start=start,
            end=end,
            resource_ids=resource_ids,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc


@router.get("/{resource_type}/export/ical")
async def export_resource_calendar_ical(
    resource_type: CalendarResourceType,
    start: datetime = Query(..., description="Start of the calendar window"),
    end: datetime = Query(..., description="End of the calendar window"),
    resource_ids: Annotated[
        list[int] | None, Query(description="Filter by resource ids")
    ] = None,
    session: AsyncSession = Depends(get_async_session),
    _: User = Depends(_manage_calendar),
) -> PlainTextResponse:
    """Export the calendar window as an iCalendar feed."""

    try:
        content = await export_calendar_to_ical(
            session,
            resource_type=resource_type,
            start=start,
            end=end,
            resource_ids=resource_ids,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    filename = f"{resource_type.value}-calendar.ics"
    headers = {"Content-Disposition": f"attachment; filename=\"{filename}\""}
    return PlainTextResponse(
        content=content,
        media_type="text/calendar",
        headers=headers,
    )


@router.get("/{resource_type}/export/print", response_class=HTMLResponse)
async def export_resource_calendar_print(
    resource_type: CalendarResourceType,
    start: datetime = Query(..., description="Start of the calendar window"),
    end: datetime = Query(..., description="End of the calendar window"),
    resource_ids: Annotated[
        list[int] | None, Query(description="Filter by resource ids")
    ] = None,
    session: AsyncSession = Depends(get_async_session),
    _: User = Depends(_manage_calendar),
) -> HTMLResponse:
    """Return a printer-friendly HTML schedule."""

    try:
        html = await generate_calendar_print_view(
            session,
            resource_type=resource_type,
            start=start,
            end=end,
            resource_ids=resource_ids,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    return HTMLResponse(content=html)


@router.get("/{resource_type}/export/pdf")
async def export_resource_calendar_pdf(
    resource_type: CalendarResourceType,
    start: datetime = Query(..., description="Start of the calendar window"),
    end: datetime = Query(..., description="End of the calendar window"),
    resource_ids: Annotated[
        list[int] | None, Query(description="Filter by resource ids")
    ] = None,
    session: AsyncSession = Depends(get_async_session),
    _: User = Depends(_manage_calendar),
) -> Response:
    """Download the calendar view as a PDF document."""

    try:
        pdf_bytes = await generate_calendar_pdf(
            session,
            resource_type=resource_type,
            start=start,
            end=end,
            resource_ids=resource_ids,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    filename = f"{resource_type.value}-calendar.pdf"
    headers = {"Content-Disposition": f"attachment; filename=\"{filename}\""}
    return Response(content=pdf_bytes, media_type="application/pdf", headers=headers)


@router.post("/events", response_model=CalendarEventRead, status_code=status.HTTP_201_CREATED)
async def create_calendar_entry(
    event_in: CalendarEventCreate,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(_manage_calendar),
) -> CalendarEventRead:
    """Create a manual calendar event for a resource."""

    try:
        return await create_calendar_event(
            session, event_in, created_by_id=current_user.id
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc


@router.get("/events/{event_id}", response_model=CalendarEventRead)
async def get_calendar_event(
    event_id: int,
    session: AsyncSession = Depends(get_async_session),
    _: User = Depends(_manage_calendar),
) -> CalendarEventRead:
    """Return the calendar event identified by *event_id*."""

    event = await get_calendar_event_by_id(session, event_id)
    if event is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Calendar event not found",
        )
    return event


@router.patch("/events/{event_id}", response_model=CalendarEventRead)
async def update_calendar_entry(
    event_id: int,
    event_update: CalendarEventUpdate,
    session: AsyncSession = Depends(get_async_session),
    _: User = Depends(_manage_calendar),
) -> CalendarEventRead:
    """Update an existing manual calendar event."""

    event = await get_calendar_event_by_id(session, event_id)
    if event is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Calendar event not found",
        )

    try:
        return await update_calendar_event(session, event, event_update)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc


@router.delete(
    "/events/{event_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
)
async def delete_calendar_entry(
    event_id: int,
    session: AsyncSession = Depends(get_async_session),
    _: User = Depends(_manage_calendar),
) -> Response:
    """Delete a manual calendar event."""

    event = await get_calendar_event_by_id(session, event_id)
    if event is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Calendar event not found",
        )

    await delete_calendar_event(session, event)

    return Response(status_code=status.HTTP_204_NO_CONTENT)


__all__ = [
    "create_calendar_entry",
    "delete_calendar_entry",
    "export_resource_calendar_ical",
    "export_resource_calendar_pdf",
    "export_resource_calendar_print",
    "get_calendar_event",
    "get_resource_calendar",
    "stream_calendar_updates",
    "update_calendar_entry",
]
