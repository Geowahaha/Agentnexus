"""add marketplace fields, custom tools, and mcp servers

Revision ID: 002_marketplace
Revises: 001_create_agents
Create Date: 2026-06-17

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "002_marketplace"
down_revision: Union[str, Sequence[str], None] = "001_create_agents"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("agents", sa.Column("owner_id", sa.String(length=120), nullable=False, server_default="system"))
    op.add_column("agents", sa.Column("price_usd_per_run", sa.Numeric(10, 4), nullable=False, server_default="0"))
    op.add_column("agents", sa.Column("capabilities", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="[]"))
    op.add_column("agents", sa.Column("category", sa.String(length=80), nullable=True))

    op.create_table(
        "custom_tools",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False, unique=True),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("owner_id", sa.String(length=120), nullable=False),
        sa.Column("tool_type", sa.String(length=40), nullable=False),
        sa.Column("config", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )

    op.create_table(
        "mcp_servers",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False, unique=True),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("owner_id", sa.String(length=120), nullable=False),
        sa.Column("transport", sa.String(length=40), nullable=False),
        sa.Column("config", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )

    op.create_table(
        "mcp_tools",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("mcp_server_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("mcp_servers.id", ondelete="CASCADE"), nullable=False),
        sa.Column("tool_name", sa.String(length=120), nullable=False),
        sa.Column("qualified_name", sa.String(length=200), nullable=False, unique=True),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("input_schema", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="{}"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )

    op.execute(
        """
        UPDATE agents SET
            owner_id = 'system',
            price_usd_per_run = 0.01,
            capabilities = '["research"]'::jsonb,
            category = 'research'
        WHERE id = '11111111-1111-4111-8111-111111111101'
        """
    )
    op.execute(
        """
        UPDATE agents SET
            owner_id = 'system',
            price_usd_per_run = 0.02,
            capabilities = '["writing", "content"]'::jsonb,
            category = 'content'
        WHERE id = '11111111-1111-4111-8111-111111111102'
        """
    )
    op.execute(
        """
        UPDATE agents SET
            owner_id = 'system',
            price_usd_per_run = 0.015,
            capabilities = '["review", "quality"]'::jsonb,
            category = 'quality'
        WHERE id = '11111111-1111-4111-8111-111111111103'
        """
    )


def downgrade() -> None:
    op.drop_table("mcp_tools")
    op.drop_table("mcp_servers")
    op.drop_table("custom_tools")
    op.drop_column("agents", "category")
    op.drop_column("agents", "capabilities")
    op.drop_column("agents", "price_usd_per_run")
    op.drop_column("agents", "owner_id")