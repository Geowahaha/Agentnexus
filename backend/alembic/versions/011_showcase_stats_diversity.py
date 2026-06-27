"""showcase stats and second case study

Revision ID: 011_showcase_stats
Revises: 010_showcase_sales
Create Date: 2026-06-17

"""
import json
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "011_showcase_stats"
down_revision: Union[str, Sequence[str], None] = "010_showcase_sales"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

EXPERT_SKILL_ID = "33333333-3333-4333-8333-333333333301"
SHOWCASE_AIBOTAUTH_ID = "55555555-5555-4555-8555-555555555501"
SHOWCASE_CASTING_ID = "55555555-5555-4555-8555-555555555502"

AIBOTAUTH_STATS = {
    "score": "85/100",
    "time_saved": "~3 hours vs manual audit",
    "deliverables_count": "5 files",
    "runtime": "3–5 minutes",
}

CASTING_STATS = {
    "score": "Limited (site gated)",
    "time_saved": "~2 hours research either way",
    "deliverables_count": "Guidance + partial report",
    "runtime": "3–5 minutes",
}

CASTING_SAMPLE = """## Scan note
Site returned HTTP 401 — scanner blocked. Audit still lists likely fixes from public signals.

## Auditor (excerpt)
P0: Allow trusted AI crawlers in robots.txt and WAF.
P1: Publish llms.txt so agents know your brand and contact.
P2: Add Organization JSON-LD on the homepage.

## What you still receive
Prioritized fix list, template robots.txt / llms.txt, and deployment notes — even when full scan access is blocked."""


def upgrade() -> None:
    op.add_column(
        "skill_showcases",
        sa.Column("stats", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="{}"),
    )

    op.execute(
        f"""
        UPDATE skill_showcases
        SET stats = '{json.dumps(AIBOTAUTH_STATS).replace("'", "''")}'::jsonb,
            metric_label = 'Visibility score',
            metric_value = '85/100'
        WHERE id = '{SHOWCASE_AIBOTAUTH_ID}'
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
    )
    op.bulk_insert(
        showcases,
        [
            {
                "id": SHOWCASE_CASTING_ID,
                "expert_skill_id": EXPERT_SKILL_ID,
                "title": "Gated site — still get a fix plan",
                "site_name": "SuccessCasting",
                "site_url": "https://successcasting.com",
                "summary": (
                    "Not every site allows scanners. This case study shows what buyers still receive "
                    "when a WAF blocks access — honest expectations, partial visibility signals, "
                    "and the same deployable fix templates."
                ),
                "metric_label": "Scan result",
                "metric_value": "HTTP 401 — partial audit",
                "highlights": [
                    "Real-world WAF challenge",
                    "Fix list without full score",
                    "Same skill, different outcome",
                    "Clear buyer expectations",
                ],
                "sort_order": 1,
                "is_featured": False,
                "is_active": True,
                "sample_output": CASTING_SAMPLE,
                "deliverables": [
                    "Partial visibility report",
                    "WAF / access guidance",
                    "Template policy files",
                    "Priority fix roadmap",
                ],
                "stats": CASTING_STATS,
            }
        ],
    )


def downgrade() -> None:
    op.execute(f"DELETE FROM skill_showcases WHERE id = '{SHOWCASE_CASTING_ID}'")
    op.drop_column("skill_showcases", "stats")