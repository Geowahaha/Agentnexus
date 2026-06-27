from datetime import datetime

from pydantic import BaseModel, Field


class AgentStats(BaseModel):
    portfolio_count: int = 0
    total_hires: int = 0


class PortfolioItem(BaseModel):
    id: str
    agent_id: str
    workflow_id: str
    title: str
    summary: str | None = None
    task_preview: str
    output_preview: str
    workflow_type: str
    is_public: bool
    sort_order: int
    created_at: datetime
    updated_at: datetime


class PortfolioItemCreate(BaseModel):
    workflow_id: str = Field(..., min_length=1)
    title: str | None = Field(default=None, max_length=200)
    summary: str | None = Field(default=None, max_length=2000)
    is_public: bool = True


class PortfolioItemUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    summary: str | None = Field(default=None, max_length=2000)
    is_public: bool | None = None
    sort_order: int | None = None


class AgentProfile(BaseModel):
    agent_id: str
    stats: AgentStats
    portfolio: list[PortfolioItem]