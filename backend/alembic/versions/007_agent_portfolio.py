"""agent portfolio items

Revision ID: 007_agent_portfolio
Revises: 006_seed_gemini
Create Date: 2026-06-17

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "007_agent_portfolio"
down_revision: Union[str, Sequence[str], None] = "006_seed_gemini"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "agent_portfolio_items",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column(
            "agent_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("agents.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("workflow_id", sa.String(length=36), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("task_preview", sa.Text(), nullable=False),
        sa.Column("output_preview", sa.Text(), nullable=False),
        sa.Column("workflow_type", sa.String(length=40), nullable=False),
        sa.Column("is_public", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.UniqueConstraint("agent_id", "workflow_id", name="uq_portfolio_agent_workflow"),
    )
    op.create_index("ix_portfolio_agent_public", "agent_portfolio_items", ["agent_id", "is_public"])


def downgrade() -> None:
    op.drop_index("ix_portfolio_agent_public", table_name="agent_portfolio_items")
    op.drop_table("agent_portfolio_items")