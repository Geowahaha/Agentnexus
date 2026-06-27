from datetime import datetime

from pydantic import BaseModel, Field


class NotificationEvent(BaseModel):
    id: str
    event_type: str
    title: str
    body: str
    payload: dict = Field(default_factory=dict)
    is_read: bool
    created_at: datetime


class NotificationBadge(BaseModel):
    unread_count: int


class NotificationListResponse(BaseModel):
    items: list[NotificationEvent]
    unread_count: int


class MarkNotificationsReadRequest(BaseModel):
    ids: list[str] = Field(default_factory=list)