"""Agent-Ready Auto Fix — Phase 3 deploy (GitHub PR + CF Pages direct upload)

Revision ID: 037_agent_ready_phase3
Revises: 036_agent_ready_phase2
Create Date: 2026-06-21

"""
import json
from typing import Sequence, Union

from alembic import op

revision: str = "037_agent_ready_phase3"
down_revision: Union[str, Sequence[str], None] = "036_agent_ready_phase2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

EXPERT_SKILL_ID = "33333333-3333-4333-8333-333333333310"

CREW_CONFIG = {
    "input_mode": "url",
    "pipeline_label": "Scan → Gap Map → Fix Pack → Deploy → Verify → QA",
    "run_title": "Run Agent-Ready Auto Fix",
    "run_cta": "Fix to Level 5 — $9.99",
    "run_hint": "Stack detect + fix pack + GitHub PR or CF Pages deploy + verify loop",
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
            "id": "deploy",
            "type": "agent_ready",
            "action": "deploy_github",
            "title": "GitHub PR Deploy",
            "optional": True,
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
            description = description || ' Phase 3: GitHub PR bot + Cloudflare Pages direct upload API.'
        WHERE id = '{EXPERT_SKILL_ID}'
        """
    )


def downgrade() -> None:
    pass