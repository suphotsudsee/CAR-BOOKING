from __future__ import annotations

import io

import pytest
from starlette.datastructures import UploadFile

from app.services.expense import (
    ReceiptValidationError,
    handle_expense_receipt_upload,
)
from app.services.storage import S3StorageService
from tests.s3_stub import InMemoryS3Client


@pytest.mark.asyncio
async def test_handle_expense_receipt_upload_stores_file() -> None:
    client = InMemoryS3Client()
    storage = S3StorageService(
        client=client,
        bucket="receipts",
        base_prefix="uploads",
        default_expiration=120,
    )

    upload = UploadFile(
        filename="receipt.jpg",
        file=io.BytesIO(b"fake-image-bytes"),
        headers={"content-type": "image/jpeg"},
    )

    stored = await handle_expense_receipt_upload(
        storage,
        upload,
        max_size=1024 * 1024,
        allowed_extensions=["jpg", "jpeg", "pdf"],
        expires_in=90,
    )

    assert stored.key.startswith("uploads/expense-receipts/")
    assert stored.content_type == "image/jpeg"
    assert stored.size == len(b"fake-image-bytes")
    assert stored.expires_in == 90


@pytest.mark.asyncio
async def test_handle_expense_receipt_upload_rejects_extension() -> None:
    client = InMemoryS3Client()
    storage = S3StorageService(
        client=client,
        bucket="receipts",
        base_prefix="uploads",
        default_expiration=120,
    )

    upload = UploadFile(
        filename="receipt.exe",
        file=io.BytesIO(b"malware"),
        headers={"content-type": "application/octet-stream"},
    )

    with pytest.raises(ReceiptValidationError):
        await handle_expense_receipt_upload(
            storage,
            upload,
            max_size=1024 * 1024,
            allowed_extensions=["jpg", "jpeg", "pdf"],
            expires_in=90,
        )


@pytest.mark.asyncio
async def test_handle_expense_receipt_upload_rejects_large_file() -> None:
    client = InMemoryS3Client()
    storage = S3StorageService(
        client=client,
        bucket="receipts",
        base_prefix="uploads",
        default_expiration=120,
    )

    upload = UploadFile(
        filename="receipt.pdf",
        file=io.BytesIO(b"x" * (2 * 1024 * 1024)),
        headers={"content-type": "application/pdf"},
    )

    with pytest.raises(ReceiptValidationError):
        await handle_expense_receipt_upload(
            storage,
            upload,
            max_size=1024 * 1024,
            allowed_extensions=["jpg", "jpeg", "pdf"],
            expires_in=90,
        )
