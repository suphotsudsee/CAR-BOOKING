"""Calendar endpoints for resource scheduling."""

from __future__ import annotations

from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
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
    get_calendar_event_by_id,
    update_calendar_event,
)

router = APIRouter()

_MANAGEMENT_ROLES = (UserRole.MANAGER, UserRole.FLEET_ADMIN)
_manage_calendar = RoleBasedAccess(_MANAGEMENT_ROLES)


@router.get("/{resource_type}", response_model=list[CalendarResourceView])
async def get_resource_calendar(
    resource_type: CalendarResourceType,
    start: datetime = Query(..., description="Start of the calendar window"),
    end: datetime = Query(..., description="End of the calendar window"),
    resource_ids: Annotated[list[int] | None, Query(None, description="Filter by resource ids")]
    = None,
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


@router.delete("/events/{event_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_calendar_entry(
    event_id: int,
    session: AsyncSession = Depends(get_async_session),
    _: User = Depends(_manage_calendar),
) -> None:
    """Delete a manual calendar event."""

    event = await get_calendar_event_by_id(session, event_id)
    if event is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Calendar event not found",
        )

    await delete_calendar_event(session, event)


__all__ = [
    "create_calendar_entry",
    "delete_calendar_entry",
    "get_calendar_event",
    "get_resource_calendar",
    "update_calendar_entry",
]
