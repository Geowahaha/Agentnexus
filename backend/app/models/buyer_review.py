from datetime import datetime

from pydantic import BaseModel, Field


class BuyerReviewSubmit(BaseModel):
    workflow_id: str = Field(..., min_length=1)
    expert_skill_id: str = Field(..., min_length=1)
    rating: int = Field(..., ge=1, le=5)
    comment: str = Field(..., min_length=3, max_length=5000)


class BuyerReviewItem(BaseModel):
    id: str
    expert_skill_id: str
    skill_name: str
    skill_slug: str
    rating: int
    comment: str
    status: str
    workflow_id: str | None
    created_at: datetime
    updated_at: datetime
    has_creator_reply: bool = False
    unread_replies: int = 0


class WorkflowReviewEligibility(BaseModel):
    eligible: bool
    reason: str | None = None
    workflow_id: str | None = None
    workflow_status: str | None = None
    expert_skill_id: str | None = None
    skill_name: str | None = None
    skill_slug: str | None = None
    already_reviewed: bool = False
    existing_review: BuyerReviewItem | None = None


class BuyerReviewSubmitted(BaseModel):
    review: BuyerReviewItem
    message: str = "Review submitted successfully"