"""Community case studies seed + Fable-5 Pro before/after metrics

Revision ID: 025_community_cases
Revises: 024_fable5_credits
Create Date: 2026-06-20

"""
import json
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "025_community_cases"
down_revision: Union[str, Sequence[str], None] = "024_fable5_credits"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

AI_VISIBILITY_SKILL = "33333333-3333-4333-8333-333333333301"
SEO_SKILL = "33333333-3333-4333-8333-333333333302"
FREE_SKILL = "33333333-3333-4333-8333-333333333303"
PREMIUM_SKILL = "33333333-3333-4333-8333-333333333304"

PREMIUM_SHOWCASE_ID = "55555555-5555-4555-8555-555555555506"
SHOWCASE_OBOLLA_ID = "55555555-5555-4555-8555-555555555507"
SHOWCASE_NONPROFIT_ID = "55555555-5555-4555-8555-555555555508"
SHOWCASE_CRON_ID = "55555555-5555-4555-8555-555555555509"
SHOWCASE_RETRY_ID = "55555555-5555-4555-8555-555555555510"

PREMIUM_BEFORE_AFTER = {
    "score_before": "Sketch only — no tests (~2.5 hrs)",
    "score_after": "READY — plan + code + review (4 min)",
    "bots": [],
    "fixes_applied": [
        "Exploration mapped 6 files + Stripe docs",
        "Webhook idempotency + signature verification",
        "pytest suite with mocked Stripe events",
        "Grok review 9/10 — P2 nit patched",
        "QA gate READY + deploy checklist",
    ],
}

PREMIUM_STATS = {
    "score": "READY",
    "time_saved": "~2.5 hours vs solo coding",
    "deliverables_count": "Plan + code + review + QA",
    "runtime": "4 minutes",
    "engines": "GPT-4.1 + Grok 3 Mini",
    "cost": "$5 run + ~$0.18 LLM",
}

OBOLLA_BEFORE_AFTER = {
    "score_before": "62/100",
    "score_after": "88/100",
    "bots": [
        {"name": "GPTBot", "before": "served", "after": "can read"},
        {"name": "ClaudeBot", "before": "blocked", "after": "can read"},
        {"name": "PerplexityBot", "before": "served", "after": "can read"},
    ],
    "fixes_applied": [
        "llms.txt with creator charter + skill catalog",
        "robots.txt explicit AI crawler policy",
        "Organization JSON-LD on homepage",
        "Community manifesto in semantic HTML",
    ],
}

NONPROFIT_BEFORE_AFTER = {
    "score_before": "41/100 technical SEO",
    "score_after": "76/100 — 90-day plan",
    "bots": [],
    "fixes_applied": [
        "Core Web Vitals: LCP 4.2s → 2.1s (hero image)",
        "Missing meta descriptions on 12 key pages",
        "LocalBusiness schema for 3 service areas",
        "Content gap: 8 FAQ pages for donor intent",
    ],
}

CRON_BEFORE_AFTER = {
    "score_before": "TODO comment — no monitor",
    "score_after": "READY — cron + alert tests",
    "bots": [],
    "fixes_applied": [
        "APScheduler job with health ping",
        "Slack webhook on 2 consecutive failures",
        "Unit tests with freezegun time mocks",
        "Local LoRA review: 8/10",
    ],
}

RETRY_BEFORE_AFTER = {
    "score_before": "Fragile retries — no DLQ",
    "score_after": "READY — idempotent queue",
    "bots": [],
    "fixes_applied": [
        "Exponential backoff + jitter (max 5 attempts)",
        "Dead-letter queue table + admin replay",
        "Integration tests with Redis faker",
        "Pro review caught race on concurrent workers",
    ],
}


def upgrade() -> None:
    op.execute(
        sa.text(
            """
            UPDATE skill_showcases
            SET before_after = CAST(:before_after AS jsonb),
                stats = CAST(:stats AS jsonb),
                metric_label = :metric_label,
                metric_value = :metric_value,
                summary = :summary
            WHERE id = CAST(:showcase_id AS uuid)
            """
        ).bindparams(
            before_after=json.dumps(PREMIUM_BEFORE_AFTER),
            stats=json.dumps(PREMIUM_STATS),
            metric_label="Before → After",
            metric_value="2.5 hrs → 4 min READY",
            summary=(
                "Measurable Pro run: GPT-4.1 + Grok 3 Mini turned a vague Stripe webhook "
                "note into production code with tests — $5/run, ~4 minutes, QA READY."
            ),
            showcase_id=PREMIUM_SHOWCASE_ID,
        )
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
                "id": SHOWCASE_OBOLLA_ID,
                "expert_skill_id": AI_VISIBILITY_SKILL,
                "title": "OBOLLA.com — agent-ready community home",
                "site_name": "OBOLLA",
                "site_url": "https://obolla.com",
                "summary": (
                    "We eat our own cooking: AI Visibility Audit on obolla.com so agents "
                    "can discover creator flows, charter rules, and community DNA."
                ),
                "metric_label": "Visibility score",
                "metric_value": "62 → 88/100",
                "highlights": [
                    "llms.txt + charter",
                    "Community manifesto SEO",
                    "Creator skill catalog",
                    "Honest upstream credits",
                ],
                "sort_order": 2,
                "is_featured": True,
                "is_active": True,
                "sample_output": (
                    "## AIBotAuth Scan\n"
                    "Before: 62/100 — ClaudeBot blocked, sparse llms.txt\n\n"
                    "## Fix Pack\n"
                    "- llms.txt with Markdown skill links\n"
                    "- robots.txt AI crawler allowlist\n"
                    "- Organization JSON-LD\n\n"
                    "## After re-scan: 88/100"
                ),
                "deliverables": [
                    "5-layer visibility scorecard",
                    "llms.txt + robots.txt templates",
                    "JSON-LD snippets",
                    "Before/after bot access table",
                ],
                "stats": {
                    "score": "88/100",
                    "time_saved": "~4 hours vs manual audit",
                    "runtime": "4 minutes",
                    "deliverables_count": "Fix pack + QA",
                },
                "before_after": OBOLLA_BEFORE_AFTER,
            },
            {
                "id": SHOWCASE_NONPROFIT_ID,
                "expert_skill_id": SEO_SKILL,
                "title": "Community food bank — 90-day SEO plan",
                "site_name": "Harvest Hope",
                "site_url": "https://harvesthope.example",
                "summary": (
                    "SEO Expert Analysis for a volunteer-run nonprofit: technical fixes, "
                    "donor-intent content gaps, and a prioritized 90-day roadmap."
                ),
                "metric_label": "Technical SEO",
                "metric_value": "41 → 76/100",
                "highlights": [
                    "Core Web Vitals fixes",
                    "LocalBusiness schema",
                    "Donor FAQ content gaps",
                    "Impact forecast",
                ],
                "sort_order": 3,
                "is_featured": True,
                "is_active": True,
                "sample_output": (
                    "## Technical Scan\n"
                    "LCP 4.2s · CLS 0.18 · 12 pages missing meta\n\n"
                    "## Analyzer\n"
                    "P0: Hero image WebP + dimensions\n"
                    "P1: Donor landing FAQ cluster\n"
                    "P2: LocalBusiness schema × 3 regions\n\n"
                    "## Report: 90-day plan with impact forecast"
                ),
                "deliverables": [
                    "Technical SEO audit",
                    "Competitor gap analysis",
                    "90-day action plan",
                    "Schema + meta templates",
                ],
                "stats": {
                    "score": "76/100 projected",
                    "time_saved": "~6 hours vs agency brief",
                    "runtime": "5–8 minutes",
                    "deliverables_count": "7-step pipeline",
                },
                "before_after": NONPROFIT_BEFORE_AFTER,
            },
            {
                "id": SHOWCASE_CRON_ID,
                "expert_skill_id": FREE_SKILL,
                "title": "Cron health monitor — local LoRA shipped",
                "site_name": "Internal ops task",
                "site_url": "",
                "summary": (
                    "Free tier on hotdogs/qwen3.6-27b-fable5-lora: describe a missing cron "
                    "monitor; get plan, implementation, review, and QA on your GPU — $0."
                ),
                "metric_label": "QA verdict",
                "metric_value": "READY",
                "highlights": [
                    "Local LoRA all 4 steps",
                    "$0 run + $0 LLM",
                    "APScheduler + Slack alert",
                    "pytest + freezegun",
                ],
                "sort_order": 4,
                "is_featured": True,
                "is_active": True,
                "sample_output": (
                    "## Planner (qwen3.6-27b-fable5)\n"
                    "Goal: APScheduler job ping /health every 5m; Slack on 2 failures.\n\n"
                    "## Implementer\n"
                    "scheduler.py + tests/test_scheduler.py\n\n"
                    "## QA Gate: READY"
                ),
                "deliverables": [
                    "Exploration notes + plan",
                    "scheduler.py implementation",
                    "Local LoRA code review",
                    "QA checklist",
                ],
                "stats": {
                    "score": "READY",
                    "engines": "qwen3.6-27b-fable5 (Ollama)",
                    "runtime": "5–9 minutes (GPU)",
                    "time_saved": "~1.5 hours",
                },
                "before_after": CRON_BEFORE_AFTER,
            },
            {
                "id": SHOWCASE_RETRY_ID,
                "expert_skill_id": PREMIUM_SKILL,
                "title": "Payment retry queue — Pro cloud pipeline",
                "site_name": "SaaS billing task",
                "site_url": "",
                "summary": (
                    "Pro tier ($5): fragile payment retries became an idempotent queue with "
                    "DLQ, integration tests, and senior review — no GPU required."
                ),
                "metric_label": "Before → After",
                "metric_value": "Fragile → READY",
                "highlights": [
                    "GPT-4.1 implement",
                    "Grok 3 Mini review",
                    "DLQ + replay admin",
                    "Redis integration tests",
                ],
                "sort_order": 5,
                "is_featured": False,
                "is_active": True,
                "sample_output": (
                    "## Planner (GPT-4.1)\n"
                    "Map billing/worker.py; design retry queue + DLQ schema.\n\n"
                    "## Code Reviewer (Grok)\n"
                    "9/10 — fixed race on concurrent dequeue.\n\n"
                    "## QA: READY"
                ),
                "deliverables": [
                    "Architecture + step plan",
                    "queue.py + worker patches",
                    "Senior review + patches",
                    "Integration test suite",
                ],
                "stats": {
                    "score": "READY",
                    "engines": "GPT-4.1 + Grok 3 Mini",
                    "runtime": "5 minutes",
                    "cost": "$5 run + ~$0.18 LLM",
                    "time_saved": "~3 hours",
                },
                "before_after": RETRY_BEFORE_AFTER,
            },
        ],
    )


def downgrade() -> None:
    for sid in (
        SHOWCASE_OBOLLA_ID,
        SHOWCASE_NONPROFIT_ID,
        SHOWCASE_CRON_ID,
        SHOWCASE_RETRY_ID,
    ):
        op.execute(f"DELETE FROM skill_showcases WHERE id = '{sid}'")
    op.execute(
        sa.text(
            """
            UPDATE skill_showcases
            SET before_after = '{}'::jsonb,
                metric_label = 'QA verdict',
                metric_value = 'READY',
                summary = :summary,
                stats = CAST(:stats AS jsonb)
            WHERE id = CAST(:showcase_id AS uuid)
            """
        ).bindparams(
            summary=(
                "No GPU? Pro runs GPT-4.1 + Grok 3 Mini in the cloud. "
                "Deeper plans, complete files, strict review — $5/run marketplace fee."
            ),
            stats=json.dumps(
                {
                    "score": "READY",
                    "engines": "GPT-4.1 + Grok 3 Mini",
                    "runtime": "3–6 minutes",
                }
            ),
            showcase_id=PREMIUM_SHOWCASE_ID,
        )
    )