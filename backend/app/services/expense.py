"""Service helpers for expense uploads, validation, and analytics."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
from typing import Optional, Sequence

from fastapi import UploadFile
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.job_run import ExpenseStatus, JobRun
from app.services.storage import S3StorageService


class ReceiptValidationError(ValueError):
    """Raised when an uploaded expense receipt is invalid."""


@dataclass(slots=True)
class StoredReceipt:
    """Descriptor returned after uploading an expense receipt."""

    key: str
    url: str
    content_type: str
    size: int
    expires_in: int


@dataclass(slots=True)
class ExpenseStatusBreakdownEntry:
    """Aggregated totals for expenses per status."""

    status: ExpenseStatus
    count: int
    total_expenses: Decimal


@dataclass(slots=True)
class ExpenseAnalyticsResult:
    """Aggregated expense metrics."""

    generated_at: datetime
    total_jobs: int
    total_fuel_cost: Decimal
    total_toll_cost: Decimal
    total_other_expenses: Decimal
    total_expenses: Decimal
    average_fuel_cost: Decimal
    average_total_expense: Decimal
    status_breakdown: list[ExpenseStatusBreakdownEntry]


async def handle_expense_receipt_upload(
    storage: S3StorageService,
    upload: UploadFile,
    *,
    max_size: int,
    allowed_extensions: Sequence[str],
    expires_in: int,
    prefix: str = "expense-receipts",
) -> StoredReceipt:
    """Validate and persist an expense receipt file."""

    filename = upload.filename or ""
    extension = Path(filename).suffix.lower().lstrip(".")
    if not extension:
        raise ReceiptValidationError("Receipt filename must include an extension")

    normalised_extensions = {ext.lower() for ext in allowed_extensions}
    if extension not in normalised_extensions:
        allowed = ", ".join(sorted(normalised_extensions)) or "unknown"
        raise ReceiptValidationError(
            f"Unsupported receipt format '{extension}'. Allowed extensions: {allowed}"
        )

    raw_bytes = await upload.read()
    if not raw_bytes:
        raise ReceiptValidationError("Uploaded receipt is empty")

    if len(raw_bytes) > max_size:
        raise ReceiptValidationError(
            f"Receipt exceeds maximum size of {max_size // (1024 * 1024)}MB"
        )

    content_type = upload.content_type or "application/octet-stream"
    metadata = {
        "variant": "expense-receipt",
        "uploaded-at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }
    if filename:
        metadata["original-filename"] = filename

    key = storage.build_object_key(prefix=prefix, extension=extension)
    await storage.upload_file(
        key=key,
        content=raw_bytes,
        content_type=content_type,
        metadata=metadata,
        cache_control="max-age=31536000, private",
    )

    url = await storage.generate_presigned_url(key, expires_in=expires_in)
    return StoredReceipt(
        key=key,
        url=url,
        content_type=content_type,
        size=len(raw_bytes),
        expires_in=expires_in,
    )


def _to_decimal(value: Optional[Decimal]) -> Decimal:
    if value is None:
        return Decimal("0.00")
    if isinstance(value, Decimal):
        return value
    return Decimal(str(value))


async def generate_expense_analytics(
    session: AsyncSession,
    *,
    start: Optional[datetime] = None,
    end: Optional[datetime] = None,
    status: Optional[ExpenseStatus] = None,
) -> ExpenseAnalyticsResult:
    """Return aggregated analytics for recorded expenses."""

    filters = [JobRun.checkout_datetime.is_not(None)]
    if start is not None:
        filters.append(JobRun.checkout_datetime >= start)
    if end is not None:
        filters.append(JobRun.checkout_datetime <= end)
    if status is not None:
        filters.append(JobRun.expense_status == status)

    totals_stmt = (
        select(
            func.count(JobRun.id),
            func.coalesce(func.sum(JobRun.fuel_cost), 0),
            func.coalesce(func.sum(JobRun.toll_cost), 0),
            func.coalesce(func.sum(JobRun.other_expenses), 0),
        )
        .where(*filters)
    )

    totals_result = await session.execute(totals_stmt)
    total_jobs, fuel_sum, toll_sum, other_sum = totals_result.one()

    total_fuel = _to_decimal(fuel_sum)
    total_toll = _to_decimal(toll_sum)
    total_other = _to_decimal(other_sum)
    total_expenses = total_fuel + total_toll + total_other

    job_count = int(total_jobs)
    divisor = Decimal(job_count) if job_count else Decimal("1")
    average_fuel = (total_fuel / divisor) if job_count else Decimal("0.00")
    average_total = (total_expenses / divisor) if job_count else Decimal("0.00")

    breakdown_stmt = (
        select(
            JobRun.expense_status,
            func.count(JobRun.id),
            func.coalesce(
                func.sum(
                    JobRun.fuel_cost + JobRun.toll_cost + JobRun.other_expenses
                ),
                0,
            ),
        )
        .where(*filters)
        .group_by(JobRun.expense_status)
    )
    breakdown_result = await session.execute(breakdown_stmt)

    breakdown: list[ExpenseStatusBreakdownEntry] = []
    for status_value, count_value, expense_sum in breakdown_result:
        breakdown.append(
            ExpenseStatusBreakdownEntry(
                status=status_value,
                count=int(count_value),
                total_expenses=_to_decimal(expense_sum),
            )
        )

    return ExpenseAnalyticsResult(
        generated_at=datetime.now(timezone.utc),
        total_jobs=job_count,
        total_fuel_cost=total_fuel,
        total_toll_cost=total_toll,
        total_other_expenses=total_other,
        total_expenses=total_expenses,
        average_fuel_cost=average_fuel,
        average_total_expense=average_total,
        status_breakdown=breakdown,
    )


__all__ = [
    "ExpenseAnalyticsResult",
    "ExpenseStatusBreakdownEntry",
    "ReceiptValidationError",
    "StoredReceipt",
    "generate_expense_analytics",
    "handle_expense_receipt_upload",
]
