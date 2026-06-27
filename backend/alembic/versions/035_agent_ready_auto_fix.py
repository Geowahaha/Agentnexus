"""Agent-Ready Auto Fix Pro — paid marketplace skill

Revision ID: 035_agent_ready_auto_fix
Revises: 034_successcasting_honest
Create Date: 2026-06-21

"""
import json
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "035_agent_ready_auto_fix"
down_revision: Union[str, Sequence[str], None] = "034_successcasting_honest"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

SYSTEM_USER_ID = "00000000-0000-4000-8000-000000000001"
EXPERT_SKILL_ID = "33333333-3333-4333-8333-333333333310"
FIX_BOT_SKILL_ID = "33333333-3333-4333-8333-333333333309"

CREW_CONFIG = {
    "input_mode": "url",
    "pipeline_label": "Scan → Gap Map → Fix Pack → Deploy → QA",
    "run_title": "Run Agent-Ready Auto Fix",
    "run_cta": "Fix to Level 5 — $9.99",
    "run_hint": "Full isitagentready fix pack — successcasting.com went 25% → 100%",
    "upgrade_skill_id": None,
    "steps": [
        {"id": "scan", "type": "mcp", "tool": "mcp.aibotauth.scan", "title": "Agent-Ready Scan"},
        {"id": "analyze", "type": "llm", "model": "claude-sonnet-4-5-20250929", "title": "Gap Mapper"},
        {"id": "improve", "type": "llm", "model": "gemini-2.5-flash", "title": "Auto Fix Pack"},
        {"id": "qa", "type": "llm", "model": "grok-3-mini", "title": "Deploy QA"},
    ],
}

CAPABILITIES = [
    "seo",
    "aeo",
    "geo",
    "ai-visibility",
    "agent-readiness",
    "auto-fix",
    "fix-pack",
    "robots-txt",
    "llms-txt",
    "content-signals",
    "commerce-protocols",
    "mcp-discovery",
    "x402",
]

DESCRIPTION = (
    "Agent-Ready Auto Fix Pro — scan your URL with isitagentready.com taxonomy, "
    "generate full deployable fix pack (robots, llms, OAuth/MCP stubs, commerce layer), "
    "stack-specific deploy steps, and re-verify checklist. "
    "Reference: successcasting.com 25% → 100% Level 5 Agent-Native."
)


def upgrade() -> None:
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
                "slug": "agent-ready-auto-fix",
                "name": "Agent-Ready Auto Fix Pro",
                "description": DESCRIPTION,
                "category": "seo",
                "pack_slug": "agent-ready-auto-fix",
                "crew_config": CREW_CONFIG,
                "capabilities": CAPABILITIES,
                "price_usd_per_run": "9.9900",
                "owner_id": SYSTEM_USER_ID,
                "is_active": True,
            }
        ],
    )

    crew_json = json.dumps(
        {
            "input_mode": "url",
            "pipeline_label": "Scan → Audit → Fix Pack → QA",
            "run_title": "Run Free Agent Scan",
            "run_cta": "Scan & Fix — Free",
            "run_hint": "Free scan — upgrade to Auto Fix Pro for full Level 5 pack",
            "upgrade_skill_id": EXPERT_SKILL_ID,
            "steps": [
                {"id": "scan", "type": "mcp", "tool": "mcp.aibotauth.scan", "title": "Agent-Ready Scan"},
                {"id": "analyze", "type": "llm", "model": "claude-sonnet-4-5-20250929", "title": "Fix Bot Auditor"},
                {"id": "improve", "type": "llm", "model": "gemini-2.5-flash", "title": "Fix Pack Generator"},
                {"id": "qa", "type": "llm", "model": "grok-3-mini", "title": "QA Gate"},
            ],
        }
    ).replace("'", "''")

    op.execute(
        f"""
        UPDATE expert_skills
        SET crew_config = '{crew_json}'::jsonb
        WHERE id = '{FIX_BOT_SKILL_ID}'
        """
    )


def downgrade() -> None:
    op.execute(f"DELETE FROM expert_skills WHERE id = '{EXPERT_SKILL_ID}'")