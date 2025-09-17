"""Schemas for image upload and gallery management."""

from __future__ import annotations

from typing import Optional

from pydantic import AnyUrl, BaseModel, ConfigDict, Field


class VehicleImageUploadResponse(BaseModel):
    """Response payload for a successfully uploaded vehicle image."""

    key: str = Field(..., description="Object storage key for the image")
    url: AnyUrl = Field(..., description="Presigned URL for accessing the image")
    expires_in: int = Field(..., ge=1, description="URL validity period in seconds")
    content_type: str = Field(..., description="MIME type of the stored image")
    width: int = Field(..., ge=1)
    height: int = Field(..., ge=1)
    size: int = Field(..., ge=1, description="Size of the processed image in bytes")
    preview_key: Optional[str] = Field(
        default=None, description="Object storage key for the preview variant"
    )
    preview_url: Optional[AnyUrl] = Field(
        default=None, description="Presigned URL for the preview image"
    )
    preview_width: Optional[int] = Field(default=None, ge=1)
    preview_height: Optional[int] = Field(default=None, ge=1)

    model_config = ConfigDict(extra="forbid")


class SignedUrlResponse(BaseModel):
    """Simple response wrapper for signed URL generation."""

    url: AnyUrl
    expires_in: int = Field(..., ge=1)

    model_config = ConfigDict(extra="forbid")


class GalleryImage(BaseModel):
    """Represents an image asset in a job run gallery."""

    key: str
    url: AnyUrl
    content_type: str
    width: Optional[int] = Field(default=None, ge=1)
    height: Optional[int] = Field(default=None, ge=1)
    preview_key: Optional[str] = None
    preview_url: Optional[AnyUrl] = None
    preview_width: Optional[int] = Field(default=None, ge=1)
    preview_height: Optional[int] = Field(default=None, ge=1)

    model_config = ConfigDict(extra="forbid")


class JobRunImageGallery(BaseModel):
    """Grouped check-in and check-out images for a job run."""

    checkin: list[GalleryImage] = Field(default_factory=list)
    checkout: list[GalleryImage] = Field(default_factory=list)

    model_config = ConfigDict(extra="forbid")


__all__ = [
    "GalleryImage",
    "JobRunImageGallery",
    "SignedUrlResponse",
    "VehicleImageUploadResponse",
]
