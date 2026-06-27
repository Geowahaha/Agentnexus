"""AI Visibility Audit 2026 marketplace polish — price, showcases, before_after

Revision ID: 017_ai_visibility_2026
Revises: 016_google_auth
Create Date: 2026-06-18

"""
import json
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "017_ai_visibility_2026"
down_revision: Union[str, Sequence[str], None] = "016_google_auth"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

EXPERT_SKILL_ID = "33333333-3333-4333-8333-333333333301"
SHOWCASE_AIBOTAUTH_ID = "55555555-5555-4555-8555-555555555501"
SHOWCASE_CASTING_ID = "55555555-5555-4555-8555-555555555502"
SHOWCASE_PINPOINT_ID = "55555555-5555-4555-8555-555555555503"

SKILL_DESCRIPTION = (
    "Deep-scan any website for AI bot readability. Get a scored audit, prioritized issues, "
    "and paste-ready robots.txt, llms.txt, and JSON-LD — plus QA-verified recommendations "
    "you can deploy today."
)

CAPABILITIES = [
    "seo",
    "aeo",
    "geo",
    "ai-visibility",
    "agent-readiness",
    "fix-pack",
    "robots-txt",
    "llms-txt",
    "json-ld",
    "content-signals",
]

AIBOTAUTH_BEFORE_AFTER = {
    "score_before": "71/100",
    "score_after": "85/100",
    "bots": [
        {"name": "GPTBot", "before": "served", "after": "can read"},
        {"name": "ClaudeBot", "before": "served", "after": "can read"},
        {"name": "PerplexityBot", "before": "blocked", "after": "can read"},
        {"name": "OAI-SearchBot", "before": "served", "after": "can read"},
        {"name": "Google-Extended", "before": "served", "after": "can read"},
    ],
    "fixes_applied": [
        "Explicit AI crawler rules in robots.txt",
        "llms.txt with Markdown links",
        "Organization + WebSite JSON-LD",
        "Content-Signal: search=yes, ai-input=yes",
    ],
}

PINPOINT_BEFORE_AFTER = {
    "score_before": "58/100",
    "score_after": "82/100",
    "bots": [
        {"name": "GPTBot", "before": "served", "after": "can read"},
        {"name": "ClaudeBot", "before": "served", "after": "can read"},
        {"name": "PerplexityBot", "before": "served", "after": "can read"},
        {"name": "OAI-SearchBot", "before": "blocked", "after": "can read"},
    ],
    "fixes_applied": [
        "llms.txt: bare URLs → 27 Markdown links",
        "Content-Signal ai-input=yes in robots.txt + _headers",
        "www subdomain HTTP 522 → 200",
        "Hero LCP: removed scroll-reveal on above-fold copy",
        "JSON-LD moved to end of body",
    ],
}

CASTING_BEFORE_AFTER = {
    "score_before": "Limited (WAF)",
    "score_after": "Full scan after WAF allowlist",
    "bots": [
        {"name": "GPTBot", "before": "blocked (401)", "after": "can read"},
        {"name": "ClaudeBot", "before": "blocked (401)", "after": "can read"},
        {"name": "PerplexityBot", "before": "blocked (401)", "after": "can read"},
    ],
    "fixes_applied": [
        "WAF allowlist for scanner UAs",
        "robots.txt AI crawler policy",
        "llms.txt publication",
        "Deferred analytics for faster LCP",
    ],
}

PINPOINT_SAMPLE = """## AIBotAuth Scan (before fixes)
Layer scores: Discovery 14/20 · Access 12/20 · Structure 11/20 · Trust 10/20 · Agent-ready 11/20
Overall: 58/100 — access and structure gaps limit AI citations

## Auditor (excerpt)
P0: www.pinpointaccountingservice.com returns HTTP 522 — fix CDN custom domain.
P1: llms.txt uses bare URLs; convert to Markdown links for agent parsers.
P1: Missing Content-Signal ai-input=yes — agents cannot use content at inference.
P2: Hero copy hidden by scroll-reveal — scanners see empty paragraphs (LCP/Structure hit).

## Fix Pack Generator
- robots.txt — explicit AI bots + Content-Signal: search=yes, ai-input=yes, ai-train=no
- llms.txt — 27 Markdown links to key service pages
- JSON-LD — LocalBusiness + ProfessionalService graph
- _headers — Cloudflare Content-Signal + security headers

## QA Challenger
PASS: llms.txt Markdown syntax · PASS: no secrets in output · PASS: P0 www fix documented
Verdict: READY — projected 82/100 after deploy"""

PINPOINT_STATS = {
    "score": "58 → 82/100",
    "time_saved": "~4 hours vs manual audit",
    "deliverables_count": "4 files",
    "runtime": "3–5 minutes",
}

AIBOTAUTH_SAMPLE = """## AIBotAuth Scan
Layer scores: Discovery 18/20 · Access 17/20 · Structure 16/20 · Trust 15/20 · Agent-ready 19/20
Overall: 85/100 — strong agent visibility baseline

## Bot status (after fixes)
| Bot | Before | After |
|---|---|---|
| GPTBot | served | can read |
| PerplexityBot | blocked | can read |
| ClaudeBot | served | can read |

## Fix Pack Generator
- robots.txt — allow AI crawlers, Content-Signal, sitemap
- llms.txt — Markdown links, site purpose, API docs
- JSON-LD — Organization schema
- _headers — security + Content-Signal template

## QA Challenger
All checklist items PASS. Verdict: READY"""


def upgrade() -> None:
    op.add_column(
        "skill_showcases",
        sa.Column("before_after", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="{}"),
    )

    caps_json = json.dumps(CAPABILITIES).replace("'", "''")
    op.execute(
        f"""
        UPDATE expert_skills
        SET price_usd_per_run = 2.5000,
            description = '{SKILL_DESCRIPTION.replace("'", "''")}',
            capabilities = '{caps_json}'::jsonb
        WHERE id = '{EXPERT_SKILL_ID}'
        """
    )

    aibotauth_ba = json.dumps(AIBOTAUTH_BEFORE_AFTER).replace("'", "''")
    casting_ba = json.dumps(CASTING_BEFORE_AFTER).replace("'", "''")
    pinpoint_ba = json.dumps(PINPOINT_BEFORE_AFTER).replace("'", "''")

    op.execute(
        f"""
        UPDATE skill_showcases
        SET metric_label = 'Visibility score',
            metric_value = '85/100',
            before_after = '{aibotauth_ba}'::jsonb,
            sample_output = '{AIBOTAUTH_SAMPLE.replace("'", "''")}'
        WHERE id = '{SHOWCASE_AIBOTAUTH_ID}'
        """
    )

    op.execute(
        f"""
        UPDATE skill_showcases
        SET title = 'WAF unblock — full audit unlocked',
            summary = 'SuccessCasting initially blocked scanners with HTTP 401. After WAF allowlist '
                      'and policy files, the same skill delivers a full scorecard and deployable fix pack.',
            metric_label = 'Scan result',
            metric_value = '401 blocked → full audit',
            highlights = '["WAF allowlist fix", "Before/after bot status", "Same $2.50 run", "Honest partial-scan path"]'::jsonb,
            before_after = '{casting_ba}'::jsonb,
            stats = '{{"score": "401 → full scan", "time_saved": "~3 hours", "deliverables_count": "5 files", "runtime": "3–5 min"}}'::jsonb
        WHERE id = '{SHOWCASE_CASTING_ID}'
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
                "id": SHOWCASE_PINPOINT_ID,
                "expert_skill_id": EXPERT_SKILL_ID,
                "title": "llms.txt + Content-Signal — measurable lift",
                "site_name": "Pinpoint Accounting",
                "site_url": "https://pinpointaccountingservice.com",
                "summary": (
                    "Real client audit: bare URLs in llms.txt, missing ai-input signal, www 522, "
                    "and LCP issues from scroll-reveal. One skill run produced paste-ready fixes "
                    "and a clear before/after bot status table."
                ),
                "metric_label": "Score improvement",
                "metric_value": "58 → 82/100",
                "highlights": [
                    "llms.txt Markdown links",
                    "Content-Signal ai-input=yes",
                    "www 522 fixed",
                    "Bot status before/after",
                ],
                "sort_order": 2,
                "is_featured": True,
                "is_active": True,
                "sample_output": PINPOINT_SAMPLE,
                "deliverables": [
                    "5-layer visibility scorecard",
                    "P0/P1/P2 prioritized fixes",
                    "robots.txt with Content-Signal",
                    "llms.txt with Markdown links",
                    "JSON-LD + _headers templates",
                ],
                "stats": PINPOINT_STATS,
                "before_after": PINPOINT_BEFORE_AFTER,
            }
        ],
    )


def downgrade() -> None:
    op.execute(f"DELETE FROM skill_showcases WHERE id = '{SHOWCASE_PINPOINT_ID}'")
    op.drop_column("skill_showcases", "before_after")
    op.execute(
        f"""
        UPDATE expert_skills
        SET price_usd_per_run = 4.9900,
            capabilities = '["seo", "aeo", "geo", "agent-readiness", "fix-pack"]'::jsonb
        WHERE id = '{EXPERT_SKILL_ID}'
        """
    )