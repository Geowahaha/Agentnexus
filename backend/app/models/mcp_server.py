from datetime import datetime, timezone
from typing import Literal
from uuid import uuid4

from pydantic import BaseModel, Field

MCPTransport = Literal["sse", "stdio", "http"]


class MCPServerBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=120, pattern=r"^[a-z][a-z0-9_-]*$")
    description: str = Field(..., min_length=1)
    transport: MCPTransport
    config: dict = Field(default_factory=dict)
    is_active: bool = True


class MCPServerCreate(MCPServerBase):
    """Payload for registering an MCP server."""


class MCPServerUpdate(BaseModel):
    description: str | None = Field(default=None, min_length=1)
    transport: MCPTransport | None = None
    config: dict | None = None
    is_active: bool | None = None


class MCPServer(MCPServerBase):
    id: str
    owner_id: str
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_create(cls, data: MCPServerCreate) -> "MCPServer":
        now = datetime.now(timezone.utc)
        return cls(
            id=str(uuid4()),
            created_at=now,
            updated_at=now,
            **data.model_dump(),
        )


class MCPTool(BaseModel):
    id: str
    mcp_server_id: str
    tool_name: str
    qualified_name: str
    description: str
    input_schema: dict
    is_active: bool
    created_at: datetime
    updated_at: datetime