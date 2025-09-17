"""Image processing and storage helpers for vehicle condition photos."""

from __future__ import annotations

import io
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional, Sequence

from fastapi import UploadFile
from PIL import Image, ImageOps, UnidentifiedImageError

from app.core.config import settings

from .storage import S3StorageService, StoredImage

try:  # Pillow >= 9
    _RESAMPLE = Image.Resampling.LANCZOS  # type: ignore[attr-defined]
except AttributeError:  # pragma: no cover - fallback for older Pillow versions
    _RESAMPLE = Image.LANCZOS


class ImageValidationError(ValueError):
    """Raised when an uploaded image fails validation or processing."""


@dataclass(slots=True)
class ProcessedVehicleImage:
    """In-memory representation of a processed vehicle image."""

    data: bytes
    content_type: str
    width: int
    height: int
    extension: str
    size: int
    preview_data: Optional[bytes]
    preview_content_type: Optional[str]
    preview_width: Optional[int]
    preview_height: Optional[int]
    preview_extension: Optional[str]
    original_filename: Optional[str]


async def process_vehicle_image_upload(
    upload: UploadFile,
    *,
    max_size: int,
    allowed_extensions: Sequence[str],
    max_dimension: int,
    preview_dimension: int,
) -> ProcessedVehicleImage:
    """Validate and prepare ``upload`` for storage."""

    filename = upload.filename or ""
    extension = Path(filename).suffix.lower().lstrip(".")
    if not extension:
        raise ImageValidationError("Filename must include an image extension")

    normalised_extensions = {ext.lower() for ext in allowed_extensions}
    if extension not in normalised_extensions:
        allowed = ", ".join(sorted(normalised_extensions))
        raise ImageValidationError(
            f"Unsupported image format '{extension}'. Allowed extensions: {allowed}"
        )

    raw_bytes = await upload.read()
    if len(raw_bytes) > max_size:
        raise ImageValidationError(
            f"Image exceeds maximum size of {max_size // (1024 * 1024)}MB"
        )

    if not raw_bytes:
        raise ImageValidationError("Uploaded image file is empty")

    try:
        image = Image.open(io.BytesIO(raw_bytes))
        image = ImageOps.exif_transpose(image)
    except (
        UnidentifiedImageError,
        OSError,
    ) as exc:  # pragma: no cover - pillow message
        raise ImageValidationError("Unable to read uploaded image") from exc

    image = image.convert("RGB")

    processed = image.copy()
    processed.thumbnail((max_dimension, max_dimension), _RESAMPLE)
    width, height = processed.size

    if width == 0 or height == 0:
        raise ImageValidationError("Processed image has invalid dimensions")

    buffer = io.BytesIO()
    processed.save(buffer, format="JPEG", quality=90, optimize=True)
    data = buffer.getvalue()

    preview_image = processed.copy()
    preview_image.thumbnail((preview_dimension, preview_dimension), _RESAMPLE)
    preview_width, preview_height = preview_image.size

    if preview_width == 0 or preview_height == 0:
        raise ImageValidationError("Preview image has invalid dimensions")

    preview_buffer = io.BytesIO()
    preview_image.save(preview_buffer, format="JPEG", quality=85, optimize=True)
    preview_data = preview_buffer.getvalue()

    return ProcessedVehicleImage(
        data=data,
        content_type="image/jpeg",
        width=width,
        height=height,
        extension="jpg",
        size=len(data),
        preview_data=preview_data,
        preview_content_type="image/jpeg",
        preview_width=preview_width,
        preview_height=preview_height,
        preview_extension="jpg",
        original_filename=filename or None,
    )


async def store_vehicle_image(
    processed: ProcessedVehicleImage,
    storage: S3StorageService,
    *,
    prefix: str,
    expires_in: Optional[int] = None,
) -> StoredImage:
    """Persist ``processed`` to storage and return its descriptor."""

    expires = expires_in or storage.default_expiration
    base_prefix = prefix.strip("/") or "vehicle-images"

    original_key = storage.build_object_key(
        prefix=base_prefix, extension=processed.extension
    )

    preview_key: Optional[str] = None
    if processed.preview_data:
        preview_key = storage.build_object_key(
            prefix=f"{base_prefix}/previews",
            extension=processed.preview_extension or processed.extension,
        )
        await storage.upload_file(
            key=preview_key,
            content=processed.preview_data,
            content_type=processed.preview_content_type or processed.content_type,
            metadata={
                "variant": "preview",
                "parent-key": original_key,
                "image-width": str(processed.preview_width or 0),
                "image-height": str(processed.preview_height or 0),
            },
            cache_control="max-age=604800, private",
        )

    metadata = {
        "variant": "original",
        "image-width": str(processed.width),
        "image-height": str(processed.height),
        "processed-at": datetime.utcnow().isoformat(timespec="seconds"),
    }

    if processed.original_filename:
        metadata["original-filename"] = processed.original_filename

    if preview_key:
        metadata["preview-key"] = preview_key
        if processed.preview_width:
            metadata["preview-width"] = str(processed.preview_width)
        if processed.preview_height:
            metadata["preview-height"] = str(processed.preview_height)

    await storage.upload_file(
        key=original_key,
        content=processed.data,
        content_type=processed.content_type,
        metadata=metadata,
        cache_control="max-age=31536000, private",
    )

    url = await storage.generate_presigned_url(original_key, expires_in=expires)
    preview_url = (
        await storage.generate_presigned_url(preview_key, expires_in=expires)
        if preview_key
        else None
    )

    return StoredImage(
        key=original_key,
        url=url,
        content_type=processed.content_type,
        width=processed.width,
        height=processed.height,
        size=processed.size,
        preview_key=preview_key,
        preview_url=preview_url,
        preview_width=processed.preview_width,
        preview_height=processed.preview_height,
        expires_in=expires,
        metadata=metadata,
    )


async def handle_vehicle_image_upload(
    storage: S3StorageService,
    upload: UploadFile,
    *,
    max_size: Optional[int] = None,
    allowed_extensions: Optional[Sequence[str]] = None,
    max_dimension: Optional[int] = None,
    preview_dimension: Optional[int] = None,
    expires_in: Optional[int] = None,
) -> StoredImage:
    """Process and store ``upload`` returning the persisted image descriptor."""

    allowed = allowed_extensions or ["jpg", "jpeg", "png"]
    processed = await process_vehicle_image_upload(
        upload,
        max_size=max_size or settings.MAX_FILE_SIZE,
        allowed_extensions=allowed,
        max_dimension=max_dimension or settings.IMAGE_MAX_DIMENSION,
        preview_dimension=preview_dimension or settings.IMAGE_PREVIEW_DIMENSION,
    )
    return await store_vehicle_image(
        processed,
        storage,
        prefix="vehicle-images",
        expires_in=expires_in or settings.S3_URL_EXPIRATION,
    )


__all__ = [
    "ImageValidationError",
    "ProcessedVehicleImage",
    "handle_vehicle_image_upload",
    "process_vehicle_image_upload",
    "store_vehicle_image",
]
