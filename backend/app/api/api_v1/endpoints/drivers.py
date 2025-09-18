"""Driver management API endpoints."""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import RoleBasedAccess
from app.core.config import settings
from app.db import get_async_session
from app.models.driver import DriverStatus
from app.models.user import User, UserRole
from app.schemas import (
    DriverAvailabilityUpdate,
    DriverCreate,
    DriverLicenseExpiryNotification,
    DriverRead,
    DriverStatusUpdate,
    DriverUpdate,
)
from app.services import (
    create_driver,
    delete_driver as delete_driver_service,
    get_driver_by_id,
    get_expiring_driver_licenses,
    list_drivers as list_drivers_service,
    update_driver as update_driver_service,
    update_driver_availability as update_driver_availability_service,
    update_driver_status as update_driver_status_service,
)

router = APIRouter()

_management_roles = (UserRole.FLEET_ADMIN, UserRole.MANAGER)
_manage_drivers = RoleBasedAccess(_management_roles)


@router.get("/", response_model=list[DriverRead])
async def list_drivers_endpoint(
    skip: int = Query(0, ge=0),
    limit: int = Query(
        default=settings.DEFAULT_PAGE_SIZE,
        ge=1,
        le=settings.MAX_PAGE_SIZE,
    ),
    status: Optional[DriverStatus] = None,
    search: Optional[str] = Query(default=None, min_length=1),
    session: AsyncSession = Depends(get_async_session),
    _: User = Depends(_manage_drivers),
) -> list[DriverRead]:
    """List drivers with optional filtering and pagination."""

    search_term = search.strip() if search else None
    return await list_drivers_service(
        session,
        skip=skip,
        limit=limit,
        status=status,
        search=search_term,
    )


@router.post("/", response_model=DriverRead, status_code=status.HTTP_201_CREATED)
async def create_driver_endpoint(
    driver_in: DriverCreate,
    session: AsyncSession = Depends(get_async_session),
    _: User = Depends(_manage_drivers),
) -> DriverRead:
    """Register a new driver profile."""

    try:
        return await create_driver(session, driver_in)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc


@router.get("/{driver_id}", response_model=DriverRead)
async def get_driver_detail(
    driver_id: int,
    session: AsyncSession = Depends(get_async_session),
    _: User = Depends(_manage_drivers),
) -> DriverRead:
    """Retrieve driver information by identifier."""

    driver = await get_driver_by_id(session, driver_id)
    if driver is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Driver not found")
    return driver


@router.patch("/{driver_id}", response_model=DriverRead)
async def update_driver_endpoint(
    driver_id: int,
    driver_update: DriverUpdate,
    session: AsyncSession = Depends(get_async_session),
    _: User = Depends(_manage_drivers),
) -> DriverRead:
    """Update driver profile information."""

    driver = await get_driver_by_id(session, driver_id)
    if driver is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Driver not found")

    try:
        return await update_driver_service(session, driver=driver, driver_update=driver_update)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc


@router.patch("/{driver_id}/status", response_model=DriverRead)
async def update_driver_status_endpoint(
    driver_id: int,
    status_update: DriverStatusUpdate,
    session: AsyncSession = Depends(get_async_session),
    _: User = Depends(_manage_drivers),
) -> DriverRead:
    """Update only the status field for a driver."""

    driver = await get_driver_by_id(session, driver_id)
    if driver is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Driver not found")

    return await update_driver_status_service(session, driver=driver, status_update=status_update)


@router.patch("/{driver_id}/availability", response_model=DriverRead)
async def update_driver_availability_endpoint(
    driver_id: int,
    availability_update: DriverAvailabilityUpdate,
    session: AsyncSession = Depends(get_async_session),
    _: User = Depends(_manage_drivers),
) -> DriverRead:
    """Replace the driver's availability schedule."""

    driver = await get_driver_by_id(session, driver_id)
    if driver is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Driver not found")

    return await update_driver_availability_service(
        session,
        driver=driver,
        availability_update=availability_update,
    )


@router.delete(
    "/{driver_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
)
async def delete_driver_endpoint(
    driver_id: int,
    session: AsyncSession = Depends(get_async_session),
    _: User = Depends(_manage_drivers),
) -> Response:
    """Delete a driver from the system."""

    driver = await get_driver_by_id(session, driver_id)
    if driver is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Driver not found")

    await delete_driver_service(session, driver=driver)

    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get(
    "/license-expiry",
    response_model=list[DriverLicenseExpiryNotification],
)
async def list_driver_license_expiry_notifications(
    within_days: int = Query(30, ge=0, le=365),
    session: AsyncSession = Depends(get_async_session),
    _: User = Depends(_manage_drivers),
) -> list[DriverLicenseExpiryNotification]:
    """List drivers whose licenses expire within the provided time window."""

    try:
        reminders = await get_expiring_driver_licenses(session, within_days=within_days)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    return [
        DriverLicenseExpiryNotification(
            driver_id=reminder.driver_id,
            employee_code=reminder.employee_code,
            full_name=reminder.full_name,
            license_number=reminder.license_number,
            license_expiry_date=reminder.license_expiry_date,
            days_until_expiry=reminder.days_until_expiry,
        )
        for reminder in reminders
    ]
