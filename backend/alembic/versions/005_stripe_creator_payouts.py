"""stripe checkout and creator earnings

Revision ID: 005_stripe_payouts
Revises: 004_billing
Create Date: 2026-06-17

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "005_stripe_payouts"
down_revision: Union[str, Sequence[str], None] = "004_billing"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "wallets",
        sa.Column("earnings_balance_usd", sa.Numeric(12, 4), nullable=False, server_default="0"),
    )

    op.create_table(
        "stripe_checkout_sessions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("stripe_session_id", sa.String(length=255), nullable=False, unique=True),
        sa.Column("amount_usd", sa.Numeric(12, 4), nullable=False),
        sa.Column("status", sa.String(length=40), nullable=False, server_default="pending"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
    )

    op.create_table(
        "creator_earnings",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("creator_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("buyer_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("agent_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("agents.id", ondelete="CASCADE"), nullable=False),
        sa.Column("workflow_id", sa.String(length=36), nullable=False),
        sa.Column("gross_amount_usd", sa.Numeric(12, 4), nullable=False),
        sa.Column("platform_fee_usd", sa.Numeric(12, 4), nullable=False),
        sa.Column("net_amount_usd", sa.Numeric(12, 4), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )


def downgrade() -> None:
    op.drop_table("creator_earnings")
    op.drop_table("stripe_checkout_sessions")
    op.drop_column("wallets", "earnings_balance_usd")