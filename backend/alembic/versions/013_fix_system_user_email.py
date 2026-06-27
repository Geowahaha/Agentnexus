"""fix system user email for pydantic validation

Revision ID: 013_system_email
Revises: 012_creator_dashboard
Create Date: 2026-06-17

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "013_system_email"
down_revision: Union[str, Sequence[str], None] = "012_creator_dashboard"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

SYSTEM_USER_ID = "00000000-0000-4000-8000-000000000001"


def upgrade() -> None:
    op.execute(
        sa.text(
            f"""
            UPDATE users
            SET email = 'system@agentnexus.dev'
            WHERE id = '{SYSTEM_USER_ID}'::uuid
              AND email = 'system@agentnexus.local'
            """
        )
    )


def downgrade() -> None:
    op.execute(
        sa.text(
            f"""
            UPDATE users
            SET email = 'system@agentnexus.local'
            WHERE id = '{SYSTEM_USER_ID}'::uuid
              AND email = 'system@agentnexus.dev'
            """
        )
    )