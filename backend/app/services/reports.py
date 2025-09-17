"""Reporting and analytics services for fleet operations."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, date, datetime
from decimal import Decimal
from typing import Iterable, Optional, Sequence

from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.assignment import Assignment
from app.models.booking import BookingRequest, BookingStatus
from app.models.driver import Driver
from app.models.job_run import JobRun, JobRunStatus
from app.models.vehicle import Vehicle, VehicleType
from app.services.expense import ExpenseAnalyticsResult, generate_expense_analytics

_UTILISATION_STATUSES: Sequence[BookingStatus] = (
    BookingStatus.APPROVED,
    BookingStatus.ASSIGNED,
    BookingStatus.IN_PROGRESS,
    BookingStatus.COMPLETED,
)


def _normalise_department(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    cleaned = value.strip()
    return cleaned or None


def _duration_hours_expression(model: BookingRequest) -> func:  # type: ignore[type-arg]
    """Return an SQL expression that calculates booking duration in hours."""

    seconds = func.coalesce(
        func.extract("epoch", model.end_datetime - model.start_datetime),
        0,
    )
    return seconds / 3600.0


def _job_run_duration_expression() -> func:  # type: ignore[type-arg]
    """Return an SQL expression that calculates actual trip duration in hours."""

    seconds = func.coalesce(
        func.extract("epoch", JobRun.checkout_datetime - JobRun.checkin_datetime),
        0,
    )
    return seconds / 3600.0


@dataclass(slots=True)
class VehicleUtilisationEntry:
    """Aggregated utilisation metrics for a vehicle."""

    vehicle_id: int
    registration_number: str
    vehicle_type: VehicleType
    total_trips: int
    total_hours: float
    active_days: int
    average_trip_duration_hours: float
    utilisation_rate: float
    current_mileage: int


@dataclass(slots=True)
class DepartmentUsageEntry:
    """Monthly usage metrics grouped by department."""

    period: date
    department: str
    total_requests: int
    completed_trips: int
    total_passengers: int
    total_hours: float


@dataclass(slots=True)
class DriverPerformanceEntry:
    """Aggregated performance and workload metrics for drivers."""

    driver_id: int
    full_name: str
    assignments: int
    completed_jobs: int
    total_hours: float
    average_completion_time_hours: float
    workload_index: float


@dataclass(slots=True)
class PredictiveMaintenanceInsight:
    """Predictive maintenance signal for a vehicle."""

    vehicle_id: int
    registration_number: str
    vehicle_type: VehicleType
    risk_score: float
    recommended_action: str
    projected_service_date: date


@dataclass(slots=True)
class BookingPatternInsight:
    """Booking distribution insight for a specific day of week."""

    day_of_week: str
    weekday_index: int
    average_bookings: float
    peak_hour: int
    average_passengers: float


@dataclass(slots=True)
class CostOptimisationRecommendation:
    """Cost optimisation suggestion based on expense trends."""

    label: str
    detail: str
    potential_saving: float


@dataclass(slots=True)
class CustomReportSummary:
    """Summary statistics for the custom report builder."""

    total_bookings: int
    total_completed: int
    total_expenses: float
    average_booking_hours: float
    filters: dict[str, object]


@dataclass(slots=True)
class CustomReportOptions:
    """Available filtering options for the custom report builder."""

    departments: list[str]
    vehicle_types: list[VehicleType]
    drivers: list[dict[str, object]]


@dataclass(slots=True)
class ReportOverview:
    """Comprehensive reporting payload."""

    generated_at: datetime
    timeframe_start: Optional[datetime]
    timeframe_end: Optional[datetime]
    vehicle_utilisation: list[VehicleUtilisationEntry]
    department_usage: list[DepartmentUsageEntry]
    driver_performance: list[DriverPerformanceEntry]
    expense_summary: ExpenseAnalyticsResult
    predictive_maintenance: list[PredictiveMaintenanceInsight]
    booking_patterns: list[BookingPatternInsight]
    cost_recommendations: list[CostOptimisationRecommendation]
    custom_report_summary: CustomReportSummary
    custom_report_options: CustomReportOptions


async def _base_booking_filters(
    start: Optional[datetime],
    end: Optional[datetime],
    department: Optional[str],
) -> list:
    filters: list = [BookingRequest.status.in_(_UTILISATION_STATUSES)]
    if start is not None:
        filters.append(BookingRequest.start_datetime >= start)
    if end is not None:
        filters.append(BookingRequest.end_datetime <= end)
    if department is not None:
        filters.append(func.lower(BookingRequest.department) == department.lower())
    return filters


async def _gather_vehicle_utilisation(
    session: AsyncSession,
    *,
    start: Optional[datetime],
    end: Optional[datetime],
    department: Optional[str],
    vehicle_type: Optional[VehicleType],
) -> list[VehicleUtilisationEntry]:
    filters = await _base_booking_filters(start, end, department)

    stmt = (
        select(
            Vehicle.id,
            Vehicle.registration_number,
            Vehicle.vehicle_type,
            Vehicle.current_mileage,
            func.count(BookingRequest.id),
            func.coalesce(func.sum(_duration_hours_expression(BookingRequest)), 0.0),
            func.count(
                func.distinct(func.date_trunc("day", BookingRequest.start_datetime))
            ),
        )
        .join(Assignment, Assignment.vehicle_id == Vehicle.id)
        .join(BookingRequest, BookingRequest.id == Assignment.booking_request_id)
        .where(*filters)
        .group_by(Vehicle.id)
        .order_by(func.count(BookingRequest.id).desc())
    )

    if vehicle_type is not None:
        stmt = stmt.where(Vehicle.vehicle_type == vehicle_type)

    rows = await session.execute(stmt)

    entries: list[VehicleUtilisationEntry] = []
    for row in rows.all():
        (
            vehicle_id,
            registration_number,
            vehicle_type_value,
            current_mileage,
            trip_count,
            total_hours,
            active_days,
        ) = row

        trips = int(trip_count or 0)
        hours = float(total_hours or 0.0)
        days = int(active_days or 0)
        average_duration = hours / trips if trips else 0.0
        capacity_hours = days * 24 if days else (24 if trips else 0)
        utilisation_rate = (
            (hours / capacity_hours) * 100 if capacity_hours else (100.0 if trips else 0.0)
        )
        utilisation_rate = float(max(0.0, min(utilisation_rate, 100.0)))
        entries.append(
            VehicleUtilisationEntry(
                vehicle_id=int(vehicle_id),
                registration_number=registration_number,
                vehicle_type=vehicle_type_value,
                total_trips=trips,
                total_hours=round(hours, 2),
                active_days=days,
                average_trip_duration_hours=round(average_duration, 2),
                utilisation_rate=round(utilisation_rate, 2),
                current_mileage=int(current_mileage or 0),
            )
        )

    return entries


async def _gather_department_usage(
    session: AsyncSession,
    *,
    start: Optional[datetime],
    end: Optional[datetime],
    department: Optional[str],
    vehicle_type: Optional[VehicleType],
) -> list[DepartmentUsageEntry]:
    filters = await _base_booking_filters(start, end, department)

    stmt = (
        select(
            func.date_trunc("month", BookingRequest.start_datetime),
            func.coalesce(BookingRequest.department, "ไม่ระบุ"),
            func.count(BookingRequest.id),
            func.sum(
                case((JobRun.status == JobRunStatus.COMPLETED, 1), else_=0)
            ),
            func.coalesce(func.sum(BookingRequest.passenger_count), 0),
            func.coalesce(func.sum(_duration_hours_expression(BookingRequest)), 0.0),
        )
        .join(Assignment, Assignment.booking_request_id == BookingRequest.id)
        .join(Vehicle, Vehicle.id == Assignment.vehicle_id)
        .outerjoin(JobRun, JobRun.booking_request_id == BookingRequest.id)
        .where(*filters)
        .group_by(func.date_trunc("month", BookingRequest.start_datetime), BookingRequest.department)
        .order_by(func.date_trunc("month", BookingRequest.start_datetime))
    )

    if vehicle_type is not None:
        stmt = stmt.where(Vehicle.vehicle_type == vehicle_type)

    rows = await session.execute(stmt)

    results: list[DepartmentUsageEntry] = []
    for row in rows.all():
        (
            period,
            department_value,
            total_requests,
            completed_trips,
            passenger_total,
            total_hours,
        ) = row

        month_date = (period or datetime.now(UTC)).date()
        results.append(
            DepartmentUsageEntry(
                period=month_date.replace(day=1),
                department=str(department_value or "ไม่ระบุ"),
                total_requests=int(total_requests or 0),
                completed_trips=int(completed_trips or 0),
                total_passengers=int(passenger_total or 0),
                total_hours=round(float(total_hours or 0.0), 2),
            )
        )

    return results


async def _gather_driver_performance(
    session: AsyncSession,
    *,
    start: Optional[datetime],
    end: Optional[datetime],
    department: Optional[str],
    vehicle_type: Optional[VehicleType],
) -> list[DriverPerformanceEntry]:
    filters = await _base_booking_filters(start, end, department)

    stmt = (
        select(
            Driver.id,
            Driver.full_name,
            func.count(Assignment.id),
            func.coalesce(
                func.sum(
                    case(
                        (JobRun.status == JobRunStatus.COMPLETED, _job_run_duration_expression()),
                        else_=0.0,
                    )
                ),
                0.0,
            ),
            func.coalesce(
                func.sum(case((JobRun.status == JobRunStatus.COMPLETED, 1), else_=0)),
                0,
            ),
            func.coalesce(
                func.avg(
                    case(
                        (JobRun.status == JobRunStatus.COMPLETED, _job_run_duration_expression()),
                        else_=None,
                    )
                ),
                0.0,
            ),
        )
        .join(Assignment, Assignment.driver_id == Driver.id)
        .join(BookingRequest, BookingRequest.id == Assignment.booking_request_id)
        .outerjoin(JobRun, JobRun.booking_request_id == BookingRequest.id)
        .join(Vehicle, Vehicle.id == Assignment.vehicle_id)
        .where(*filters)
        .group_by(Driver.id)
        .order_by(func.count(Assignment.id).desc())
    )

    if vehicle_type is not None:
        stmt = stmt.where(Vehicle.vehicle_type == vehicle_type)

    rows = await session.execute(stmt)

    entries: list[DriverPerformanceEntry] = []
    for row in rows.all():
        (
            driver_id,
            full_name,
            assignment_count,
            total_hours,
            completed_jobs,
            average_hours,
        ) = row

        assignments = int(assignment_count or 0)
        completed = int(completed_jobs or 0)
        total_duration = float(total_hours or 0.0)
        average_duration = float(average_hours or 0.0)
        workload = (
            min(100.0, (completed / assignments) * 100) if assignments else 0.0
        )
        entries.append(
            DriverPerformanceEntry(
                driver_id=int(driver_id),
                full_name=full_name,
                assignments=assignments,
                completed_jobs=completed,
                total_hours=round(total_duration, 2),
                average_completion_time_hours=round(average_duration, 2),
                workload_index=round(workload, 2),
            )
        )

    return entries


async def _gather_booking_patterns(
    session: AsyncSession,
    *,
    start: Optional[datetime],
    end: Optional[datetime],
    department: Optional[str],
) -> list[BookingPatternInsight]:
    filters = await _base_booking_filters(start, end, department)

    day_stmt = (
        select(
            func.extract("dow", BookingRequest.start_datetime),
            func.coalesce(func.count(BookingRequest.id), 0),
            func.coalesce(func.avg(BookingRequest.passenger_count), 0.0),
        )
        .where(*filters)
        .group_by(func.extract("dow", BookingRequest.start_datetime))
    )

    hour_stmt = (
        select(
            func.extract("hour", BookingRequest.start_datetime),
            func.count(BookingRequest.id),
        )
        .where(*filters)
        .group_by(func.extract("hour", BookingRequest.start_datetime))
    )

    day_rows = await session.execute(day_stmt)
    hour_rows = await session.execute(hour_stmt)

    hourly_counts = {int(hour): int(count) for hour, count in hour_rows.all()}
    peak_hour = max(hourly_counts, key=hourly_counts.get, default=8)

    insights: list[BookingPatternInsight] = []
    for weekday_index, booking_count, passengers in day_rows.all():
        weekday = int(weekday_index or 0)
        average_bookings = float(booking_count or 0) / max(1, len(hourly_counts) or 1)
        average_passengers = float(passengers or 0.0)
        day_label = [
            "วันอาทิตย์",
            "วันจันทร์",
            "วันอังคาร",
            "วันพุธ",
            "วันพฤหัสบดี",
            "วันศุกร์",
            "วันเสาร์",
        ][weekday % 7]
        insights.append(
            BookingPatternInsight(
                day_of_week=day_label,
                weekday_index=weekday,
                average_bookings=round(average_bookings, 2),
                peak_hour=int(peak_hour),
                average_passengers=round(average_passengers, 2),
            )
        )

    insights.sort(key=lambda item: item.weekday_index)
    return insights


async def _gather_cost_recommendations(
    session: AsyncSession,
    *,
    start: Optional[datetime],
    end: Optional[datetime],
    department: Optional[str],
) -> list[CostOptimisationRecommendation]:
    filters = await _base_booking_filters(start, end, department)
    filters.append(JobRun.checkout_datetime.is_not(None))

    expense_stmt = (
        select(
            func.coalesce(BookingRequest.department, "ไม่ระบุ"),
            func.coalesce(
                func.sum(
                    JobRun.fuel_cost + JobRun.toll_cost + JobRun.other_expenses
                ),
                0,
            ),
            func.count(JobRun.id),
        )
        .join(JobRun, JobRun.booking_request_id == BookingRequest.id)
        .where(*filters)
        .group_by(BookingRequest.department)
    )

    rows = await session.execute(expense_stmt)

    recommendations: list[CostOptimisationRecommendation] = []
    for department_value, total_expense, job_count in rows.all():
        trips = int(job_count or 0)
        total = float(total_expense or 0.0)
        if trips == 0:
            continue
        cost_per_trip = total / trips
        potential = round(cost_per_trip * 0.1, 2)
        recommendations.append(
            CostOptimisationRecommendation(
                label=f"{department_value or 'ไม่ระบุ'}",
                detail=(
                    "ค่าใช้จ่ายต่อการเดินทางสูงกว่าค่าเฉลี่ย เสนอให้ประเมินการใช้รถร่วม"
                    if cost_per_trip > 1500
                    else "พิจารณากำหนดเส้นทางให้มีการรวมงานเพื่อลดค่าใช้จ่าย"
                ),
                potential_saving=potential,
            )
        )

    if not recommendations:
        recommendations.append(
            CostOptimisationRecommendation(
                label="ภาพรวม",
                detail="ค่าใช้จ่ายอยู่ในระดับที่ควบคุมได้ ควรรักษาการติดตามอย่างต่อเนื่อง",
                potential_saving=0.0,
            )
        )

    return recommendations


async def _gather_custom_report_summary(
    session: AsyncSession,
    *,
    start: Optional[datetime],
    end: Optional[datetime],
    department: Optional[str],
    vehicle_type: Optional[VehicleType],
    driver_ids: Optional[Sequence[int]] = None,
) -> CustomReportSummary:
    filters = await _base_booking_filters(start, end, department)

    stmt = (
        select(
            func.count(BookingRequest.id),
            func.sum(
                case((JobRun.status == JobRunStatus.COMPLETED, 1), else_=0)
            ),
            func.coalesce(func.sum(_duration_hours_expression(BookingRequest)), 0.0),
            func.coalesce(
                func.sum(
                    case(
                        (JobRun.status.in_([JobRunStatus.COMPLETED, JobRunStatus.IN_PROGRESS]),
                         JobRun.fuel_cost + JobRun.toll_cost + JobRun.other_expenses),
                        else_=Decimal("0.00"),
                    )
                ),
                Decimal("0.00"),
            ),
        )
        .join(Assignment, Assignment.booking_request_id == BookingRequest.id)
        .join(Vehicle, Vehicle.id == Assignment.vehicle_id)
        .outerjoin(JobRun, JobRun.booking_request_id == BookingRequest.id)
        .where(*filters)
    )

    if vehicle_type is not None:
        stmt = stmt.where(Vehicle.vehicle_type == vehicle_type)
    if driver_ids:
        stmt = stmt.where(Assignment.driver_id.in_(driver_ids))

    total_bookings, total_completed, total_hours, total_expenses = (
        await session.execute(stmt)
    ).one()

    bookings = int(total_bookings or 0)
    completed = int(total_completed or 0)
    hours = float(total_hours or 0.0)
    expenses = float(total_expenses or 0.0)
    average_hours = hours / bookings if bookings else 0.0

    filters_payload: dict[str, object] = {}
    if start:
        filters_payload["start"] = start.isoformat()
    if end:
        filters_payload["end"] = end.isoformat()
    if department:
        filters_payload["department"] = department
    if vehicle_type is not None:
        filters_payload["vehicle_type"] = vehicle_type.value
    if driver_ids:
        filters_payload["drivers"] = list(driver_ids)

    return CustomReportSummary(
        total_bookings=bookings,
        total_completed=completed,
        total_expenses=round(expenses, 2),
        average_booking_hours=round(average_hours, 2),
        filters=filters_payload,
    )


async def _gather_custom_report_options(session: AsyncSession) -> CustomReportOptions:
    department_stmt = select(func.distinct(BookingRequest.department)).order_by(
        BookingRequest.department
    )
    vehicle_stmt = select(func.distinct(Vehicle.vehicle_type)).order_by(Vehicle.vehicle_type)
    driver_stmt = select(Driver.id, Driver.full_name).order_by(Driver.full_name)

    departments = [
        value
        for (value,) in (await session.execute(department_stmt)).all()
        if value
    ]
    vehicle_types = [
        value
        for (value,) in (await session.execute(vehicle_stmt)).all()
        if value is not None
    ]
    drivers = [
        {"id": int(driver_id), "name": full_name}
        for driver_id, full_name in (await session.execute(driver_stmt)).all()
    ]

    return CustomReportOptions(
        departments=departments,
        vehicle_types=vehicle_types,
        drivers=drivers,
    )


def _build_predictive_maintenance(
    utilisation: Iterable[VehicleUtilisationEntry],
) -> list[PredictiveMaintenanceInsight]:
    today = datetime.now(UTC).date()
    insights: list[PredictiveMaintenanceInsight] = []
    for entry in utilisation:
        mileage_factor = min(1.0, entry.current_mileage / 120_000)
        utilisation_factor = entry.utilisation_rate / 100.0
        duration_factor = min(1.0, entry.average_trip_duration_hours / 8.0)
        risk = round((mileage_factor * 0.5 + utilisation_factor * 0.35 + duration_factor * 0.15) * 100, 2)
        if risk >= 80:
            recommendation = "ควรจัดตารางบำรุงรักษาภายใน 7 วัน"
            offset = 7
        elif risk >= 60:
            recommendation = "ตรวจสอบระบบหลักและเตรียมอะไหล่สำรอง"
            offset = 14
        elif risk >= 40:
            recommendation = "ติดตามข้อมูลการใช้งานอย่างใกล้ชิด"
            offset = 21
        else:
            recommendation = "อยู่ในสภาพพร้อมใช้งาน ตรวจสอบตามรอบปกติ"
            offset = 30

        insights.append(
            PredictiveMaintenanceInsight(
                vehicle_id=entry.vehicle_id,
                registration_number=entry.registration_number,
                vehicle_type=entry.vehicle_type,
                risk_score=risk,
                recommended_action=recommendation,
                projected_service_date=today.replace(day=min(today.day + offset, 28)),
            )
        )

    return insights


async def generate_report_overview(
    session: AsyncSession,
    *,
    start: Optional[datetime] = None,
    end: Optional[datetime] = None,
    department: Optional[str] = None,
    vehicle_type: Optional[VehicleType] = None,
    driver_ids: Optional[Sequence[int]] = None,
) -> ReportOverview:
    """Generate an aggregated reporting overview for the requested filters."""

    department_filter = _normalise_department(department)

    vehicle_utilisation = await _gather_vehicle_utilisation(
        session,
        start=start,
        end=end,
        department=department_filter,
        vehicle_type=vehicle_type,
    )
    department_usage = await _gather_department_usage(
        session,
        start=start,
        end=end,
        department=department_filter,
        vehicle_type=vehicle_type,
    )
    driver_performance = await _gather_driver_performance(
        session,
        start=start,
        end=end,
        department=department_filter,
        vehicle_type=vehicle_type,
    )
    expense_summary = await generate_expense_analytics(
        session,
        start=start,
        end=end,
        status=None,
    )
    booking_patterns = await _gather_booking_patterns(
        session,
        start=start,
        end=end,
        department=department_filter,
    )
    cost_recommendations = await _gather_cost_recommendations(
        session,
        start=start,
        end=end,
        department=department_filter,
    )
    custom_report_summary = await _gather_custom_report_summary(
        session,
        start=start,
        end=end,
        department=department_filter,
        vehicle_type=vehicle_type,
        driver_ids=driver_ids,
    )
    custom_report_options = await _gather_custom_report_options(session)
    predictive_maintenance = _build_predictive_maintenance(vehicle_utilisation)

    return ReportOverview(
        generated_at=datetime.now(UTC),
        timeframe_start=start,
        timeframe_end=end,
        vehicle_utilisation=vehicle_utilisation,
        department_usage=department_usage,
        driver_performance=driver_performance,
        expense_summary=expense_summary,
        predictive_maintenance=predictive_maintenance,
        booking_patterns=booking_patterns,
        cost_recommendations=cost_recommendations,
        custom_report_summary=custom_report_summary,
        custom_report_options=custom_report_options,
    )


__all__ = [
    "BookingPatternInsight",
    "CostOptimisationRecommendation",
    "CustomReportOptions",
    "CustomReportSummary",
    "DepartmentUsageEntry",
    "DriverPerformanceEntry",
    "PredictiveMaintenanceInsight",
    "ReportOverview",
    "VehicleUtilisationEntry",
    "generate_report_overview",
]
