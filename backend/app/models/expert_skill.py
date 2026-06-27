from datetime import datetime, timezone
from decimal import Decimal
from uuid import uuid4

from pydantic import BaseModel, Field


class ExpertSkill(BaseModel):
    id: str
    slug: str
    name: str
    description: str
    i18n: dict = Field(default_factory=dict)
    display_locale: str | None = None
    category: str | None = None
    pack_slug: str
    crew_config: dict = Field(default_factory=dict)
    capabilities: list[str] = Field(default_factory=list)
    price_usd_per_run: Decimal = Field(default=Decimal("0"), ge=0)
    owner_id: str
    is_active: bool = True
    created_at: datetime
    updated_at: datetime


class PipelineStepInfo(BaseModel):
    id: str
    title: str
    step_type: str
    tool_or_model: str | None = None


class SkillAttributionLink(BaseModel):
    label: str
    href: str
    detail: str


class SkillAttribution(BaseModel):
    charter_summary: str
    pack_slug: str
    upstream: list[SkillAttributionLink] = Field(default_factory=list)
    obolla_layer: str
    pricing_honesty: str
    credits_markdown: str | None = None


class ModelTierRuntimeInfo(BaseModel):
    downgraded: bool = False
    requested_tier_id: str | None = None
    effective_tier_id: str | None = None
    effective_price_usd: str | None = None
    listed_price_usd: str | None = None
    note_en: str | None = None
    note_th: str | None = None


class ExpertSkillDetail(ExpertSkill):
    skill_preview: str | None = None
    reference_count: int = 0
    owner_name: str | None = None
    pipeline_steps: list[PipelineStepInfo] = Field(default_factory=list)
    attribution: SkillAttribution | None = None
    model_tier_runtime: ModelTierRuntimeInfo | None = None


class ExpertSkillRunRequest(BaseModel):
    task_description: str = Field(..., min_length=1, description="URL or task, e.g. https://example.com")