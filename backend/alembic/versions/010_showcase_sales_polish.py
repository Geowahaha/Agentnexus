"""showcase sample output and skill price bump

Revision ID: 010_showcase_sales
Revises: 009_skill_showcases
Create Date: 2026-06-17

"""
from typing import Sequence, Union

import json

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "010_showcase_sales"
down_revision: Union[str, Sequence[str], None] = "009_skill_showcases"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

EXPERT_SKILL_ID = "33333333-3333-4333-8333-333333333301"
SHOWCASE_AIBOTAUTH_ID = "55555555-5555-4555-8555-555555555501"

SAMPLE_OUTPUT = """## AIBotAuth Scan
Layer scores (deterministic): Discovery 18/20 · Access 17/20 · Structure 16/20 · Trust 15/20 · Agent-ready 19/20
Overall: 85/100 — strong agent visibility baseline

## Auditor
P0: Publish llms.txt at /.well-known/llms.txt with allowed crawlers and contact.
P1: Add Organization + WebSite JSON-LD on homepage.
P1: Ensure robots.txt explicitly permits GPTBot, ClaudeBot, and PerplexityBot.
P2: Add security headers (CSP, X-Robots-Tag guidance for public docs).

## Fix Pack Generator
- robots.txt — allow AI crawlers, sitemap reference
- llms.txt — site purpose, API docs, contact
- JSON-LD snippet — Organization schema for homepage
- _headers — Cloudflare security header template

## QA Challenger
Verified: scan matches public HTML fetch. Recommend re-scan after WAF changes."""

DELIVERABLES = [
    "5-layer visibility scorecard",
    "P0/P1/P2 prioritized fixes",
    "Deployable robots.txt & llms.txt",
    "JSON-LD snippets",
    "Security header templates",
]


def upgrade() -> None:
    op.add_column("skill_showcases", sa.Column("sample_output", sa.Text(), nullable=True))
    op.add_column(
        "skill_showcases",
        sa.Column("deliverables", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="[]"),
    )

    op.execute(
        f"""
        UPDATE expert_skills
        SET price_usd_per_run = 4.9900,
            description = 'Agency-grade AI visibility audit for site owners: AIBotAuth scan → expert audit → deployable fix pack → QA review. Enter your URL and get files you can paste today.'
        WHERE id = '{EXPERT_SKILL_ID}'
        """
    )

    escaped_sample = SAMPLE_OUTPUT.replace("'", "''")
    deliverables_json = json.dumps(DELIVERABLES).replace("'", "''")
    op.execute(
        f"""
        UPDATE skill_showcases
        SET sample_output = '{escaped_sample}',
            deliverables = '{deliverables_json}'::jsonb
        WHERE id = '{SHOWCASE_AIBOTAUTH_ID}'
        """
    )


def downgrade() -> None:
    op.execute(
        f"""
        UPDATE expert_skills
        SET price_usd_per_run = 2.5000
        WHERE id = '{EXPERT_SKILL_ID}'
        """
    )
    op.drop_column("skill_showcases", "deliverables")
    op.drop_column("skill_showcases", "sample_output")