"""Audit logging and reporting services."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.system import AuditLog
from app.models.user import User


async def log_audit_event(
    session: AsyncSession,
    *,
    actor_id: int | None,
    action: str,
    resource: str,
    status_code: int,
    ip_address: str | None,
    user_agent: str | None,
    context: dict[str, Any] | None = None,
) -> AuditLog:
    """Persist a new audit log entry."""

    entry = AuditLog(
        user_id=actor_id,
        action=action,
        resource=resource,
        status_code=status_code,
        ip_address=ip_address,
        user_agent=user_agent,
        context=context,
    )
    session.add(entry)
    await session.commit()
    await session.refresh(entry)
    return entry


def _build_filters(
    *,
    user_id: int | None = None,
    action: str | None = None,
    resource: str | None = None,
    status_code: int | None = None,
    query: str | None = None,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
) -> list[Any]:
    filters: list[Any] = []

    if user_id is not None:
        filters.append(AuditLog.user_id == user_id)
    if action is not None:
        filters.append(AuditLog.action == action)
    if resource is not None:
        filters.append(AuditLog.resource == resource)
    if status_code is not None:
        filters.append(AuditLog.status_code == status_code)
    if date_from is not None:
        filters.append(AuditLog.created_at >= date_from)
    if date_to is not None:
        filters.append(AuditLog.created_at <= date_to)

    if query:
        like_term = f"%{query.lower()}%"
        filters.append(
            or_(
                func.lower(AuditLog.resource).like(like_term),
                func.lower(AuditLog.action).like(like_term),
                func.coalesce(func.lower(AuditLog.user_agent), "").like(like_term),
            )
        )

    return filters


async def search_audit_logs(
    session: AsyncSession,
    *,
    skip: int = 0,
    limit: int = 100,
    user_id: int | None = None,
    action: str | None = None,
    resource: str | None = None,
    status_code: int | None = None,
    query: str | None = None,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
) -> list[AuditLog]:
    """Search audit log entries using a variety of filters."""

    stmt = select(AuditLog).order_by(AuditLog.created_at.desc())
    filters = _build_filters(
        user_id=user_id,
        action=action,
        resource=resource,
        status_code=status_code,
        query=query,
        date_from=date_from,
        date_to=date_to,
    )

    if filters:
        stmt = stmt.where(and_(*filters))

    stmt = stmt.offset(skip).limit(limit)
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def count_audit_logs(
    session: AsyncSession,
    *,
    user_id: int | None = None,
    action: str | None = None,
    resource: str | None = None,
    status_code: int | None = None,
    query: str | None = None,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
) -> int:
    """Return the count of audit log entries that match the filters."""

    filters = _build_filters(
        user_id=user_id,
        action=action,
        resource=resource,
        status_code=status_code,
        query=query,
        date_from=date_from,
        date_to=date_to,
    )

    stmt = select(func.count(AuditLog.id))
    if filters:
        stmt = stmt.where(and_(*filters))

    return (await session.execute(stmt)).scalar_one()


async def get_user_activity_report(
    session: AsyncSession,
    *,
    days: int = 7,
    limit: int = 50,
) -> list[dict[str, Any]]:
    """Return aggregated user activity statistics for the given period."""

    since = datetime.utcnow() - timedelta(days=days)

    stmt = (
        select(
            User.id.label("user_id"),
            User.username,
            User.full_name,
            func.count(AuditLog.id).label("actions"),
            func.max(AuditLog.created_at).label("last_activity"),
        )
        .join(AuditLog, AuditLog.user_id == User.id)
        .where(AuditLog.created_at >= since)
        .group_by(User.id, User.username, User.full_name)
        .order_by(func.count(AuditLog.id).desc())
        .limit(limit)
    )

    result = await session.execute(stmt)
    rows = result.all()
    return [
        {
            "user_id": row.user_id,
            "username": row.username,
            "full_name": row.full_name,
            "actions": row.actions,
            "last_activity": row.last_activity,
        }
        for row in rows
    ]


async def get_audit_log_statistics(
    session: AsyncSession,
    *,
    since: datetime | None = None,
) -> dict[str, Any]:
    """Provide quick statistics for the audit trail."""

    stmt = select(func.count(AuditLog.id))
    if since is not None:
        stmt = stmt.where(AuditLog.created_at >= since)
    total = (await session.execute(stmt)).scalar_one()

    status_stmt = select(AuditLog.status_code, func.count(AuditLog.id)).group_by(
        AuditLog.status_code
    )
    if since is not None:
        status_stmt = status_stmt.where(AuditLog.created_at >= since)
    status_stmt = status_stmt.order_by(func.count(AuditLog.id).desc())

    status_rows = await session.execute(status_stmt)
    status_breakdown = {row[0]: row[1] for row in status_rows.all()}

    return {
        "total_events": total,
        "status_breakdown": status_breakdown,
    }


__all__ = [
    "get_audit_log_statistics",
    "get_user_activity_report",
    "count_audit_logs",
    "log_audit_event",
    "search_audit_logs",
]
