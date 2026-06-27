"""Smart farm telemetry — farms, devices, readings, dataset packs

Revision ID: 042_smart_farm_telemetry
Revises: 041_obolla_thai_bilingual
Create Date: 2026-06-22

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "042_smart_farm_telemetry"
down_revision: Union[str, Sequence[str], None] = "041_obolla_thai_bilingual"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "smart_farms",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("crop_type", sa.String(80), nullable=False, server_default="generic"),
        sa.Column("timezone", sa.String(64), nullable=False, server_default="Asia/Bangkok"),
        sa.Column("auto_export_enabled", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("auto_export_hours", sa.Integer(), nullable=False, server_default="24"),
        sa.Column("metadata", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_smart_farms_user_id", "smart_farms", ["user_id"])

    op.create_table(
        "smart_farm_devices",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("farm_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("smart_farms.id", ondelete="CASCADE"), nullable=False),
        sa.Column("device_name", sa.String(120), nullable=False),
        sa.Column("token_hash", sa.String(64), nullable=False, unique=True),
        sa.Column("protocol", sa.String(20), nullable=False, server_default="http"),
        sa.Column("mqtt_topic", sa.String(200), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="active"),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_smart_farm_devices_farm_id", "smart_farm_devices", ["farm_id"])
    op.create_index("ix_smart_farm_devices_mqtt_topic", "smart_farm_devices", ["mqtt_topic"])

    op.create_table(
        "smart_farm_channels",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("device_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("smart_farm_devices.id", ondelete="CASCADE"), nullable=False),
        sa.Column("channel_key", sa.String(80), nullable=False),
        sa.Column("label", sa.String(120), nullable=False, server_default=""),
        sa.Column("unit", sa.String(40), nullable=False, server_default=""),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_smart_farm_channels_device_id", "smart_farm_channels", ["device_id"])
    op.create_index("ix_smart_farm_channels_device_key", "smart_farm_channels", ["device_id", "channel_key"], unique=True)

    op.create_table(
        "smart_farm_readings",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("channel_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("smart_farm_channels.id", ondelete="CASCADE"), nullable=False),
        sa.Column("recorded_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("value_numeric", sa.Float(), nullable=True),
        sa.Column("value_json", postgresql.JSONB(), nullable=True),
        sa.Column("source", sa.String(20), nullable=False, server_default="http"),
        sa.Column("ingest_meta", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
    )
    op.create_index("ix_smart_farm_readings_channel_id", "smart_farm_readings", ["channel_id"])
    op.create_index("ix_smart_farm_readings_recorded_at", "smart_farm_readings", ["recorded_at"])
    op.create_index("ix_smart_farm_readings_channel_time", "smart_farm_readings", ["channel_id", "recorded_at"])

    op.create_table(
        "smart_farm_dataset_packs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("farm_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("smart_farms.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(160), nullable=False),
        sa.Column("format", sa.String(10), nullable=False, server_default="json"),
        sa.Column("file_path", sa.Text(), nullable=False),
        sa.Column("record_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("window_start", sa.DateTime(timezone=True), nullable=True),
        sa.Column("window_end", sa.DateTime(timezone=True), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="ready"),
        sa.Column("auto_generated", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_smart_farm_dataset_packs_farm_id", "smart_farm_dataset_packs", ["farm_id"])

    op.create_table(
        "smart_farm_ingest_events",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("device_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("smart_farm_devices.id", ondelete="SET NULL"), nullable=True),
        sa.Column("source", sa.String(20), nullable=False, server_default="http"),
        sa.Column("payload", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("status", sa.String(20), nullable=False, server_default="ok"),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("readings_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_smart_farm_ingest_events_device_id", "smart_farm_ingest_events", ["device_id"])
    op.create_index("ix_smart_farm_ingest_events_created_at", "smart_farm_ingest_events", ["created_at"])


def downgrade() -> None:
    op.drop_table("smart_farm_ingest_events")
    op.drop_table("smart_farm_dataset_packs")
    op.drop_table("smart_farm_readings")
    op.drop_table("smart_farm_channels")
    op.drop_table("smart_farm_devices")
    op.drop_table("smart_farms")