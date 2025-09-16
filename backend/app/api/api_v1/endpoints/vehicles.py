"""Vehicle management API endpoints."""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import RoleBasedAccess
from app.core.config import settings
from app.db import get_async_session
from app.models.user import User, UserRole
from app.models.vehicle import VehicleStatus, VehicleType
from app.schemas import VehicleCreate, VehicleRead, VehicleStatusUpdate, VehicleUpdate
from app.services import (
    create_vehicle,
    delete_vehicle as delete_vehicle_service,
    get_vehicle_by_id,
    list_vehicles,
    update_vehicle as update_vehicle_service,
    update_vehicle_status as update_vehicle_status_service,
)

router = APIRouter()

_management_roles = (UserRole.FLEET_ADMIN, UserRole.MANAGER)
_manage_vehicles = RoleBasedAccess(_management_roles)


@router.get("/", response_model=list[VehicleRead])
async def list_vehicles_endpoint(
    skip: int = Query(0, ge=0),
    limit: int = Query(
        default=settings.DEFAULT_PAGE_SIZE,
        ge=1,
        le=settings.MAX_PAGE_SIZE,
    ),
    status: Optional[VehicleStatus] = None,
    vehicle_type: Optional[VehicleType] = None,
    search: Optional[str] = Query(default=None, min_length=1),
    session: AsyncSession = Depends(get_async_session),
    _: User = Depends(_manage_vehicles),
) -> list[VehicleRead]:
    """List vehicles with optional filtering and pagination."""
    search_term = search.strip() if search else None
    return await list_vehicles(
        session,
        skip=skip,
        limit=limit,
        status=status,
        vehicle_type=vehicle_type,
        search=search_term,
    )


@router.post("/", response_model=VehicleRead, status_code=status.HTTP_201_CREATED)
async def create_vehicle_endpoint(
    vehicle_in: VehicleCreate,
    session: AsyncSession = Depends(get_async_session),
    _: User = Depends(_manage_vehicles),
) -> VehicleRead:
    """Create a new vehicle entry."""
    try:
        return await create_vehicle(session, vehicle_in)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc


@router.get("/{vehicle_id}", response_model=VehicleRead)
async def get_vehicle_detail(
    vehicle_id: int,
    session: AsyncSession = Depends(get_async_session),
    _: User = Depends(_manage_vehicles),
) -> VehicleRead:
    """Retrieve a vehicle by its identifier."""
    vehicle = await get_vehicle_by_id(session, vehicle_id)
    if vehicle is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vehicle not found")
    return vehicle


@router.patch("/{vehicle_id}", response_model=VehicleRead)
async def update_vehicle_endpoint(
    vehicle_id: int,
    vehicle_update: VehicleUpdate,
    session: AsyncSession = Depends(get_async_session),
    _: User = Depends(_manage_vehicles),
) -> VehicleRead:
    """Update vehicle information."""
    vehicle = await get_vehicle_by_id(session, vehicle_id)
    if vehicle is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vehicle not found")

    try:
        return await update_vehicle_service(
            session,
            vehicle=vehicle,
            vehicle_update=vehicle_update,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc


@router.patch("/{vehicle_id}/status", response_model=VehicleRead)
async def update_vehicle_status_endpoint(
    vehicle_id: int,
    status_update: VehicleStatusUpdate,
    session: AsyncSession = Depends(get_async_session),
    _: User = Depends(_manage_vehicles),
) -> VehicleRead:
    """Update only the status of a vehicle."""
    vehicle = await get_vehicle_by_id(session, vehicle_id)
    if vehicle is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vehicle not found")

    return await update_vehicle_status_service(
        session,
        vehicle=vehicle,
        status=status_update.status,
    )


@router.delete("/{vehicle_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_vehicle_endpoint(
    vehicle_id: int,
    session: AsyncSession = Depends(get_async_session),
    _: User = Depends(_manage_vehicles),
) -> None:
    """Delete a vehicle from the fleet."""
    vehicle = await get_vehicle_by_id(session, vehicle_id)
    if vehicle is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vehicle not found")

    await delete_vehicle_service(session, vehicle=vehicle)
