from datetime import datetime, timezone
from decimal import Decimal
from uuid import uuid4

from pydantic import BaseModel, Field


class AgentBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=120)
    description: str = Field(..., min_length=1)
    role: str = Field(..., min_length=1, description="Agent persona, e.g. SEO Pro, Content Writer")
    llm_model: str = Field(..., min_length=1, description="LLM model identifier, e.g. gpt-4o")
    tools: list[str] = Field(default_factory=list)
    is_active: bool = True
    price_usd_per_run: Decimal = Field(default=Decimal("0"), ge=0)
    capabilities: list[str] = Field(default_factory=list)
    category: str | None = Field(default=None, max_length=80)


class AgentCreate(AgentBase):
    """Payload for creating a new marketplace agent."""


class AgentUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    description: str | None = Field(default=None, min_length=1)
    role: str | None = Field(default=None, min_length=1)
    llm_model: str | None = Field(default=None, min_length=1)
    tools: list[str] | None = None
    is_active: bool | None = None
    price_usd_per_run: Decimal | None = Field(default=None, ge=0)
    capabilities: list[str] | None = None
    category: str | None = Field(default=None, max_length=80)


class Agent(AgentBase):
    id: str
    owner_id: str
    created_at: datetime
    updated_at: datetime


class AgentDetail(Agent):
    owner_name: str | None = None

    @classmethod
    def from_create(cls, data: AgentCreate) -> "Agent":
        now = datetime.now(timezone.utc)
        return cls(
            id=str(uuid4()),
            created_at=now,
            updated_at=now,
            **data.model_dump(),
        )