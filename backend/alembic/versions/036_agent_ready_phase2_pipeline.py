"""Agent-Ready Auto Fix — Phase 2 pipeline (stack detect + verify loop)

Revision ID: 036_agent_ready_phase2
Revises: 035_agent_ready_auto_fix
Create Date: 2026-06-21

"""
import json
from typing import Sequence, Union

from alembic import op

revision: str = "036_agent_ready_phase2"
down_revision: Union[str, Sequence[str], None] = "035_agent_ready_auto_fix"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

EXPERT_SKILL_ID = "33333333-3333-4333-8333-333333333310"

CREW_CONFIG = {
    "input_mode": "url",
    "pipeline_label": "Scan → Gap Map → Fix Pack → Deploy Plan → Verify → QA",
    "run_title": "Run Agent-Ready Auto Fix",
    "run_cta": "Fix to Level 5 — $9.99",
    "run_hint": "Stack detect + fix pack + post-deploy verify loop (CF purge when configured)",
    "upgrade_skill_id": None,
    "steps": [
        {"id": "scan", "type": "mcp", "tool": "mcp.aibotauth.scan", "title": "Agent-Ready Scan"},
        {"id": "analyze", "type": "llm", "model": "claude-sonnet-4-5-20250929", "title": "Gap Mapper"},
        {"id": "improve", "type": "llm", "model": "gemini-2.5-flash", "title": "Auto Fix Pack"},
        {
            "id": "deploy_plan",
            "type": "agent_ready",
            "action": "analyze",
            "title": "Stack + Deploy Plan",
        },
        {
            "id": "verify",
            "type": "agent_ready",
            "action": "verify",
            "title": "Verify Loop",
            "target_percent": 95,
            "max_attempts": 3,
            "purge_between": True,
        },
        {"id": "qa", "type": "llm", "model": "grok-3-mini", "title": "Deploy QA"},
    ],
}


def upgrade() -> None:
    crew_json = json.dumps(CREW_CONFIG).replace("'", "''")
    op.execute(
        f"""
        UPDATE expert_skills
        SET crew_config = '{crew_json}'::jsonb,
            description = description || ' Phase 2: stack detector, Cloudflare purge adapter, isitagentready verify loop.'
        WHERE id = '{EXPERT_SKILL_ID}'
        """
    )


def downgrade() -> None:
    pass