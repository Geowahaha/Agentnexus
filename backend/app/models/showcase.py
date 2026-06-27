from datetime import datetime

from pydantic import BaseModel, Field


class BotStatusChange(BaseModel):
    name: str
    before: str
    after: str


class ShowcaseCategoryScores(BaseModel):
    discoverability: int | None = None
    content: int | None = None
    bot_access: int | None = None
    protocol: int | None = None
    commerce: int | None = None
    overall: int | None = None


class ShowcaseBeforeAfter(BaseModel):
    score_before: str | None = None
    score_after: str | None = None
    category_scores: dict[str, ShowcaseCategoryScores] = Field(default_factory=dict)
    bots: list[BotStatusChange] = Field(default_factory=list)
    fixes_applied: list[str] = Field(default_factory=list)
    snapshots: dict[str, str] = Field(default_factory=dict)


class SkillShowcaseSkillSummary(BaseModel):
    id: str
    slug: str
    name: str
    category: str | None = None
    price_usd_per_run: str


class ShowcaseFromWorkflowCreate(BaseModel):
    workflow_id: str
    title: str | None = None
    site_name: str | None = None
    site_url: str | None = None


class SkillShowcase(BaseModel):
    id: str
    expert_skill_id: str
    title: str
    site_name: str
    site_url: str
    summary: str
    metric_label: str | None = None
    metric_value: str | None = None
    highlights: list[str] = Field(default_factory=list)
    sort_order: int = 0
    is_featured: bool = False
    is_active: bool = True
    workflow_id: str | None = None
    sample_output: str | None = None
    deliverables: list[str] = Field(default_factory=list)
    stats: dict[str, str] = Field(default_factory=dict)
    before_after: ShowcaseBeforeAfter = Field(default_factory=ShowcaseBeforeAfter)
    created_at: datetime
    updated_at: datetime
    skill: SkillShowcaseSkillSummary | None = None