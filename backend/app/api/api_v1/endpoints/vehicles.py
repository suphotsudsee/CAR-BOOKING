"""Vehicle management API endpoints."""

from __future__ import annotations

from typing import Optional

from fastapi import (
    APIRouter,
    Depends,
    File,
    HTTPException,
    Query,
    Response,
    UploadFile,
    status,
)
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import RoleBasedAccess
from app.core.config import settings
from app.db import get_async_session
from app.models.user import User, UserRole
from app.models.vehicle import VehicleDocumentType, VehicleStatus, VehicleType
from app.schemas import (
    VehicleCreate,
    VehicleDocumentExpiryNotification,
    VehicleDocumentUploadResponse,
    VehicleRead,
    VehicleStatusUpdate,
    VehicleUpdate,
)
from app.services import (
    create_vehicle,
    delete_vehicle as delete_vehicle_service,
    get_expiring_vehicle_documents,
    get_vehicle_by_id,
    list_vehicles,
    store_vehicle_document,
    update_vehicle as update_vehicle_service,
    update_vehicle_status as update_vehicle_status_service,
)
from app.utils import build_static_file_url

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


@router.get("/document-expiry", response_model=list[VehicleDocumentExpiryNotification])
async def get_vehicle_document_expiry_notifications(
    within_days: int = Query(30, ge=0, le=365),
    session: AsyncSession = Depends(get_async_session),
    _: User = Depends(_manage_vehicles),
) -> list[VehicleDocumentExpiryNotification]:
    """Return notifications for vehicle documents expiring soon."""

    reminders = await get_expiring_vehicle_documents(session, within_days=within_days)
    return [
        VehicleDocumentExpiryNotification(
            vehicle_id=reminder.vehicle_id,
            registration_number=reminder.registration_number,
            document_type=reminder.document_type,
            expiry_date=reminder.expiry_date,
            days_until_expiry=reminder.days_until_expiry,
            document_path=reminder.document_path,
            document_url=build_static_file_url(reminder.document_path),
        )
        for reminder in reminders
    ]


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


@router.delete(
    "/{vehicle_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
)
async def delete_vehicle_endpoint(
    vehicle_id: int,
    session: AsyncSession = Depends(get_async_session),
    _: User = Depends(_manage_vehicles),
) -> Response:
    """Delete a vehicle from the fleet."""
    vehicle = await get_vehicle_by_id(session, vehicle_id)
    if vehicle is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vehicle not found")

    await delete_vehicle_service(session, vehicle=vehicle)

    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post(
    "/{vehicle_id}/documents/{document_type}",
    response_model=VehicleDocumentUploadResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_vehicle_document(
    vehicle_id: int,
    document_type: VehicleDocumentType,
    file: UploadFile = File(...),
    session: AsyncSession = Depends(get_async_session),
    _: User = Depends(_manage_vehicles),
) -> VehicleDocumentUploadResponse:
    """Upload and attach a document to a vehicle."""

    vehicle = await get_vehicle_by_id(session, vehicle_id)
    if vehicle is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vehicle not found")

    content = await file.read()
    try:
        document_path = await store_vehicle_document(
            session,
            vehicle=vehicle,
            document_type=document_type,
            filename=file.filename or "",
            content=content,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    return VehicleDocumentUploadResponse(
        vehicle_id=vehicle.id,
        document_type=document_type,
        document_path=document_path,
        document_url=build_static_file_url(document_path),
    )
