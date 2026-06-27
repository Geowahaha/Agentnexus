"""Fix Bot AI — free isitagentready-style agent scan

Revision ID: 032_fix_bot_ai_free
Revises: 031_lineart_public_names
Create Date: 2026-06-21

"""
import json
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "032_fix_bot_ai_free"
down_revision: Union[str, Sequence[str], None] = "031_lineart_public_names"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

SYSTEM_USER_ID = "00000000-0000-4000-8000-000000000001"
EXPERT_SKILL_ID = "33333333-3333-4333-8333-333333333309"
SHOWCASE_ID = "55555555-5555-4555-8555-555555555515"
AI_VISIBILITY_SKILL_ID = "33333333-3333-4333-8333-333333333301"

CREW_CONFIG = {
    "input_mode": "url",
    "pipeline_label": "Scan → Audit → Fix Pack → QA",
    "run_title": "Run Free Agent Scan",
    "run_cta": "Scan & Fix — Free",
    "run_hint": "Enter your site URL — same checks as isitagentready.com. Try successcasting.com",
    "upgrade_skill_id": AI_VISIBILITY_SKILL_ID,
    "steps": [
        {"id": "scan", "type": "mcp", "tool": "mcp.aibotauth.scan", "title": "Agent-Ready Scan"},
        {"id": "analyze", "type": "llm", "model": "claude-sonnet-4-5-20250929", "title": "Fix Bot Auditor"},
        {"id": "improve", "type": "llm", "model": "gemini-2.5-flash", "title": "Fix Pack Generator"},
        {"id": "qa", "type": "llm", "model": "grok-3-mini", "title": "QA Gate"},
    ],
}

CAPABILITIES = [
    "seo",
    "aeo",
    "geo",
    "ai-visibility",
    "agent-readiness",
    "fix-pack",
    "robots-txt",
    "llms-txt",
    "content-signals",
    "free-scan",
]

DESCRIPTION = (
    "Free Fix Bot AI scan — same agent-readiness checks as isitagentready.com. "
    "Enter a URL, get category scorecard, prioritized fixes, and paste-ready "
    "robots.txt, llms.txt, agents.txt, and Content-Signal headers. "
    "Example: successcasting.com."
)

BEFORE_AFTER = {
    "score_before": "Partial / gaps",
    "score_after": "Agent-ready pass",
    "bots": [
        {"name": "GPTBot", "before": "200 no Content-Signal", "after": "200 + policy header"},
        {"name": "ClaudeBot", "before": "200 no Content-Signal", "after": "200 + policy header"},
        {"name": "PerplexityBot", "before": "200 no Content-Signal", "after": "200 + policy header"},
        {"name": "OAI-SearchBot", "before": "200", "after": "200 + consistent policy"},
    ],
    "fixes_applied": [
        "agents.txt published (was 404)",
        "Content-Signal: ai-train=no, search=yes, ai-input=yes",
        "llms.txt — 27 Markdown links",
        "robots.txt — Applebot + AI crawlers",
        "Single H1 on homepage and /products",
        "WebMCP RFQ form hints",
    ],
}

SAMPLE_OUTPUT = """## Agent-Ready Scan (isitagentready-style)
Target: https://www.successcasting.com
Categories: Discoverability ✓ · Content ⚠ · Bot Access ⚠ · Protocol N/A · Commerce N/A
Overall: gaps in agents.txt + Content-Signal (see case study)

## Fix Bot Auditor
[P0] agents.txt 404 — Bot Access — agents cannot discover allowed paths
[P0] Missing Content-Signal header — Bot Access — policy not machine-readable
[P1] ai.txt ai-train=yes conflicts with desired opt-out — mixed training signal
[P1] llms.txt bare URLs — Discoverability — convert to Markdown links
[P2] Duplicate homepage H1 — Structure — carousel h1 → h2

## Fix Pack Generator
- robots.txt — AI bots + Applebot + Content-Signal + sitemap
- llms.txt — H1, 27 Markdown links, agents.txt link
- agents.txt — canonical www, allowed paths, ai-train=no policy
- ai.txt — aligned policy + Content-Signal
- next.config.ts / _headers — Content-Signal on HTML routes

## QA Gate
PASS: policy consistency · PASS: Markdown llms.txt · PASS: no fake MCP
Verdict: READY — verify at https://isitagentready.com/

Reference: successcasting.com before/after — likelyIssues [] post-deploy."""

SHOWCASE_STATS = {
    "score": "gaps → pass",
    "time_saved": "~3 hours vs manual scan + fixes",
    "deliverables_count": "5+ files",
    "runtime": "2–4 minutes",
}


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
                "slug": "fix-bot-ai-free",
                "name": "Fix Bot AI — Free Agent Scan",
                "description": DESCRIPTION,
                "category": "seo",
                "pack_slug": "fix-bot-ai-agent-ready",
                "crew_config": CREW_CONFIG,
                "capabilities": CAPABILITIES,
                "price_usd_per_run": "0.0000",
                "owner_id": SYSTEM_USER_ID,
                "is_active": True,
            }
        ],
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
                "id": SHOWCASE_ID,
                "expert_skill_id": EXPERT_SKILL_ID,
                "title": "successcasting.com — isitagentready pass",
                "site_name": "SuccessCasting",
                "site_url": "https://successcasting.com",
                "summary": (
                    "Real production fix: agents.txt, Content-Signal headers, llms.txt Markdown links, "
                    "and WebMCP hints. Audit likelyIssues cleared — same rubric as isitagentready.com."
                ),
                "metric_label": "Agent readiness",
                "metric_value": "gaps → pass",
                "highlights": [
                    "isitagentready.com checks",
                    "agents.txt + Content-Signal",
                    "27 Markdown llms links",
                    "Free $0 scan",
                ],
                "sort_order": 0,
                "is_featured": True,
                "is_active": True,
                "sample_output": SAMPLE_OUTPUT,
                "deliverables": [
                    "Category scorecard",
                    "P0/P1/P2 fix list",
                    "robots.txt + llms.txt + agents.txt",
                    "Content-Signal header snippet",
                    "isitagentready verify link",
                ],
                "stats": SHOWCASE_STATS,
                "before_after": BEFORE_AFTER,
            }
        ],
    )


def downgrade() -> None:
    op.execute(f"DELETE FROM skill_showcases WHERE id = '{SHOWCASE_ID}'")
    op.execute(f"DELETE FROM expert_skills WHERE id = '{EXPERT_SKILL_ID}'")