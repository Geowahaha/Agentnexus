"""SuccessCasting showcase — isitagentready 100% Level 5 Agent-Native

Revision ID: 034_successcasting_honest
Revises: 033_successcasting_scores
Create Date: 2026-06-21

"""
import json
from typing import Sequence, Union

from alembic import op

revision: str = "034_successcasting_honest"
down_revision: Union[str, Sequence[str], None] = "033_successcasting_scores"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

SHOWCASE_ID = "55555555-5555-4555-8555-555555555515"

BEFORE_AFTER = {
    "score_before": "25%",
    "score_after": "100%",
    "category_scores": {
        "before": {
            "discoverability": 25,
            "content": 0,
            "bot_access": 25,
            "protocol": 0,
            "commerce": 0,
            "overall": 25,
        },
        "after": {
            "discoverability": 100,
            "content": 100,
            "bot_access": 100,
            "protocol": 100,
            "commerce": 100,
            "overall": 100,
        },
        "isitagentready_all_checks": {
            "pass": 20,
            "fail": 0,
            "overall": 100,
            "level": 5,
            "level_name": "Agent-Native",
            "verified_at": "2026-06-21T08:41:31Z",
            "verify_url": "https://isitagentready.com/",
            "ui_categories": {
                "discoverability": "4/4",
                "content": "1/1",
                "bot_access": "2/2",
                "api_auth_mcp": "7/7",
                "commerce": "Optional 100%",
            },
        },
    },
    "bots": [
        {"name": "GPTBot", "before": "200, no Content-Signal", "after": "200 + policy header"},
        {"name": "ClaudeBot", "before": "200, no Content-Signal", "after": "200 + policy header"},
        {"name": "PerplexityBot", "before": "200, no Content-Signal", "after": "200 + policy header"},
        {"name": "OAI-SearchBot", "before": "200, no Content-Signal", "after": "200 + policy header"},
        {"name": "ChatGPT-User", "before": "200, no Content-Signal", "after": "200 + policy header"},
        {"name": "Google-Extended", "before": "200, no Content-Signal", "after": "200 + policy header"},
    ],
    "fixes_applied": [
        "agents.txt published (404 → 200)",
        "Content-Signal header on public routes",
        "Content-Signal line in robots.txt body (under User-agent: *)",
        "RFC Link headers — api-catalog, service-doc, describedby, sitemap",
        "/.well-known/api-catalog (RFC 9727 linkset)",
        "/.well-known/agent-skills/index.json",
        "llms.txt — Markdown links + agents.txt link",
        "Markdown negotiation — Accept: text/markdown",
        "robots.txt — Applebot + full AI crawler roster",
        "DNS-AID SVCB/HTTPS records at _index._agents.www",
        "OAuth/OIDC discovery + auth.md + protected resource metadata",
        "MCP Server Card + A2A Agent Card (AP2 extension)",
        "WebMCP — 2 imperative_api tools on RFQ form",
        "Commerce UCP (/.well-known/ucp) + ACP (/.well-known/acp.json)",
        "MPP — openapi.json with 3 x-payment-info operations",
        "x402 v2 — GET /api/v1 returns 402 + PAYMENT-REQUIRED header (Base Sepolia USDC)",
    ],
    "remaining_gaps": [],
    "snapshots": {
        "before_file": "references/successcasting-before.json",
        "after_file": "references/successcasting-after.json",
        "case_study": "Succescasting.com case study/CASE-STUDY-100.md",
        "screenshot": "Succescasting.com case study/Screenshot 2026-06-21 141258 after3 100%.png",
        "audit_script": "scripts/audit-agent-ready.mjs",
        "fix_generator": "scripts/agent-ready-fix-generator.mjs",
        "isitagentready_api": "POST https://isitagentready.com/api/scan",
    },
}

SAMPLE_OUTPUT = """## Scorecard (isitagentready.com — live 2026-06-21 15:41 ICT)

| Category | Score |
|----------|-------|
| **Overall** | **100** — Level 5 Agent-Native |
| Discoverability | 100 (4/4) |
| Content | 100 (1/1) |
| Bot Access Control | 100 (2/2) |
| API, Auth, MCP & Skill Discovery | 100 (7/7) |
| Commerce | 100 (Optional) |

Before: ~25% (OBOLLA snapshot, Feb 2026)
After: **100%** — full protocol + commerce stack

Reference screenshot: Succescasting.com case study/Screenshot 2026-06-21 141258 after3 100%.png

Verify: https://isitagentready.com/"""


def upgrade() -> None:
    before_after_json = json.dumps(BEFORE_AFTER).replace("'", "''")
    sample = SAMPLE_OUTPUT.replace("'", "''")
    op.execute(
        f"""
        UPDATE skill_showcases
        SET title = 'successcasting.com — 100% Agent-Native',
            metric_label = 'isitagentready All Checks',
            metric_value = '25% → 100%',
            summary = 'Production case study: content site to Level 5 Agent-Native (100/100). All 5 categories pass including Commerce x402 UCP ACP MPP AP2.',
            highlights = '["25%% → 100%% isitagentready", "Level 5 Agent-Native", "Commerce 5/5", "DNS-AID + OAuth + MCP + x402"]'::jsonb,
            stats = '{{"score": "25%% → 100%%", "time_saved": "~8 hours", "deliverables_count": "25+ files", "runtime": "2–4 min"}}'::jsonb,
            before_after = '{before_after_json}'::jsonb,
            sample_output = '{sample}'
        WHERE id = '{SHOWCASE_ID}'
        """
    )


def downgrade() -> None:
    pass