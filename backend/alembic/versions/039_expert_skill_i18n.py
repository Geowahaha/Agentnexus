"""expert_skills.i18n JSONB for Thai (and future locales)

Revision ID: 039_expert_skill_i18n
Revises: 038_agent_ready_marketplace_pricing_copy
Create Date: 2026-06-22

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

revision: str = "039_expert_skill_i18n"
down_revision: Union[str, Sequence[str], None] = "038_marketplace_pricing"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "expert_skills",
        sa.Column("i18n", JSONB, nullable=False, server_default=sa.text("'{}'::jsonb")),
    )


def downgrade() -> None:
    op.drop_column("expert_skills", "i18n")