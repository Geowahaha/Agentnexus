from fastapi import APIRouter, Depends, Query

from app.auth.dependencies import get_current_user
from app.auth.models import User
from app.core.deps import get_notification_repository
from app.models.notification import (
    MarkNotificationsReadRequest,
    NotificationBadge,
    NotificationListResponse,
)
from app.repositories.notification_repository import NotificationRepository

router = APIRouter()


@router.get("/badge", response_model=NotificationBadge)
async def get_notification_badge(
    current_user: User = Depends(get_current_user),
    repository: NotificationRepository = Depends(get_notification_repository),
) -> NotificationBadge:
    return await repository.get_badge(current_user.id)


@router.get("", response_model=NotificationListResponse)
async def list_notifications(
    limit: int = Query(default=30, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    repository: NotificationRepository = Depends(get_notification_repository),
) -> NotificationListResponse:
    return await repository.list_events(current_user.id, limit=limit)


@router.post("/mark-read", response_model=NotificationBadge)
async def mark_notifications_read(
    payload: MarkNotificationsReadRequest,
    current_user: User = Depends(get_current_user),
    repository: NotificationRepository = Depends(get_notification_repository),
) -> NotificationBadge:
    return await repository.mark_read(current_user.id, payload.ids)