"""creator dashboard: skill reviews and flexible product earnings

Revision ID: 012_creator_dashboard
Revises: 011_showcase_stats
Create Date: 2026-06-17

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "012_creator_dashboard"
down_revision: Union[str, Sequence[str], None] = "011_showcase_stats"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

EXPERT_SKILL_ID = "33333333-3333-4333-8333-333333333301"
SYSTEM_USER_ID = "00000000-0000-4000-8000-000000000001"


def upgrade() -> None:
    op.drop_constraint("creator_earnings_agent_id_fkey", "creator_earnings", type_="foreignkey")
    op.add_column(
        "creator_earnings",
        sa.Column("product_type", sa.String(length=40), nullable=False, server_default="agent"),
    )
    op.execute(
        sa.text(
            f"""
            UPDATE creator_earnings
            SET product_type = 'expert_skill'
            WHERE agent_id = '{EXPERT_SKILL_ID}'::uuid
            """
        )
    )

    op.create_table(
        "skill_reviews",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column(
            "expert_skill_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("expert_skills.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "buyer_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("rating", sa.Integer(), nullable=False),
        sa.Column("comment", sa.Text(), nullable=False),
        sa.Column("workflow_id", sa.String(length=36), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.CheckConstraint("rating >= 1 AND rating <= 5", name="ck_skill_reviews_rating"),
        sa.UniqueConstraint("expert_skill_id", "buyer_id", name="uq_skill_reviews_skill_buyer"),
    )

    op.execute(
        sa.text(
            f"""
            INSERT INTO skill_reviews (id, expert_skill_id, buyer_id, rating, comment, workflow_id)
            SELECT * FROM (VALUES
            (
                '66666666-6666-4666-8666-666666666601'::uuid,
                '{EXPERT_SKILL_ID}'::uuid,
                '{SYSTEM_USER_ID}'::uuid,
                5,
                'Clear scorecard and actionable fix pack. Ran it on our marketing site and shipped robots.txt changes same day.',
                NULL::varchar
            )
            ) AS seed(id, expert_skill_id, buyer_id, rating, comment, workflow_id)
            WHERE NOT EXISTS (
                SELECT 1 FROM skill_reviews WHERE expert_skill_id = '{EXPERT_SKILL_ID}'::uuid
            )
            """
        )
    )


def downgrade() -> None:
    op.drop_table("skill_reviews")
    op.drop_column("creator_earnings", "product_type")
    op.create_foreign_key(
        "creator_earnings_agent_id_fkey",
        "creator_earnings",
        "agents",
        ["agent_id"],
        ["id"],
        ondelete="CASCADE",
    )