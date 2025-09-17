"""Administrative system management endpoints."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import RoleBasedAccess
from app.db import get_async_session
from app.models.user import User, UserRole
from app.schemas import (
    AuditLogRead,
    AuditLogSearchResponse,
    HealthRecordCreate,
    HealthRecordRead,
    HealthSummary,
    HolidayCreate,
    HolidayRead,
    SystemConfigurationRead,
    SystemConfigurationUpdate,
    UserActivityEntry,
    UserActivityReport,
    WorkingHourCreate,
    WorkingHourRead,
)
from app.services import (
    add_holiday,
    count_audit_logs,
    get_audit_log_statistics,
    get_health_summary,
    get_system_configuration,
    get_user_activity_report,
    list_holidays,
    list_recent_health_checks,
    list_working_hours,
    record_health_status,
    remove_holiday,
    remove_working_hour,
    search_audit_logs,
    update_system_configuration,
    upsert_working_hour,
)

router = APIRouter()

_admin_only = RoleBasedAccess([UserRole.FLEET_ADMIN])


async def _load_configuration(session: AsyncSession) -> SystemConfigurationRead:
    config = await get_system_configuration(session)
    await session.refresh(config, attribute_names=["holidays", "working_hours"])
    return SystemConfigurationRead.from_orm(config)


@router.get("/config", response_model=SystemConfigurationRead)
async def read_system_configuration(
    session: AsyncSession = Depends(get_async_session),
    _: User = Depends(_admin_only),
) -> SystemConfigurationRead:
    """Return the current global system configuration."""

    return await _load_configuration(session)


@router.put("/config", response_model=SystemConfigurationRead)
async def update_system_configuration_endpoint(
    config_update: SystemConfigurationUpdate,
    session: AsyncSession = Depends(get_async_session),
    _: User = Depends(_admin_only),
) -> SystemConfigurationRead:
    """Update global system settings."""

    await update_system_configuration(
        session,
        maintenance_mode=config_update.maintenance_mode,
        maintenance_message=config_update.maintenance_message,
        require_booking_approval=config_update.require_booking_approval,
        max_pending_bookings_per_user=config_update.max_pending_bookings_per_user,
        max_active_bookings_per_user=config_update.max_active_bookings_per_user,
        auto_cancel_pending_hours=config_update.auto_cancel_pending_hours,
        working_day_start=config_update.working_day_start,
        working_day_end=config_update.working_day_end,
        working_days=config_update.working_days,
        approval_escalation_hours=config_update.approval_escalation_hours,
        booking_lead_time_hours=config_update.booking_lead_time_hours,
    )
    return await _load_configuration(session)


@router.get("/holidays", response_model=list[HolidayRead])
async def list_holidays_endpoint(
    session: AsyncSession = Depends(get_async_session),
    _: User = Depends(_admin_only),
) -> list[HolidayRead]:
    """Return configured organisation-wide holidays."""

    holidays = await list_holidays(session)
    return [HolidayRead.from_orm(holiday) for holiday in holidays]


@router.post(
    "/holidays", response_model=HolidayRead, status_code=status.HTTP_201_CREATED
)
async def create_holiday_endpoint(
    holiday_create: HolidayCreate,
    session: AsyncSession = Depends(get_async_session),
    _: User = Depends(_admin_only),
) -> HolidayRead:
    """Create a new holiday entry."""

    holiday = await add_holiday(
        session,
        date=holiday_create.date,
        name=holiday_create.name,
        description=holiday_create.description,
    )
    return HolidayRead.from_orm(holiday)


@router.delete("/holidays/{holiday_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_holiday_endpoint(
    holiday_id: int,
    session: AsyncSession = Depends(get_async_session),
    _: User = Depends(_admin_only),
) -> None:
    """Delete a configured holiday."""

    removed = await remove_holiday(session, holiday_id)
    if not removed:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Holiday not found"
        )


@router.get("/working-hours", response_model=list[WorkingHourRead])
async def list_working_hours_endpoint(
    session: AsyncSession = Depends(get_async_session),
    _: User = Depends(_admin_only),
) -> list[WorkingHourRead]:
    """Return configured working hour windows."""

    working_hours = await list_working_hours(session)
    return [WorkingHourRead.from_orm(item) for item in working_hours]


@router.put("/working-hours/{day_of_week}", response_model=WorkingHourRead)
async def upsert_working_hours_endpoint(
    day_of_week: str,
    working_hours: WorkingHourCreate,
    session: AsyncSession = Depends(get_async_session),
    _: User = Depends(_admin_only),
) -> WorkingHourRead:
    """Create or update working hours for a given day of week."""

    normalised_path = day_of_week.lower()
    if working_hours.day_of_week != normalised_path:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="day_of_week in path and body must match",
        )
    record = await upsert_working_hour(
        session,
        day_of_week=working_hours.day_of_week,
        start_time=working_hours.start_time,
        end_time=working_hours.end_time,
    )
    return WorkingHourRead.from_orm(record)


@router.delete("/working-hours/{day_of_week}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_working_hours_endpoint(
    day_of_week: str,
    session: AsyncSession = Depends(get_async_session),
    _: User = Depends(_admin_only),
) -> None:
    """Remove configured working hours for the specified day."""

    removed = await remove_working_hour(session, day_of_week)
    if not removed:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Working hours not found"
        )


@router.get("/audit", response_model=AuditLogSearchResponse)
async def search_audit_endpoint(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=500),
    user_id: Optional[int] = Query(default=None),
    action: Optional[str] = Query(default=None),
    resource: Optional[str] = Query(default=None),
    status_code: Optional[int] = Query(default=None),
    query: Optional[str] = Query(default=None),
    date_from: Optional[datetime] = Query(default=None),
    date_to: Optional[datetime] = Query(default=None),
    session: AsyncSession = Depends(get_async_session),
    _: User = Depends(_admin_only),
) -> AuditLogSearchResponse:
    """Search the audit trail with flexible filters."""

    logs = await search_audit_logs(
        session,
        skip=skip,
        limit=limit,
        user_id=user_id,
        action=action,
        resource=resource,
        status_code=status_code,
        query=query,
        date_from=date_from,
        date_to=date_to,
    )
    total = await count_audit_logs(
        session,
        user_id=user_id,
        action=action,
        resource=resource,
        status_code=status_code,
        query=query,
        date_from=date_from,
        date_to=date_to,
    )
    return AuditLogSearchResponse(
        results=[AuditLogRead.from_orm(log) for log in logs],
        total=total,
    )


@router.get("/audit/statistics")
async def audit_statistics_endpoint(
    hours: int = Query(24, ge=1),
    session: AsyncSession = Depends(get_async_session),
    _: User = Depends(_admin_only),
) -> dict[str, int | dict[int, int]]:
    """Return quick statistics for audit trail monitoring."""

    since = datetime.utcnow() - timedelta(hours=hours)
    stats = await get_audit_log_statistics(session, since=since)
    return stats


@router.get("/health/checks", response_model=list[HealthRecordRead])
async def list_health_checks_endpoint(
    component: Optional[str] = Query(default=None),
    limit: int = Query(50, ge=1, le=200),
    session: AsyncSession = Depends(get_async_session),
    _: User = Depends(_admin_only),
) -> list[HealthRecordRead]:
    """Return recent system health checks."""

    checks = await list_recent_health_checks(
        session,
        component=component,
        limit=limit,
    )
    return [HealthRecordRead.from_orm(item) for item in checks]


@router.post(
    "/health/checks",
    response_model=HealthRecordRead,
    status_code=status.HTTP_201_CREATED,
)
async def record_health_check_endpoint(
    health_record: HealthRecordCreate,
    session: AsyncSession = Depends(get_async_session),
    _: User = Depends(_admin_only),
) -> HealthRecordRead:
    """Record an explicit health check reading."""

    record = await record_health_status(
        session,
        component=health_record.component,
        status=health_record.status,
        severity=health_record.severity,
        details=health_record.details,
        extra=health_record.extra,
    )
    return HealthRecordRead.from_orm(record)


@router.get("/health/summary", response_model=HealthSummary)
async def health_summary_endpoint(
    window_minutes: int = Query(60, ge=1),
    session: AsyncSession = Depends(get_async_session),
    _: User = Depends(_admin_only),
) -> HealthSummary:
    """Return the latest health summary across monitored components."""

    summary = await get_health_summary(session, window_minutes=window_minutes)
    return HealthSummary(**summary)


@router.get("/activity", response_model=UserActivityReport)
async def user_activity_report_endpoint(
    days: int = Query(7, ge=1, le=90),
    limit: int = Query(50, ge=1, le=200),
    session: AsyncSession = Depends(get_async_session),
    _: User = Depends(_admin_only),
) -> UserActivityReport:
    """Return user activity metrics derived from audit logs."""

    entries = await get_user_activity_report(session, days=days, limit=limit)
    return UserActivityReport(entries=[UserActivityEntry(**entry) for entry in entries])
