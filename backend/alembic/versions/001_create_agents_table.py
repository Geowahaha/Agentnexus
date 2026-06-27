"""create agents table and seed default crew

Revision ID: 001_create_agents
Revises:
Create Date: 2026-06-17

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "001_create_agents"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

SEED_AGENTS = [
    {
        "id": "11111111-1111-4111-8111-111111111101",
        "name": "Researcher",
        "description": "Researches and analyzes task requirements.",
        "role": "You are a research specialist. Gather facts, context, and key insights for the task.",
        "llm_model": "gpt-4o-mini",
        "tools": ["web_search"],
        "is_active": True,
    },
    {
        "id": "11111111-1111-4111-8111-111111111102",
        "name": "Writer",
        "description": "Drafts the primary deliverable from research notes.",
        "role": "You are a content writer. Turn research into clear, structured output.",
        "llm_model": "gpt-4o-mini",
        "tools": [],
        "is_active": True,
    },
    {
        "id": "11111111-1111-4111-8111-111111111103",
        "name": "Reviewer",
        "description": "Reviews and polishes the final draft.",
        "role": "You are a quality reviewer. Refine output for accuracy, clarity, and completeness.",
        "llm_model": "gpt-4o-mini",
        "tools": [],
        "is_active": True,
    },
]


def upgrade() -> None:
    agents_table = op.create_table(
        "agents",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("role", sa.Text(), nullable=False),
        sa.Column("llm_model", sa.String(length=120), nullable=False),
        sa.Column("tools", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )

    op.bulk_insert(
        agents_table,
        [
            {
                **agent,
                "id": agent["id"],
                "tools": agent["tools"],
            }
            for agent in SEED_AGENTS
        ],
    )


def downgrade() -> None:
    op.drop_table("agents")