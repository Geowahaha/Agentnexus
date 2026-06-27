from datetime import datetime, timezone
from typing import Literal
from uuid import uuid4

from pydantic import BaseModel, Field

CustomToolType = Literal["http", "mcp"]


class CustomToolBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=120, pattern=r"^[a-z][a-z0-9_]*$")
    description: str = Field(..., min_length=1)
    tool_type: CustomToolType
    config: dict = Field(default_factory=dict)
    is_active: bool = True


class CustomToolCreate(CustomToolBase):
    """Payload for registering a custom tool."""


class CustomToolUpdate(BaseModel):
    description: str | None = Field(default=None, min_length=1)
    config: dict | None = None
    is_active: bool | None = None


class CustomTool(CustomToolBase):
    id: str
    owner_id: str
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_create(cls, data: CustomToolCreate) -> "CustomTool":
        now = datetime.now(timezone.utc)
        return cls(
            id=str(uuid4()),
            created_at=now,
            updated_at=now,
            **data.model_dump(),
        )