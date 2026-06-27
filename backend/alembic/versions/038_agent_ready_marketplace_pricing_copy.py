"""Agent-Ready marketplace pricing copy + live client proof links

Revision ID: 038_marketplace_pricing
Revises: 037_agent_ready_phase3
Create Date: 2026-06-22

"""
import json
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "038_marketplace_pricing"
down_revision: Union[str, Sequence[str], None] = "037_agent_ready_phase3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

AI_VISIBILITY_ID = "33333333-3333-4333-8333-333333333301"
FIX_BOT_ID = "33333333-3333-4333-8333-333333333309"
AUTO_FIX_ID = "33333333-3333-4333-8333-333333333310"

SHOWCASE_CASTING_FIX = "55555555-5555-4555-8555-555555555515"
SHOWCASE_PINPOINT_VIS = "55555555-5555-4555-8555-555555555503"
SHOWCASE_PINPOINT_FIX = "55555555-5555-4555-8555-555555555516"

PROOF_SUCCESSCASTING = "https://aibotauth.com/proof/successcasting-com-8bb891af45a6"
PROOF_PINPOINT = "https://aibotauth.com/proof/pinpointaccountingservice-com-c902cb05afc4"

AI_VISIBILITY_DESC = (
    "$2.50/run — agency-grade AI visibility audit with deterministic AIBotAuth scan, "
    "Claude audit, Gemini fix pack, and Grok QA. Every run includes a public proof badge. "
    "Live clients: successcasting.com and pinpointaccountingservice.com (88/100 proof on file)."
)

FIX_BOT_DESC = (
    "Free Agent-Ready scan — isitagentready.com-style scorecard, P0/P1/P2 fixes, "
    "paste-ready robots.txt, llms.txt, agents.txt, and a shareable AIBotAuth proof URL. "
    "Verified on successcasting.com and pinpointaccountingservice.com. "
    "Upgrade to Auto Fix Pro ($9.99) for full Level-5 deploy pack."
)

AUTO_FIX_DESC = (
    "$9.99/run — Agent-Ready Auto Fix Pro: gap map, full deploy pack (robots, llms, protocol, "
    "commerce layer), stack deploy guide, and re-verify checklist. Includes proof badge. "
    "Reference: successcasting.com 25%→100% Level 5. Live proof: Pinpoint Accounting 88/100."
)

FIX_BOT_CREW = {
    "input_mode": "url",
    "pipeline_label": "Scan → Audit → Fix Pack → QA",
    "run_title": "Run Free Agent Scan",
    "run_cta": "Scan & Prove — Free",
    "run_hint": (
        "Free scan + public proof link. Live: successcasting.com & pinpointaccountingservice.com. "
        "Upgrade to Auto Fix Pro $9.99 for Level 5 pack."
    ),
    "upgrade_skill_id": AUTO_FIX_ID,
    "steps": [
        {"id": "scan", "type": "mcp", "tool": "mcp.aibotauth.scan", "title": "Agent-Ready Scan"},
        {"id": "analyze", "type": "llm", "model": "claude-sonnet-4-5-20250929", "title": "Fix Bot Auditor"},
        {"id": "improve", "type": "llm", "model": "gemini-2.5-flash", "title": "Fix Pack Generator"},
        {"id": "qa", "type": "llm", "model": "grok-3-mini", "title": "QA Gate"},
    ],
}

AUTO_FIX_CREW = {
    "input_mode": "url",
    "pipeline_label": "Scan → Gap Map → Fix Pack → Deploy → Verify → QA",
    "run_title": "Run Agent-Ready Auto Fix",
    "run_cta": "Fix to Level 5 — $9.99",
    "run_hint": (
        "Full Level-5 pack + proof badge. Clients on file: successcasting.com & pinpointaccountingservice.com."
    ),
    "upgrade_skill_id": None,
    "steps": [
        {"id": "scan", "type": "mcp", "tool": "mcp.aibotauth.scan", "title": "Agent-Ready Scan"},
        {"id": "analyze", "type": "llm", "model": "claude-sonnet-4-5-20250929", "title": "Gap Mapper"},
        {"id": "improve", "type": "llm", "model": "gemini-2.5-flash", "title": "Auto Fix Pack"},
        {"id": "qa", "type": "llm", "model": "grok-3-mini", "title": "Deploy QA"},
    ],
}

PINPOINT_FIX_HIGHLIGHTS = [
    "88/100 proof on file",
    "llms.txt Markdown links",
    "Content-Signal ai-input=yes",
    "Free $0 scan + proof URL",
]

PINPOINT_FIX_DELIVERABLES = [
    "Agent-ready scorecard",
    "P0/P1/P2 fix list",
    "robots.txt + llms.txt + agents.txt",
    "Public proof URL",
    "isitagentready verify link",
]


def _sql_json(obj: dict) -> str:
    return json.dumps(obj).replace("'", "''")


def upgrade() -> None:
    op.execute(
        f"""
        UPDATE expert_skills
        SET description = '{AI_VISIBILITY_DESC.replace("'", "''")}'
        WHERE id = '{AI_VISIBILITY_ID}'
        """
    )
    op.execute(
        f"""
        UPDATE expert_skills
        SET description = '{FIX_BOT_DESC.replace("'", "''")}',
            crew_config = '{_sql_json(FIX_BOT_CREW)}'::jsonb
        WHERE id = '{FIX_BOT_ID}'
        """
    )
    op.execute(
        f"""
        UPDATE expert_skills
        SET description = '{AUTO_FIX_DESC.replace("'", "''")}',
            crew_config = '{_sql_json(AUTO_FIX_CREW)}'::jsonb
        WHERE id = '{AUTO_FIX_ID}'
        """
    )

    op.execute(
        f"""
        UPDATE skill_showcases
        SET title = 'successcasting.com — 88/100 proof',
            summary = 'Live OBOLLA client. Agent-Ready scan + public proof badge. '
                      'Reference path from WAF/401 to full isitagentready pass and Level 5 deploy.',
            metric_label = 'Proof score',
            metric_value = '88/100',
            highlights = '["88/100 AIBotAuth proof", "Level 5 deploy reference", "Public proof URL", "Free scan entry"]'::jsonb
        WHERE id = '{SHOWCASE_CASTING_FIX}'
        """
    )

    op.execute(
        f"""
        UPDATE skill_showcases
        SET summary = summary || ' Public proof: {PROOF_PINPOINT.replace("'", "''")} (88/100).',
            highlights = '["58 → 82 projected", "88/100 live proof", "llms.txt Markdown", "Content-Signal"]'::jsonb
        WHERE id = '{SHOWCASE_PINPOINT_VIS}'
        """
    )

    showcases = sa.table(
        "skill_showcases",
        sa.column("id", postgresql.UUID),
        sa.column("expert_skill_id", postgresql.UUID),
        sa.column("title", sa.String),
        sa.column("site_name", sa.String),
        sa.column("site_url", sa.String),
        sa.column("summary", sa.Text),
        sa.column("metric_label", sa.String),
        sa.column("metric_value", sa.String),
        sa.column("highlights", postgresql.JSONB),
        sa.column("sort_order", sa.Integer),
        sa.column("is_featured", sa.Boolean),
        sa.column("is_active", sa.Boolean),
        sa.column("sample_output", sa.Text),
        sa.column("deliverables", postgresql.JSONB),
        sa.column("stats", postgresql.JSONB),
        sa.column("before_after", postgresql.JSONB),
    )
    op.bulk_insert(
        showcases,
        [
            {
                "id": SHOWCASE_PINPOINT_FIX,
                "expert_skill_id": FIX_BOT_ID,
                "title": "pinpointaccountingservice.com — live proof",
                "site_name": "Pinpoint Accounting",
                "site_url": "https://pinpointaccountingservice.com",
                "summary": (
                    "Live OBOLLA client — Thai accounting services site. Free Agent-Ready scan "
                    "produced 88/100 proof, llms.txt Markdown links, and Content-Signal alignment. "
                    f"Proof: {PROOF_PINPOINT}"
                ),
                "metric_label": "Proof score",
                "metric_value": "88/100",
                "highlights": PINPOINT_FIX_HIGHLIGHTS,
                "sort_order": 1,
                "is_featured": True,
                "is_active": True,
                "sample_output": (
                    f"## Agent-Ready Proof\nPublic URL: {PROOF_PINPOINT}\n"
                    "Overall: 88/100 (B) — deterministic AIBotAuth + isitagentready rubric.\n"
                    "## Fixes shipped\n- llms.txt Markdown links\n- Content-Signal ai-input=yes\n"
                    "- www CDN custom domain\n- Hero LCP / scroll-reveal\n"
                ),
                "deliverables": PINPOINT_FIX_DELIVERABLES,
                "stats": {
                    "score": "88/100 proof",
                    "time_saved": "~3 hours vs manual",
                    "deliverables_count": "5+ files",
                    "runtime": "2–4 minutes",
                },
                "before_after": {
                    "score_before": "58/100 (audit)",
                    "score_after": "88/100 proof",
                    "proof_url": PROOF_PINPOINT,
                },
            }
        ],
    )


def downgrade() -> None:
    op.execute(f"DELETE FROM skill_showcases WHERE id = '{SHOWCASE_PINPOINT_FIX}'")