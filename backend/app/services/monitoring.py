"""System health monitoring services."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.system import SystemHealthRecord


async def record_health_status(
    session: AsyncSession,
    *,
    component: str,
    status: str,
    severity: str = "info",
    details: str | None = None,
    extra: dict[str, Any] | None = None,
) -> SystemHealthRecord:
    """Persist a health status observation for the specified component."""

    record = SystemHealthRecord(
        component=component,
        status=status,
        severity=severity,
        details=details,
        extra=extra,
    )
    session.add(record)
    await session.commit()
    await session.refresh(record)
    return record


async def list_recent_health_checks(
    session: AsyncSession,
    *,
    component: str | None = None,
    limit: int = 50,
) -> list[SystemHealthRecord]:
    """Return recent health checks optionally filtered by component."""

    stmt = select(SystemHealthRecord).order_by(SystemHealthRecord.created_at.desc())
    if component is not None:
        stmt = stmt.where(SystemHealthRecord.component == component)
    stmt = stmt.limit(limit)
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def get_health_summary(
    session: AsyncSession,
    *,
    window_minutes: int = 60,
) -> dict[str, Any]:
    """Return a summary of the latest health status for each component."""

    since = datetime.utcnow() - timedelta(minutes=window_minutes)

    latest_subquery = (
        select(
            SystemHealthRecord.component.label("component"),
            func.max(SystemHealthRecord.created_at).label("latest_checked"),
        )
        .where(SystemHealthRecord.created_at >= since)
        .group_by(SystemHealthRecord.component)
        .subquery()
    )

    stmt = (
        select(SystemHealthRecord)
        .join(
            latest_subquery,
            and_(
                SystemHealthRecord.component == latest_subquery.c.component,
                SystemHealthRecord.created_at == latest_subquery.c.latest_checked,
            ),
        )
        .order_by(SystemHealthRecord.component.asc())
    )
    result = await session.execute(stmt)
    records = list(result.scalars().all())

    def _normalise(status: str) -> str:
        lowered = status.lower()
        if lowered in {"healthy", "ok", "online"}:
            return "healthy"
        if lowered in {"warning", "degraded"}:
            return "degraded"
        if lowered in {"critical", "down", "error"}:
            return "critical"
        return lowered

    normalised = [_normalise(record.status) for record in records]
    if not normalised:
        overall = "unknown"
    elif any(status == "critical" for status in normalised):
        overall = "critical"
    elif any(status == "degraded" for status in normalised):
        overall = "degraded"
    else:
        overall = "healthy"

    return {
        "overall_status": overall,
        "components": [
            {
                "component": record.component,
                "status": record.status,
                "severity": record.severity,
                "details": record.details,
                "extra": record.extra,
                "checked_at": record.created_at,
            }
            for record in records
        ],
    }


__all__ = [
    "get_health_summary",
    "list_recent_health_checks",
    "record_health_status",
]
