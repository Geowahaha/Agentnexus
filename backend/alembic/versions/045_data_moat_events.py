"""Data Moat foundation: visibility_events + skill_execution_events

Revision ID: 045_data_moat_events
Revises: 044_smart_farm_registration
Create Date: 2026-06-26

This migration adds the core tables for the AIBotAuth + OBOLLA closed-loop
Data Moat: AI Citation/Readiness events and Skill Execution + Attribution events.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "045_data_moat_events"
down_revision: Union[str, Sequence[str], None] = "044_smart_farm_registration"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # visibility_events: captures every AIBotAuth-style scan / proof / readiness signal
    op.create_table(
        "visibility_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("url", sa.String(500), nullable=False, index=True),
        sa.Column("scanned_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("source", sa.String(60), nullable=False, server_default="aibotauth_mcp"),
        sa.Column("overall", sa.Numeric(5, 1), nullable=True),
        sa.Column("grade", sa.String(10), nullable=True),
        sa.Column("level", sa.String(20), nullable=True),
        sa.Column("percent", sa.Numeric(5, 1), nullable=True),
        sa.Column("details", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("proof_share_id", sa.String(120), nullable=True),
        sa.Column("proof_url", sa.String(500), nullable=True),
        sa.Column("workflow_id", sa.String(36), nullable=True, index=True),
        sa.Column("linked_skill_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_foreign_key(
        "fk_visibility_events_linked_skill",
        "visibility_events", "expert_skills",
        ["linked_skill_id"], ["id"],
        ondelete="SET NULL",
    )

    # skill_execution_events: captures marketplace skill runs with context, costs, outcomes, links
    op.create_table(
        "skill_execution_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("workflow_id", sa.String(36), nullable=False, unique=True, index=True),
        sa.Column("expert_skill_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("skill_slug", sa.String(120), nullable=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("target_urls", postgresql.JSONB(), nullable=False, server_default="[]"),
        sa.Column("step_summary", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("marketplace_cost_usd", sa.Numeric(12, 4), nullable=False, server_default="0"),
        sa.Column("llm_cost_usd", sa.Numeric(12, 4), nullable=False, server_default="0"),
        sa.Column("total_cost_usd", sa.Numeric(12, 4), nullable=False, server_default="0"),
        sa.Column("outcome_proxies", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("linked_visibility_event_ids", postgresql.JSONB(), nullable=False, server_default="[]"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_foreign_key(
        "fk_skill_exec_linked_skill",
        "skill_execution_events", "expert_skills",
        ["expert_skill_id"], ["id"],
        ondelete="SET NULL",
    )
    op.create_foreign_key(
        "fk_skill_exec_user",
        "skill_execution_events", "users",
        ["user_id"], ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    op.drop_constraint("fk_skill_exec_user", "skill_execution_events", type_="foreignkey")
    op.drop_constraint("fk_skill_exec_linked_skill", "skill_execution_events", type_="foreignkey")
    op.drop_table("skill_execution_events")

    op.drop_constraint("fk_visibility_events_linked_skill", "visibility_events", type_="foreignkey")
    op.drop_table("visibility_events")
