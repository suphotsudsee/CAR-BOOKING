"""Analytics and reporting API endpoints."""

from __future__ import annotations

from datetime import datetime
from typing import Optional, Sequence

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import RoleBasedAccess
from app.db import get_async_session
from app.models.user import User, UserRole
from app.models.vehicle import VehicleType
from app.schemas import (
    BookingPatternReport,
    CostOptimisationReport,
    CustomReportDriverOption,
    CustomReportOptionsRead,
    CustomReportSummaryRead,
    DepartmentUsageReport,
    DriverPerformanceReport,
    ExpenseAnalytics,
    ExpenseStatusSummary,
    PredictiveMaintenanceReport,
    ReportOverviewResponse,
    VehicleUtilisationReport,
)
from app.services.reports import (
    BookingPatternInsight,
    CostOptimisationRecommendation,
    CustomReportOptions,
    CustomReportSummary,
    DepartmentUsageEntry,
    DriverPerformanceEntry,
    PredictiveMaintenanceInsight,
    ReportOverview,
    VehicleUtilisationEntry,
    generate_report_overview,
)

router = APIRouter()

_REPORT_ROLES = (UserRole.MANAGER, UserRole.FLEET_ADMIN, UserRole.AUDITOR)
_require_reporting_access = RoleBasedAccess(_REPORT_ROLES)


def _map_vehicle_utilisation(entries: Sequence[VehicleUtilisationEntry]) -> list[VehicleUtilisationReport]:
    return [
        VehicleUtilisationReport(
            vehicle_id=item.vehicle_id,
            registration_number=item.registration_number,
            vehicle_type=item.vehicle_type,
            total_trips=item.total_trips,
            total_hours=item.total_hours,
            active_days=item.active_days,
            average_trip_duration_hours=item.average_trip_duration_hours,
            utilisation_rate=item.utilisation_rate,
            current_mileage=item.current_mileage,
        )
        for item in entries
    ]


def _map_department_usage(entries: Sequence[DepartmentUsageEntry]) -> list[DepartmentUsageReport]:
    return [
        DepartmentUsageReport(
            period=item.period,
            department=item.department,
            total_requests=item.total_requests,
            completed_trips=item.completed_trips,
            total_passengers=item.total_passengers,
            total_hours=item.total_hours,
        )
        for item in entries
    ]


def _map_driver_performance(entries: Sequence[DriverPerformanceEntry]) -> list[DriverPerformanceReport]:
    return [
        DriverPerformanceReport(
            driver_id=item.driver_id,
            full_name=item.full_name,
            assignments=item.assignments,
            completed_jobs=item.completed_jobs,
            total_hours=item.total_hours,
            average_completion_time_hours=item.average_completion_time_hours,
            workload_index=item.workload_index,
        )
        for item in entries
    ]


def _map_booking_patterns(entries: Sequence[BookingPatternInsight]) -> list[BookingPatternReport]:
    return [
        BookingPatternReport(
            day_of_week=item.day_of_week,
            weekday_index=item.weekday_index,
            average_bookings=item.average_bookings,
            peak_hour=item.peak_hour,
            average_passengers=item.average_passengers,
        )
        for item in entries
    ]


def _map_cost_recommendations(
    entries: Sequence[CostOptimisationRecommendation],
) -> list[CostOptimisationReport]:
    return [
        CostOptimisationReport(
            label=item.label,
            detail=item.detail,
            potential_saving=item.potential_saving,
        )
        for item in entries
    ]


def _map_custom_summary(summary: CustomReportSummary) -> CustomReportSummaryRead:
    return CustomReportSummaryRead(
        total_bookings=summary.total_bookings,
        total_completed=summary.total_completed,
        total_expenses=summary.total_expenses,
        average_booking_hours=summary.average_booking_hours,
        filters=summary.filters,
    )


def _map_custom_options(options: CustomReportOptions) -> CustomReportOptionsRead:
    return CustomReportOptionsRead(
        departments=options.departments,
        vehicle_types=options.vehicle_types,
        drivers=[
            CustomReportDriverOption(id=int(item["id"]), name=str(item["name"]))
            for item in options.drivers
        ],
    )


def _map_predictive(
    predictive: Sequence[PredictiveMaintenanceInsight],
) -> list[PredictiveMaintenanceReport]:
    return [
        PredictiveMaintenanceReport(
            vehicle_id=item.vehicle_id,
            registration_number=item.registration_number,
            vehicle_type=item.vehicle_type,
            risk_score=item.risk_score,
            recommended_action=item.recommended_action,
            projected_service_date=item.projected_service_date,
        )
        for item in predictive
    ]


def _map_expense_summary(report: ReportOverview) -> ExpenseAnalytics:
    analytics = report.expense_summary
    return ExpenseAnalytics(
        generated_at=analytics.generated_at,
        total_jobs=analytics.total_jobs,
        total_fuel_cost=analytics.total_fuel_cost,
        total_toll_cost=analytics.total_toll_cost,
        total_other_expenses=analytics.total_other_expenses,
        total_expenses=analytics.total_expenses,
        average_fuel_cost=analytics.average_fuel_cost,
        average_total_expense=analytics.average_total_expense,
        status_breakdown=[
            ExpenseStatusSummary(
                status=entry.status,
                count=entry.count,
                total_expenses=entry.total_expenses,
            )
            for entry in analytics.status_breakdown
        ],
    )


def _build_response(payload: ReportOverview) -> ReportOverviewResponse:
    return ReportOverviewResponse(
        generated_at=payload.generated_at,
        timeframe_start=payload.timeframe_start,
        timeframe_end=payload.timeframe_end,
        vehicle_utilisation=_map_vehicle_utilisation(payload.vehicle_utilisation),
        department_usage=_map_department_usage(payload.department_usage),
        driver_performance=_map_driver_performance(payload.driver_performance),
        expense_summary=_map_expense_summary(payload),
        predictive_maintenance=_map_predictive(payload.predictive_maintenance),
        booking_patterns=_map_booking_patterns(payload.booking_patterns),
        cost_recommendations=_map_cost_recommendations(payload.cost_recommendations),
        custom_report_summary=_map_custom_summary(payload.custom_report_summary),
        custom_report_options=_map_custom_options(payload.custom_report_options),
    )


@router.get("/overview", response_model=ReportOverviewResponse)
async def get_report_overview(
    start: datetime | None = Query(default=None),
    end: datetime | None = Query(default=None),
    department: str | None = Query(default=None, min_length=1, max_length=100),
    vehicle_type: VehicleType | None = Query(default=None),
    drivers: list[int] | None = Query(default=None),
    session: AsyncSession = Depends(get_async_session),
    _: User = Depends(_require_reporting_access),
) -> ReportOverviewResponse:
    """Return the consolidated reporting overview for the selected filters."""

    if start and end and start > end:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Start date must be before end date",
        )

    driver_ids: Optional[Sequence[int]] = drivers if drivers else None

    report = await generate_report_overview(
        session,
        start=start,
        end=end,
        department=department,
        vehicle_type=vehicle_type,
        driver_ids=driver_ids,
    )

    return _build_response(report)


@router.get("/health", response_model=dict[str, str])
async def get_reporting_health(
    _: User = Depends(_require_reporting_access),
) -> dict[str, str]:
    """Simple health endpoint to verify reporting access."""

    return {"status": "ready"}


__all__ = ["get_report_overview", "get_reporting_health", "router"]
