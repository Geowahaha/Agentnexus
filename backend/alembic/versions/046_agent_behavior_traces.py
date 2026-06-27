"""Agent Behavior Traces — high-fidelity structured moat asset

Revision ID: 046_agent_behavior_traces
Revises: 045_data_moat_events
Create Date: 2026-06-26

This table is the heart of the durable, hard-to-replicate Data Moat.
It stores versioned, typed, causally-linked agent behavior traces
correlated with cryptographically verifiable visibility states.

Long-term value:
- Expensive to replicate (requires signed crawler + curated skills + volume on same URLs)
- Unique ownership via AIBotAuth provenance + our execution data
- Compounds: enables proprietary SkillEfficacy, DomainBenchmarks, recommendation models
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "046_agent_behavior_traces"
down_revision: Union[str, Sequence[str], None] = "045_data_moat_events"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "agent_behavior_traces",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("workflow_id", sa.String(36), nullable=False, unique=True),
        sa.Column("expert_skill_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("skill_slug", sa.String(120), nullable=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("target_url", sa.String(500), nullable=False),
        sa.Column("url_fingerprint", sa.String(128), nullable=True),
        sa.Column("fingerprint_version", sa.String(16), nullable=False, server_default="1.0"),
        sa.Column("pre_visibility", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("behavior_sequence", postgresql.JSONB(), nullable=False, server_default="[]"),
        sa.Column("post_visibility", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("causal_lift", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("provenance", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("marketplace_cost_usd", sa.Numeric(12, 4), nullable=False, server_default="0"),
        sa.Column("llm_cost_usd", sa.Numeric(12, 4), nullable=False, server_default="0"),
        sa.Column("total_cost_usd", sa.Numeric(12, 4), nullable=False, server_default="0"),
        sa.Column("step_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("success", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    op.create_index("ix_agent_behavior_traces_target_url", "agent_behavior_traces", ["target_url"])
    op.create_index("ix_agent_behavior_traces_skill_slug", "agent_behavior_traces", ["skill_slug"])
    op.create_index("ix_agent_behavior_traces_url_fingerprint", "agent_behavior_traces", ["url_fingerprint"])

    op.create_foreign_key(
        "fk_abt_expert_skill",
        "agent_behavior_traces", "expert_skills",
        ["expert_skill_id"], ["id"],
        ondelete="SET NULL",
    )
    op.create_foreign_key(
        "fk_abt_user",
        "agent_behavior_traces", "users",
        ["user_id"], ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    op.drop_constraint("fk_abt_user", "agent_behavior_traces", type_="foreignkey")
    op.drop_constraint("fk_abt_expert_skill", "agent_behavior_traces", type_="foreignkey")
    op.drop_index("ix_agent_behavior_traces_url_fingerprint", table_name="agent_behavior_traces")
    op.drop_index("ix_agent_behavior_traces_skill_slug", table_name="agent_behavior_traces")
    op.drop_index("ix_agent_behavior_traces_target_url", table_name="agent_behavior_traces")
    op.drop_table("agent_behavior_traces")
