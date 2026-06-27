"""local agent bridge devices and pairing

Revision ID: 019_local_agent_bridge
Revises: 018_seo_expert_analysis
Create Date: 2026-06-19

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "019_local_agent_bridge"
down_revision: Union[str, Sequence[str], None] = "018_seo_expert"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "bridge_pairing_codes",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("code", sa.String(length=6), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "device_id",
            postgresql.UUID(as_uuid=True),
            nullable=True,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("ix_bridge_pairing_codes_code", "bridge_pairing_codes", ["code"], unique=True)
    op.create_index("ix_bridge_pairing_codes_user_id", "bridge_pairing_codes", ["user_id"])

    op.create_table(
        "bridge_devices",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("device_name", sa.String(length=120), nullable=False),
        sa.Column("token_hash", sa.String(length=64), nullable=False),
        sa.Column(
            "capabilities",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default='["read"]',
        ),
        sa.Column(
            "allowed_roots",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default="[]",
        ),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="active"),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_bridge_devices_user_id", "bridge_devices", ["user_id"])
    op.create_index("ix_bridge_devices_token_hash", "bridge_devices", ["token_hash"], unique=True)

    op.create_table(
        "bridge_audit_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "device_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("bridge_devices.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("tool_name", sa.String(length=80), nullable=False),
        sa.Column("args", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="{}"),
        sa.Column("ok", sa.Boolean(), nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("ix_bridge_audit_events_user_id", "bridge_audit_events", ["user_id"])


def downgrade() -> None:
    op.drop_index("ix_bridge_audit_events_user_id", table_name="bridge_audit_events")
    op.drop_table("bridge_audit_events")
    op.drop_index("ix_bridge_devices_token_hash", table_name="bridge_devices")
    op.drop_index("ix_bridge_devices_user_id", table_name="bridge_devices")
    op.drop_table("bridge_devices")
    op.drop_index("ix_bridge_pairing_codes_user_id", table_name="bridge_pairing_codes")
    op.drop_index("ix_bridge_pairing_codes_code", table_name="bridge_pairing_codes")
    op.drop_table("bridge_pairing_codes")