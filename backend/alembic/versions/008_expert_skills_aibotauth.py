"""expert skills and aibotauth mcp seed

Revision ID: 008_expert_skills
Revises: 007_agent_portfolio
Create Date: 2026-06-17

"""
import json
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "008_expert_skills"
down_revision: Union[str, Sequence[str], None] = "007_agent_portfolio"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

SYSTEM_USER_ID = "00000000-0000-4000-8000-000000000001"
AIBOTAUTH_SERVER_ID = "22222222-2222-4222-8222-222222222201"
EXPERT_SKILL_ID = "33333333-3333-4333-8333-333333333301"

CREW_CONFIG = {
    "steps": [
        {"id": "scan", "type": "mcp", "tool": "mcp.aibotauth.scan", "title": "AIBotAuth Scan"},
        {"id": "analyze", "type": "llm", "model": "claude-sonnet-4-5-20250929", "title": "Auditor"},
        {"id": "improve", "type": "llm", "model": "gemini-2.5-flash", "title": "Fix Pack Generator"},
        {"id": "qa", "type": "llm", "model": "grok-3-mini", "title": "QA Challenger"},
    ]
}

MCP_TOOLS = [
    {
        "id": "44444444-4444-4444-8444-444444444401",
        "tool_name": "scan",
        "description": "4-layer AI visibility scorecard (deterministic rubric + optional LLM narrative).",
        "input_schema": {
            "type": "object",
            "properties": {
                "url": {"type": "string", "description": "Public website URL"},
                "lang": {"type": "string", "enum": ["th", "en"]},
            },
            "required": ["url"],
        },
    },
    {
        "id": "44444444-4444-4444-8444-444444444402",
        "tool_name": "tech_audit",
        "description": "Security headers and semantic structure audit.",
        "input_schema": {
            "type": "object",
            "properties": {"url": {"type": "string"}, "lang": {"type": "string"}},
            "required": ["url"],
        },
    },
    {
        "id": "44444444-4444-4444-8444-444444444403",
        "tool_name": "bot_intel",
        "description": "AI bot intelligence loop for crawler access.",
        "input_schema": {
            "type": "object",
            "properties": {"url": {"type": "string"}, "lang": {"type": "string"}},
            "required": ["url"],
        },
    },
]


def upgrade() -> None:
    op.create_table(
        "expert_skills",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("slug", sa.String(length=120), nullable=False, unique=True),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("category", sa.String(length=80), nullable=True),
        sa.Column("pack_slug", sa.String(length=120), nullable=False),
        sa.Column("crew_config", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="{}"),
        sa.Column("capabilities", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="[]"),
        sa.Column("price_usd_per_run", sa.Numeric(12, 4), nullable=False, server_default="0"),
        sa.Column(
            "owner_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )

    mcp_servers = sa.table(
        "mcp_servers",
        sa.column("id", postgresql.UUID),
        sa.column("name", sa.String),
        sa.column("description", sa.Text),
        sa.column("owner_id", postgresql.UUID),
        sa.column("transport", sa.String),
        sa.column("config", postgresql.JSONB),
        sa.column("is_active", sa.Boolean),
    )
    op.bulk_insert(
        mcp_servers,
        [
            {
                "id": AIBOTAUTH_SERVER_ID,
                "name": "aibotauth",
                "description": "AIBotAuth AI visibility scanner — deterministic scores via MCP HTTP JSON-RPC.",
                "owner_id": SYSTEM_USER_ID,
                "transport": "http",
                "config": {"url": "https://aibotauth.com/api/mcp"},
                "is_active": True,
            }
        ],
    )

    mcp_tools = sa.table(
        "mcp_tools",
        sa.column("id", postgresql.UUID),
        sa.column("mcp_server_id", postgresql.UUID),
        sa.column("tool_name", sa.String),
        sa.column("qualified_name", sa.String),
        sa.column("description", sa.Text),
        sa.column("input_schema", postgresql.JSONB),
        sa.column("is_active", sa.Boolean),
    )
    op.bulk_insert(
        mcp_tools,
        [
            {
                "id": tool["id"],
                "mcp_server_id": AIBOTAUTH_SERVER_ID,
                "tool_name": tool["tool_name"],
                "qualified_name": f"mcp.aibotauth.{tool['tool_name']}",
                "description": tool["description"],
                "input_schema": tool["input_schema"],
                "is_active": True,
            }
            for tool in MCP_TOOLS
        ],
    )

    expert_skills = sa.table(
        "expert_skills",
        sa.column("id", postgresql.UUID),
        sa.column("slug", sa.String),
        sa.column("name", sa.String),
        sa.column("description", sa.Text),
        sa.column("category", sa.String),
        sa.column("pack_slug", sa.String),
        sa.column("crew_config", postgresql.JSONB),
        sa.column("capabilities", postgresql.JSONB),
        sa.column("price_usd_per_run", sa.Numeric),
        sa.column("owner_id", postgresql.UUID),
        sa.column("is_active", sa.Boolean),
    )
    op.bulk_insert(
        expert_skills,
        [
            {
                "id": EXPERT_SKILL_ID,
                "slug": "ai-visibility-2026",
                "name": "AI Visibility Audit 2026",
                "description": (
                    "Agency-grade AI visibility audit: AIBotAuth scan → Claude analysis → "
                    "Gemini fix pack → Grok QA. Enter a website URL and get deployable fixes."
                ),
                "category": "seo",
                "pack_slug": "ai-visibility-2026",
                "crew_config": CREW_CONFIG,
                "capabilities": ["seo", "aeo", "geo", "agent-readiness", "fix-pack"],
                "price_usd_per_run": "2.5000",
                "owner_id": SYSTEM_USER_ID,
                "is_active": True,
            }
        ],
    )


def downgrade() -> None:
    op.execute(f"DELETE FROM expert_skills WHERE id = '{EXPERT_SKILL_ID}'")
    op.execute(f"DELETE FROM mcp_tools WHERE mcp_server_id = '{AIBOTAUTH_SERVER_ID}'")
    op.execute(f"DELETE FROM mcp_servers WHERE id = '{AIBOTAUTH_SERVER_ID}'")
    op.drop_table("expert_skills")