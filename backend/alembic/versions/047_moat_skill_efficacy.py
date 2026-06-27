"""Persist Moat Skill Efficacy profiles for compounding moat and revenue intelligence

Revision ID: 047_moat_skill_efficacy
Revises: 046_agent_behavior_traces
Create Date: 2026-06-26

This table persists the derived proprietary SkillEfficacyProfiles with revenue attribution.
Enables fast queries for revenue intelligence products without recomputing.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "047_moat_skill_efficacy"
down_revision: Union[str, Sequence[str], None] = "046_agent_behavior_traces"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "moat_skill_efficacy",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("skill_slug", sa.String(120), nullable=False, unique=True),
        sa.Column("total_runs", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("successful_lifts", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("avg_delta_percent", sa.Numeric(8, 2), nullable=False, server_default="0"),
        sa.Column("confidence_score", sa.Numeric(5, 3), nullable=False, server_default="0"),
        sa.Column("url_categories", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("total_attributed_revenue_usd", sa.Numeric(12, 4), nullable=False, server_default="0"),
        sa.Column("avg_revenue_per_lift", sa.Numeric(12, 4), nullable=False, server_default="0"),
        sa.Column("profile_data", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("last_updated", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_moat_skill_efficacy_skill_slug", "moat_skill_efficacy", ["skill_slug"])


def downgrade() -> None:
    op.drop_index("ix_moat_skill_efficacy_skill_slug", table_name="moat_skill_efficacy")
    op.drop_table("moat_skill_efficacy")
