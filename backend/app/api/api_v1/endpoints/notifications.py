"""Notification management API endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.db import get_async_session
from app.models import Notification
from app.models.user import User
from app.schemas import (
    NotificationCreateRequest,
    NotificationMarkReadResponse,
    NotificationPreferenceRead,
    NotificationPreferenceUpdate,
    NotificationRead,
)
from app.services.notification import NotificationService

router = APIRouter()


def _serialise_preference(preference) -> NotificationPreferenceRead:
    return NotificationPreferenceRead(
        in_app_enabled=preference.in_app_enabled,
        email_enabled=preference.email_enabled,
        line_enabled=preference.line_enabled,
        line_token_registered=bool(preference.line_access_token),
        updated_at=preference.updated_at,
    )


@router.get("/", response_model=list[NotificationRead])
async def list_notifications(
    limit: int = 20,
    offset: int = 0,
    unread_only: bool = False,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user),
) -> list[NotificationRead]:
    """Return a list of notifications for the current user."""

    service = NotificationService(session)
    notifications = await service.list_notifications(
        current_user.id, limit=limit, offset=offset, unread_only=unread_only
    )
    return [NotificationRead.model_validate(notification) for notification in notifications]


@router.get("/unread-count")
async def unread_count(
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user),
) -> dict[str, int]:
    """Return the number of unread notifications for the current user."""

    service = NotificationService(session)
    count = await service.count_unread(current_user.id)
    return {"unread": count}


@router.post("/{notification_id}/read", response_model=NotificationMarkReadResponse)
async def mark_notification_read(
    notification_id: int,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user),
) -> NotificationMarkReadResponse:
    """Mark the specified notification as read."""

    notification = await session.get(Notification, notification_id)
    if notification is None or notification.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found",
        )

    service = NotificationService(session)
    updated = await service.mark_read(notification)
    return NotificationMarkReadResponse(
        notification=NotificationRead.model_validate(updated)
    )


@router.post("/read-all")
async def mark_all_read(
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user),
) -> dict[str, int]:
    """Mark all notifications as read for the current user."""

    service = NotificationService(session)
    updated = await service.mark_all_read(current_user.id)
    return {"updated": updated}


@router.get("/preferences", response_model=NotificationPreferenceRead)
async def get_preferences(
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user),
) -> NotificationPreferenceRead:
    """Return the user's current notification preferences."""

    service = NotificationService(session)
    preference = await service.get_preferences(current_user.id)
    return _serialise_preference(preference)


@router.put("/preferences", response_model=NotificationPreferenceRead)
async def update_preferences(
    payload: NotificationPreferenceUpdate,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user),
) -> NotificationPreferenceRead:
    """Update the user's notification preferences."""

    service = NotificationService(session)
    preference = await service.update_preferences(
        current_user.id,
        in_app_enabled=payload.in_app_enabled,
        email_enabled=payload.email_enabled,
        line_enabled=payload.line_enabled,
        line_access_token=payload.line_access_token,
    )
    return _serialise_preference(preference)


@router.post("/dispatch-test", response_model=NotificationRead)
async def dispatch_test_notification(
    payload: NotificationCreateRequest,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user),
) -> NotificationRead:
    """Allow users to trigger a notification to verify their settings."""

    service = NotificationService(session)
    notification = await service.create_notification(
        current_user,
        title=payload.title,
        message=payload.message,
        category=payload.category,
        metadata=payload.metadata,
        channels=payload.channels,
    )
    return NotificationRead.model_validate(notification)

