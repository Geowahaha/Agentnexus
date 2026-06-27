"""skill showcases for marketplace

Revision ID: 009_skill_showcases
Revises: 008_expert_skills
Create Date: 2026-06-17

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "009_skill_showcases"
down_revision: Union[str, Sequence[str], None] = "008_expert_skills"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

EXPERT_SKILL_ID = "33333333-3333-4333-8333-333333333301"
SHOWCASE_AIBOTAUTH_ID = "55555555-5555-4555-8555-555555555501"


def upgrade() -> None:
    op.create_table(
        "skill_showcases",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("expert_skill_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("site_name", sa.String(length=120), nullable=False),
        sa.Column("site_url", sa.String(length=500), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("metric_label", sa.String(length=80), nullable=True),
        sa.Column("metric_value", sa.String(length=80), nullable=True),
        sa.Column("highlights", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="[]"),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("is_featured", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("workflow_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["expert_skill_id"], ["expert_skills.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_skill_showcases_expert_skill_id", "skill_showcases", ["expert_skill_id"])

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
    )
    op.bulk_insert(
        showcases,
        [
            {
                "id": SHOWCASE_AIBOTAUTH_ID,
                "expert_skill_id": EXPERT_SKILL_ID,
                "title": "AIBotAuth — built with this skill",
                "site_name": "AIBotAuth",
                "site_url": "https://www.aibotauth.com",
                "summary": (
                    "AIBotAuth is the live reference implementation for the AI Visibility Audit pipeline. "
                    "The same Expert Skill that scans, audits, and ships fix packs for client sites was used "
                    "to optimize agent discovery, llms.txt, and crawler access on aibotauth.com."
                ),
                "metric_label": "Skill used",
                "metric_value": "AI Visibility Audit 2026",
                "highlights": [
                    "Live AIBotAuth scanner integration",
                    "llms.txt & robots.txt agent policy",
                    "JSON-LD & semantic structure",
                    "Public scorecard demo",
                ],
                "sort_order": 0,
                "is_featured": True,
                "is_active": True,
            }
        ],
    )


def downgrade() -> None:
    op.drop_index("ix_skill_showcases_expert_skill_id", table_name="skill_showcases")
    op.drop_table("skill_showcases")