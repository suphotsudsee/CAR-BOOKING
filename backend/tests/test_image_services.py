from __future__ import annotations

import io

import pytest
from PIL import Image
from starlette.datastructures import UploadFile

from app.services.image import (
    ImageValidationError,
    handle_vehicle_image_upload,
    process_vehicle_image_upload,
    store_vehicle_image,
)
from app.services.storage import S3StorageService
from tests.s3_stub import InMemoryS3Client


def _make_upload(width: int = 1200, height: int = 900) -> UploadFile:
    image = Image.new("RGB", (width, height), color="red")
    buffer = io.BytesIO()
    image.save(buffer, format="JPEG")
    buffer.seek(0)
    return UploadFile(filename="vehicle.jpg", file=io.BytesIO(buffer.getvalue()))


@pytest.mark.asyncio
async def test_process_vehicle_image_upload_resizes_and_generates_preview() -> None:
    upload = _make_upload(width=3000, height=2000)

    processed = await process_vehicle_image_upload(
        upload,
        max_size=10 * 1024 * 1024,
        allowed_extensions=["jpg", "jpeg", "png"],
        max_dimension=1280,
        preview_dimension=320,
    )

    assert processed.width <= 1280
    assert processed.height <= 1280
    assert processed.preview_width is not None and processed.preview_width <= 320
    assert processed.preview_height is not None and processed.preview_height <= 320
    assert processed.content_type == "image/jpeg"
    assert processed.preview_data is not None and len(processed.preview_data) > 0


@pytest.mark.asyncio
async def test_process_vehicle_image_upload_rejects_extension() -> None:
    upload = UploadFile(filename="vehicle.gif", file=io.BytesIO(b"gifdata"))

    with pytest.raises(ImageValidationError):
        await process_vehicle_image_upload(
            upload,
            max_size=1024 * 1024,
            allowed_extensions=["jpg"],
            max_dimension=1024,
            preview_dimension=256,
        )


@pytest.mark.asyncio
async def test_store_vehicle_image_persists_and_returns_metadata() -> None:
    upload = _make_upload(width=1600, height=1200)
    processed = await process_vehicle_image_upload(
        upload,
        max_size=10 * 1024 * 1024,
        allowed_extensions=["jpg", "jpeg"],
        max_dimension=1440,
        preview_dimension=400,
    )

    client = InMemoryS3Client()
    storage = S3StorageService(
        client=client,
        bucket="test-bucket",
        base_prefix="uploads",
        default_expiration=300,
    )

    stored = await store_vehicle_image(
        processed,
        storage,
        prefix="vehicle-images",
        expires_in=120,
    )

    assert stored.key.startswith("uploads/vehicle-images/")
    assert stored.preview_key is not None
    assert stored.preview_url is not None
    assert stored.width == processed.width
    assert stored.preview_width == processed.preview_width

    head = client.head_object(Bucket="test-bucket", Key=stored.key)
    assert head["Metadata"]["preview-key"] == stored.preview_key

    described = await storage.describe_image(stored.key, expires_in=60)
    assert described.preview_key == stored.preview_key
    assert described.preview_url is not None


@pytest.mark.asyncio
async def test_handle_vehicle_image_upload_full_flow() -> None:
    upload = _make_upload(width=1024, height=768)

    client = InMemoryS3Client()
    storage = S3StorageService(
        client=client,
        bucket="test-bucket",
        base_prefix="uploads",
        default_expiration=900,
    )

    stored = await handle_vehicle_image_upload(
        storage,
        upload,
        max_size=5 * 1024 * 1024,
        allowed_extensions=["jpg", "jpeg"],
        max_dimension=1000,
        preview_dimension=300,
        expires_in=200,
    )

    assert stored.expires_in == 200
    assert stored.size is not None and stored.size > 0
    assert stored.preview_url is not None
