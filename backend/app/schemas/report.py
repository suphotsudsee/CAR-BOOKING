"""Pydantic models for reporting responses."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, Field

from app.models.vehicle import VehicleType
from app.schemas.expense import ExpenseAnalytics


class VehicleUtilisationReport(BaseModel):
    """Vehicle utilisation metrics for reporting."""

    vehicle_id: int
    registration_number: str
    vehicle_type: VehicleType
    total_trips: int = Field(ge=0)
    total_hours: float = Field(ge=0)
    active_days: int = Field(ge=0)
    average_trip_duration_hours: float = Field(ge=0)
    utilisation_rate: float = Field(ge=0, le=100)
    current_mileage: int = Field(ge=0)


class DepartmentUsageReport(BaseModel):
    """Monthly usage metrics grouped by department."""

    period: date
    department: str
    total_requests: int = Field(ge=0)
    completed_trips: int = Field(ge=0)
    total_passengers: int = Field(ge=0)
    total_hours: float = Field(ge=0)


class DriverPerformanceReport(BaseModel):
    """Driver workload and completion performance."""

    driver_id: int
    full_name: str
    assignments: int = Field(ge=0)
    completed_jobs: int = Field(ge=0)
    total_hours: float = Field(ge=0)
    average_completion_time_hours: float = Field(ge=0)
    workload_index: float = Field(ge=0, le=100)


class PredictiveMaintenanceReport(BaseModel):
    """Predictive maintenance recommendation for a vehicle."""

    vehicle_id: int
    registration_number: str
    vehicle_type: VehicleType
    risk_score: float = Field(ge=0, le=100)
    recommended_action: str
    projected_service_date: date


class BookingPatternReport(BaseModel):
    """Booking pattern insight grouped by day of week."""

    day_of_week: str
    weekday_index: int = Field(ge=0, le=6)
    average_bookings: float = Field(ge=0)
    peak_hour: int = Field(ge=0, le=23)
    average_passengers: float = Field(ge=0)


class CostOptimisationReport(BaseModel):
    """Cost optimisation recommendations."""

    label: str
    detail: str
    potential_saving: float = Field(ge=0)


class CustomReportDriverOption(BaseModel):
    """Driver option for the custom report builder."""

    id: int
    name: str


class CustomReportOptionsRead(BaseModel):
    """Available filter options for the custom report builder."""

    departments: list[str]
    vehicle_types: list[VehicleType]
    drivers: list[CustomReportDriverOption]


class CustomReportSummaryRead(BaseModel):
    """Summary payload for the custom report builder."""

    total_bookings: int = Field(ge=0)
    total_completed: int = Field(ge=0)
    total_expenses: float = Field(ge=0)
    average_booking_hours: float = Field(ge=0)
    filters: dict[str, Any]


class ReportOverviewResponse(BaseModel):
    """Comprehensive reporting response."""

    generated_at: datetime
    timeframe_start: datetime | None
    timeframe_end: datetime | None
    vehicle_utilisation: list[VehicleUtilisationReport]
    department_usage: list[DepartmentUsageReport]
    driver_performance: list[DriverPerformanceReport]
    expense_summary: ExpenseAnalytics
    predictive_maintenance: list[PredictiveMaintenanceReport]
    booking_patterns: list[BookingPatternReport]
    cost_recommendations: list[CostOptimisationReport]
    custom_report_summary: CustomReportSummaryRead
    custom_report_options: CustomReportOptionsRead


__all__ = [
    "BookingPatternReport",
    "CostOptimisationReport",
    "CustomReportDriverOption",
    "CustomReportOptionsRead",
    "CustomReportSummaryRead",
    "DepartmentUsageReport",
    "DriverPerformanceReport",
    "PredictiveMaintenanceReport",
    "ReportOverviewResponse",
    "VehicleUtilisationReport",
]
