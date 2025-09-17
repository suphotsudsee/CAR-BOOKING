"""API endpoints for booking assignments."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import RoleBasedAccess
from app.db import get_async_session
from app.models.user import User, UserRole
from app.schemas import (
    AssignmentCreate,
    AssignmentRead,
    AssignmentSuggestionRead,
    AssignmentUpdate,
)
from app.services import (
    create_assignment,
    get_assignment_by_booking_id,
    get_assignment_by_id,
    get_booking_request_by_id,
    suggest_assignment_options,
    update_assignment,
)

router = APIRouter()

_MANAGEMENT_ROLES = (UserRole.MANAGER, UserRole.FLEET_ADMIN)
_manage_assignments = RoleBasedAccess(_MANAGEMENT_ROLES)


@router.get("/{assignment_id}", response_model=AssignmentRead)
async def get_assignment_detail(
    assignment_id: int,
    session: AsyncSession = Depends(get_async_session),
    _: User = Depends(_manage_assignments),
) -> AssignmentRead:
    """Return the assignment identified by *assignment_id*."""

    assignment = await get_assignment_by_id(session, assignment_id)
    if assignment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assignment not found",
        )
    return assignment


@router.get("/by-booking/{booking_id}", response_model=AssignmentRead)
async def get_booking_assignment(
    booking_id: int,
    session: AsyncSession = Depends(get_async_session),
    _: User = Depends(_manage_assignments),
) -> AssignmentRead:
    """Return the assignment linked to the supplied booking, if any."""

    assignment = await get_assignment_by_booking_id(session, booking_id)
    if assignment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assignment not found",
        )
    return assignment


@router.get(
    "/by-booking/{booking_id}/suggestions",
    response_model=list[AssignmentSuggestionRead],
)
async def list_assignment_suggestions(
    booking_id: int,
    limit: int = Query(5, ge=1, le=20),
    session: AsyncSession = Depends(get_async_session),
    _: User = Depends(_manage_assignments),
) -> list[AssignmentSuggestionRead]:
    """Return suggested resource allocations for the given booking."""

    booking = await get_booking_request_by_id(session, booking_id)
    if booking is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Booking not found",
        )

    return await suggest_assignment_options(session, booking_request=booking, limit=limit)


@router.post("/", response_model=AssignmentRead, status_code=status.HTTP_201_CREATED)
async def create_booking_assignment(
    assignment_in: AssignmentCreate,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(_manage_assignments),
) -> AssignmentRead:
    """Create a new resource assignment for a booking."""

    try:
        return await create_assignment(session, assignment_in, assigned_by=current_user)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc


@router.patch("/{assignment_id}", response_model=AssignmentRead)
async def update_booking_assignment(
    assignment_id: int,
    assignment_update: AssignmentUpdate,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(_manage_assignments),
) -> AssignmentRead:
    """Reassign resources for an existing booking."""

    assignment = await get_assignment_by_id(session, assignment_id)
    if assignment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assignment not found",
        )

    try:
        return await update_assignment(
            session,
            assignment=assignment,
            assignment_update=assignment_update,
            assigned_by=current_user,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc


__all__ = [
    "create_booking_assignment",
    "get_assignment_detail",
    "get_booking_assignment",
    "list_assignment_suggestions",
    "update_booking_assignment",
]
