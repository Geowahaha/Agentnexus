from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, Field

from app.models.expert_skill import ExpertSkill


class CreatorSkillStats(BaseModel):
    total_runs: int = 0
    total_earnings_usd: Decimal = Decimal("0")
    average_rating: float | None = None
    review_count: int = 0


class CreatorSkillItem(ExpertSkill):
    stats: CreatorSkillStats = Field(default_factory=CreatorSkillStats)


class CreatorTopSkill(BaseModel):
    skill_id: str
    skill_name: str
    runs: int
    earnings_usd: Decimal


class CreatorActivityItem(BaseModel):
    id: str
    activity_type: str
    title: str
    detail: str | None = None
    amount_usd: Decimal | None = None
    created_at: datetime


class CreatorSummary(BaseModel):
    total_earnings_usd: Decimal
    earnings_balance_usd: Decimal
    total_runs: int
    active_skills: int
    total_skills: int
    average_rating: float | None
    review_count: int
    top_skill_this_month: CreatorTopSkill | None = None
    recent_activity: list[CreatorActivityItem] = Field(default_factory=list)
    minimum_payout_usd: Decimal = Decimal("10")
    platform_fee_percent: float


class AnalyticsDataPoint(BaseModel):
    period_start: date
    earnings_usd: Decimal
    runs: int


class CreatorAnalytics(BaseModel):
    period: str
    data_points: list[AnalyticsDataPoint]
    top_skills: list[CreatorTopSkill]
    average_runs_per_day: float
    conversion_rate: float | None = None
    conversion_tracked: bool = False


class SkillReview(BaseModel):
    id: str
    expert_skill_id: str
    skill_name: str
    buyer_id: str
    buyer_name: str
    rating: int
    comment: str
    workflow_id: str | None
    created_at: datetime


class CreatorReviewsSummary(BaseModel):
    average_rating: float | None
    review_count: int
    reviews: list[SkillReview]


class CreatorPayoutHistoryItem(BaseModel):
    id: str
    amount_usd: Decimal
    transaction_type: str
    description: str
    created_at: datetime


class CreatorPayouts(BaseModel):
    earnings_balance_usd: Decimal
    total_earned_usd: Decimal
    minimum_payout_usd: Decimal
    can_request_payout: bool
    payout_history: list[CreatorPayoutHistoryItem]


class ExpertSkillCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    slug: str = Field(..., min_length=1, max_length=120, pattern=r"^[a-z][a-z0-9-]*$")
    description: str = Field(..., min_length=1)
    category: str | None = Field(default=None, max_length=80)
    pack_slug: str = Field(default="custom", max_length=120)
    price_usd_per_run: Decimal = Field(default=Decimal("0"), ge=0)
    capabilities: list[str] = Field(default_factory=list)


class ExpertSkillUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = Field(default=None, min_length=1)
    name_th: str | None = Field(default=None, max_length=200)
    description_th: str | None = Field(default=None)
    category: str | None = Field(default=None, max_length=80)
    price_usd_per_run: Decimal | None = Field(default=None, ge=0)
    is_active: bool | None = None
    capabilities: list[str] | None = None
    crew_config: dict | None = None