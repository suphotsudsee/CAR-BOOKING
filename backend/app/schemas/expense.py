"""Schemas related to expense tracking and analytics."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, field_validator

from app.models.job_run import ExpenseStatus


class ExpenseReviewDecision(str, Enum):
    """Possible reviewer decisions for job run expenses."""

    APPROVE = "APPROVE"
    REJECT = "REJECT"


class ExpenseReceiptUploadResponse(BaseModel):
    """Response returned after uploading an expense receipt."""

    key: str
    url: str
    expires_in: int
    content_type: str
    size: int


class JobRunExpenseReview(BaseModel):
    """Payload for approving or rejecting recorded job run expenses."""

    decision: ExpenseReviewDecision
    notes: Optional[str] = Field(default=None, max_length=1000)

    @field_validator("notes")
    @classmethod
    def _normalise_notes(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        trimmed = value.strip()
        return trimmed or None


class ExpenseStatusSummary(BaseModel):
    """Aggregated totals for a single expense status."""

    status: ExpenseStatus
    count: int
    total_expenses: Decimal


class ExpenseAnalytics(BaseModel):
    """Aggregated expense metrics across job runs."""

    generated_at: datetime
    total_jobs: int
    total_fuel_cost: Decimal
    total_toll_cost: Decimal
    total_other_expenses: Decimal
    total_expenses: Decimal
    average_fuel_cost: Decimal
    average_total_expense: Decimal
    status_breakdown: list[ExpenseStatusSummary]


__all__ = [
    "ExpenseAnalytics",
    "ExpenseReceiptUploadResponse",
    "ExpenseReviewDecision",
    "ExpenseStatusSummary",
    "JobRunExpenseReview",
]
