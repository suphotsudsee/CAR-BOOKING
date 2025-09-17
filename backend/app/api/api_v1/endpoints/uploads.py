"""Endpoints for media uploads and signed URL management."""

from __future__ import annotations

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status

from app.api.deps import RoleBasedAccess, get_current_user, get_storage_service
from app.core.config import settings
from app.models.user import User, UserRole
from app.schemas import SignedUrlResponse, VehicleImageUploadResponse
from app.services.image import ImageValidationError, handle_vehicle_image_upload
from app.services.storage import ObjectNotFoundError, S3StorageService

router = APIRouter()

_ALLOWED_UPLOAD_ROLES = (
    UserRole.MANAGER,
    UserRole.FLEET_ADMIN,
    UserRole.DRIVER,
    UserRole.AUDITOR,
)


@router.post(
    "/vehicle-images",
    response_model=VehicleImageUploadResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_vehicle_image(
    file: UploadFile = File(...),
    current_user: User = Depends(RoleBasedAccess(_ALLOWED_UPLOAD_ROLES)),
    storage: S3StorageService = Depends(get_storage_service),
) -> VehicleImageUploadResponse:
    """Validate, process, and persist a vehicle condition image."""

    allowed_extensions = [
        ext
        for ext in settings.ALLOWED_EXTENSIONS
        if ext.lower() in {"jpg", "jpeg", "png"}
    ]
    if not allowed_extensions:
        allowed_extensions = ["jpg", "jpeg", "png"]
    try:
        stored = await handle_vehicle_image_upload(
            storage,
            file,
            max_size=settings.MAX_FILE_SIZE,
            allowed_extensions=allowed_extensions,
            max_dimension=settings.IMAGE_MAX_DIMENSION,
            preview_dimension=settings.IMAGE_PREVIEW_DIMENSION,
            expires_in=settings.S3_URL_EXPIRATION,
        )
    except ImageValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)
        ) from exc

    if stored.width is None or stored.height is None or stored.size is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Stored image metadata is incomplete",
        )

    return VehicleImageUploadResponse(
        key=stored.key,
        url=stored.url,
        expires_in=stored.expires_in,
        content_type=stored.content_type,
        width=stored.width,
        height=stored.height,
        size=stored.size,
        preview_key=stored.preview_key,
        preview_url=stored.preview_url,
        preview_width=stored.preview_width,
        preview_height=stored.preview_height,
    )


@router.get(
    "/vehicle-images/{image_key:path}/signed-url",
    response_model=SignedUrlResponse,
)
async def get_vehicle_image_signed_url(
    image_key: str,
    current_user: User = Depends(get_current_user),
    storage: S3StorageService = Depends(get_storage_service),
) -> SignedUrlResponse:
    """Return a signed URL for accessing ``image_key``."""

    try:
        descriptor = await storage.describe_image(
            image_key, expires_in=settings.S3_URL_EXPIRATION
        )
    except ObjectNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Image not found"
        ) from exc

    return SignedUrlResponse(url=descriptor.url, expires_in=descriptor.expires_in)


__all__ = ["get_vehicle_image_signed_url", "upload_vehicle_image"]
