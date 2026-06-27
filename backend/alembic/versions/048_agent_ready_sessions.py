"""Agent-Ready per-user site sessions (coach state + free rescan entitlement)

Revision ID: 048_agent_ready_sessions
Revises: 047_moat_skill_efficacy
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "048_agent_ready_sessions"
down_revision: Union[str, Sequence[str], None] = "047_moat_skill_efficacy"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "agent_ready_sessions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("site_url", sa.Text(), nullable=False),
        sa.Column("site_host", sa.String(255), nullable=False),
        sa.Column("expert_skill_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("entitled", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("first_paid_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_scan_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("scan_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("workflow_id", sa.String(36), nullable=True),
        sa.Column("coach_headline", sa.Text(), nullable=True),
        sa.Column("state", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("user_id", "site_host", name="uq_agent_ready_sessions_user_host"),
    )
    op.create_index("ix_agent_ready_sessions_user_id", "agent_ready_sessions", ["user_id"])
    op.create_index("ix_agent_ready_sessions_site_host", "agent_ready_sessions", ["site_host"])


def downgrade() -> None:
    op.drop_index("ix_agent_ready_sessions_site_host", table_name="agent_ready_sessions")
    op.drop_index("ix_agent_ready_sessions_user_id", table_name="agent_ready_sessions")
    op.drop_table("agent_ready_sessions")