"""Smart farm registration: organization, location, gateway IPs, weather alerts

Revision ID: 044_smart_farm_registration
Revises: 043_smart_farm_marketplace
Create Date: 2026-06-22

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "044_smart_farm_registration"
down_revision: Union[str, Sequence[str], None] = "043_smart_farm_marketplace"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("smart_farms", sa.Column("organization_name", sa.String(160), nullable=True))
    op.add_column("smart_farms", sa.Column("address", sa.Text(), nullable=True))
    op.add_column("smart_farms", sa.Column("latitude", sa.Float(), nullable=True))
    op.add_column("smart_farms", sa.Column("longitude", sa.Float(), nullable=True))
    op.add_column("smart_farms", sa.Column("google_maps_url", sa.Text(), nullable=True))
    op.add_column(
        "smart_farms",
        sa.Column("gateway_ips", postgresql.JSONB(), nullable=False, server_default="[]"),
    )
    op.add_column(
        "smart_farms",
        sa.Column("weather_alerts_enabled", sa.Boolean(), nullable=False, server_default="true"),
    )


def downgrade() -> None:
    op.drop_column("smart_farms", "weather_alerts_enabled")
    op.drop_column("smart_farms", "gateway_ips")
    op.drop_column("smart_farms", "google_maps_url")
    op.drop_column("smart_farms", "longitude")
    op.drop_column("smart_farms", "latitude")
    op.drop_column("smart_farms", "address")
    op.drop_column("smart_farms", "organization_name")