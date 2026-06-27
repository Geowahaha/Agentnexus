"""update seeded crew agents to gemini default model

Revision ID: 006_seed_gemini
Revises: 005_stripe_payouts
Create Date: 2026-06-17

"""
from typing import Sequence, Union

from alembic import op

revision: str = "006_seed_gemini"
down_revision: Union[str, Sequence[str], None] = "005_stripe_payouts"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

SEED_AGENT_IDS = (
    "11111111-1111-4111-8111-111111111101",
    "11111111-1111-4111-8111-111111111102",
    "11111111-1111-4111-8111-111111111103",
)


def upgrade() -> None:
    op.execute(
        """
        UPDATE agents
        SET llm_model = 'gemini-2.5-flash', updated_at = now()
        WHERE id IN (
            '11111111-1111-4111-8111-111111111101',
            '11111111-1111-4111-8111-111111111102',
            '11111111-1111-4111-8111-111111111103'
        )
        AND llm_model = 'gpt-4o-mini'
        """
    )


def downgrade() -> None:
    op.execute(
        """
        UPDATE agents
        SET llm_model = 'gpt-4o-mini', updated_at = now()
        WHERE id IN (
            '11111111-1111-4111-8111-111111111101',
            '11111111-1111-4111-8111-111111111102',
            '11111111-1111-4111-8111-111111111103'
        )
        AND llm_model = 'gemini-2.5-flash'
        """
    )