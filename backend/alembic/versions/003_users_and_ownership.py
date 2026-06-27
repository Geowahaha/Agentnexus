"""add users table and link owner_id to users

Revision ID: 003_users
Revises: 002_marketplace
Create Date: 2026-06-17

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "003_users"
down_revision: Union[str, Sequence[str], None] = "002_marketplace"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

SYSTEM_USER_ID = "00000000-0000-4000-8000-000000000001"


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False, unique=True),
        sa.Column("hashed_password", sa.String(length=255), nullable=False),
        sa.Column("full_name", sa.String(length=120), nullable=False),
        sa.Column("role", sa.String(length=40), nullable=False, server_default="user"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )

    op.execute(
        f"""
        INSERT INTO users (id, email, hashed_password, full_name, role, is_active)
        VALUES (
            '{SYSTEM_USER_ID}',
            'system@agentnexus.local',
            '$2b$12$/e1NvGRZg381J4awWuRDK.bR8DTLbZ/89ri5TeAZBBIEk7EMnmgOW',
            'System',
            'admin',
            true
        )
        """
    )

    for table in ("agents", "custom_tools", "mcp_servers"):
        op.add_column(table, sa.Column("owner_id_uuid", postgresql.UUID(as_uuid=True), nullable=True))
        op.execute(
            f"""
            UPDATE {table}
            SET owner_id_uuid = '{SYSTEM_USER_ID}'
            WHERE owner_id = 'system' OR owner_id_uuid IS NULL
            """
        )
        op.alter_column(table, "owner_id_uuid", nullable=False)
        op.drop_column(table, "owner_id")
        op.alter_column(table, "owner_id_uuid", new_column_name="owner_id")
        op.create_foreign_key(
            f"fk_{table}_owner_id_users",
            table,
            "users",
            ["owner_id"],
            ["id"],
            ondelete="RESTRICT",
        )


def downgrade() -> None:
    for table in ("mcp_servers", "custom_tools", "agents"):
        op.drop_constraint(f"fk_{table}_owner_id_users", table, type_="foreignkey")
        op.alter_column(table, "owner_id", new_column_name="owner_id_uuid")
        op.add_column(table, sa.Column("owner_id", sa.String(length=120), nullable=True))
        op.execute(
            f"""
            UPDATE {table}
            SET owner_id = 'system'
            WHERE owner_id_uuid = '{SYSTEM_USER_ID}'
            """
        )
        op.alter_column(table, "owner_id", nullable=False)
        op.drop_column(table, "owner_id_uuid")

    op.drop_table("users")