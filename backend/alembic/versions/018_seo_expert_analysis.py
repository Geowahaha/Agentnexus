"""SEO Expert Analysis expert skill seed

Revision ID: 018_seo_expert
Revises: 017_ai_visibility_2026
Create Date: 2026-06-18

"""
import json
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "018_seo_expert"
down_revision: Union[str, Sequence[str], None] = "017_ai_visibility_2026"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

SYSTEM_USER_ID = "00000000-0000-4000-8000-000000000001"
EXPERT_SKILL_ID = "33333333-3333-4333-8333-333333333302"
SHOWCASE_CPE_ID = "55555555-5555-4555-8555-555555555504"

CREW_CONFIG = {
    "steps": [
        {
            "id": "tech_scan",
            "type": "mcp",
            "tool": "mcp.aibotauth.tech_audit",
            "title": "Technical Scan",
        },
        {
            "id": "visibility_scan",
            "type": "mcp",
            "tool": "mcp.aibotauth.scan",
            "title": "Site Visibility Scan",
        },
        {
            "id": "research",
            "type": "llm",
            "model": "gemini-2.5-flash",
            "title": "Researcher Agent",
        },
        {
            "id": "analyze",
            "type": "llm",
            "model": "claude-sonnet-4-5-20250929",
            "title": "Analyzer Agent",
        },
        {
            "id": "audit",
            "type": "llm",
            "model": "claude-sonnet-4-5-20250929",
            "title": "Auditor Agent",
        },
        {
            "id": "optimize",
            "type": "llm",
            "model": "gemini-2.5-flash",
            "title": "Optimizer Agent",
        },
        {
            "id": "report",
            "type": "llm",
            "model": "grok-3-mini",
            "title": "Report Generator",
        },
    ]
}

CAPABILITIES = [
    "seo",
    "technical-seo",
    "on-page",
    "competitor-analysis",
    "content-gap",
    "core-web-vitals",
    "schema",
    "action-plan",
    "impact-forecast",
]

DESCRIPTION = (
    "Professional SEO Expert Analysis: multi-agent competitor research, content gap analysis, "
    "technical SEO audit, Core Web Vitals assessment, and prioritized action plan with "
    "impact forecasts — delivered as a client-ready report."
)

CPE_BEFORE_AFTER = {
    "score_before": "32/100",
    "score_after": "68/100",
    "bots": [],
    "fixes_applied": [
        "LCP 15.8s → target <2.5s (hero image + render-blocking JS)",
        "Add meta descriptions on all indexable pages",
        "Fix heading hierarchy and image alt attributes",
        "Deploy Organization JSON-LD",
        "Quick-win internal linking on service pages",
    ],
}

CPE_SAMPLE = """## Executive Summary
Overall SEO Score: 32/100 (projected 68/100 after fixes)
- Technical: 12/25 — LCP 15.8s, TBT 2,870ms
- On-page: 14/25 — missing meta descriptions, heading issues
- Content: 11/20 — thin service pages vs competitors
- Performance: 3/15 — critical CWV failures
- Competitive: 8/15 — peers have deeper content hubs

## Top Quick Wins
1. Optimize LCP hero image (est. 15–25% mobile CTR lift)
2. Add unique meta descriptions (SEO +8–12 pts)
3. Fix crawlable link labels

## Competitor Gap
Regional foundry competitors publish material spec guides and case studies — CPE Foundry lacks equivalent depth.

## QA Verdict: READY"""

CPE_STATS = {
    "score": "32 → 68/100",
    "time_saved": "~6 hours vs agency audit",
    "deliverables_count": "Full report",
    "runtime": "5–8 minutes",
}


def upgrade() -> None:
    caps_json = json.dumps(CAPABILITIES).replace("'", "''")
    crew_json = json.dumps(CREW_CONFIG).replace("'", "''")

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
                "slug": "seo-expert-analysis",
                "name": "SEO Expert Analysis",
                "description": DESCRIPTION,
                "category": "seo",
                "pack_slug": "seo-expert-analysis",
                "crew_config": CREW_CONFIG,
                "capabilities": CAPABILITIES,
                "price_usd_per_run": "4.9900",
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
                "id": SHOWCASE_CPE_ID,
                "expert_skill_id": EXPERT_SKILL_ID,
                "title": "Foundry site — LCP + on-page gaps",
                "site_name": "CPE Foundry",
                "site_url": "https://www.cpefoundry.com",
                "summary": (
                    "Mobile Performance score 28, LCP 15.8s, missing meta descriptions. "
                    "SEO Expert Analysis identified competitor content gaps and a path from "
                    "32/100 to projected 68/100 with prioritized quick wins."
                ),
                "metric_label": "SEO score",
                "metric_value": "32 → 68/100",
                "highlights": [
                    "Competitor content gap",
                    "CWV impact forecast",
                    "Quick wins vs long-term",
                    "Client-ready report",
                ],
                "sort_order": 0,
                "is_featured": True,
                "is_active": True,
                "sample_output": CPE_SAMPLE,
                "deliverables": [
                    "Overall SEO scorecard",
                    "Competitor analysis table",
                    "Content gap report",
                    "Technical SEO audit",
                    "CWV assessment",
                    "Action plan with impact forecasts",
                ],
                "stats": CPE_STATS,
                "before_after": CPE_BEFORE_AFTER,
            }
        ],
    )


def downgrade() -> None:
    op.execute(f"DELETE FROM skill_showcases WHERE id = '{SHOWCASE_CPE_ID}'")
    op.execute(f"DELETE FROM expert_skills WHERE id = '{EXPERT_SKILL_ID}'")