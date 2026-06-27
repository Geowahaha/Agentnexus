from datetime import datetime

from pydantic import BaseModel, Field


class ReviewAttachment(BaseModel):
    id: str
    file_name: str
    content_type: str
    file_size: int
    download_url: str
    created_at: datetime


class ThreadMessage(BaseModel):
    id: str
    sender_id: str
    sender_name: str
    sender_role: str
    body: str
    attachments: list[ReviewAttachment] = Field(default_factory=list)
    created_at: datetime
    is_initial_review: bool = False


class ReviewInboxItem(BaseModel):
    id: str
    expert_skill_id: str
    skill_name: str
    buyer_id: str
    buyer_name: str
    buyer_avatar_url: str | None = None
    rating: int
    comment_preview: str
    status: str
    is_read: bool
    workflow_id: str | None
    created_at: datetime
    updated_at: datetime
    first_response_at: datetime | None = None
    response_time_hours: float | None = None
    message_count: int = 1


class ReviewInboxStats(BaseModel):
    average_rating: float | None
    total_reviews: int
    unread_count: int
    response_rate_percent: float
    average_response_time_hours: float | None
    average_response_time_label: str | None = None


class ReviewInboxResponse(BaseModel):
    stats: ReviewInboxStats
    items: list[ReviewInboxItem]


class ReviewThread(BaseModel):
    review_id: str
    expert_skill_id: str
    skill_name: str
    buyer_id: str
    buyer_name: str
    rating: int
    status: str
    messages: list[ThreadMessage]
    first_response_at: datetime | None = None
    resolved_at: datetime | None = None


class QuickReply(BaseModel):
    id: str
    title: str
    body: str
    sort_order: int
    created_at: datetime
    updated_at: datetime


class QuickReplyCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=120)
    body: str = Field(..., min_length=1)


class QuickReplyUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=120)
    body: str | None = Field(default=None, min_length=1)
    sort_order: int | None = None


class ReviewNotificationSettings(BaseModel):
    notify_mode: str = "all"


class ReviewNotificationBadge(BaseModel):
    unread_count: int
    notify_mode: str