"""Fable-5 free tier: HuggingFace credits in description + showcase

Revision ID: 024_fable5_credits
Revises: 023_fable5_tiers
Create Date: 2026-06-20

"""
import json
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "024_fable5_credits"
down_revision: Union[str, Sequence[str], None] = "023_fable5_tiers"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

FREE_SKILL_ID = "33333333-3333-4333-8333-333333333303"
FREE_SHOWCASE_ID = "55555555-5555-4555-8555-555555555505"

LORA_URL = "https://huggingface.co/hotdogs/qwen3.6-27b-fable5-lora"
TRACES_URL = "https://huggingface.co/datasets/Glint-Research/Fable-5-traces"

DESCRIPTION = (
    "Free local Fable-5 LoRA: plan → implement → review → QA on "
    "hotdogs/qwen3.6-27b-fable5-lora (Ollama, $0 run + $0 LLM). "
    f"Adapter: {LORA_URL} · Traces: {TRACES_URL} · No cloud fallback."
)


def upgrade() -> None:
    op.execute(
        sa.text(
            """
            UPDATE expert_skills
            SET description = :description
            WHERE id = CAST(:skill_id AS uuid)
            """
        ).bindparams(description=DESCRIPTION, skill_id=FREE_SKILL_ID)
    )
    op.execute(
        sa.text(
            """
            UPDATE skill_showcases
            SET summary = :summary,
                highlights = CAST(:highlights AS jsonb)
            WHERE id = CAST(:showcase_id AS uuid)
            """
        ).bindparams(
            summary=(
                "Runs the upstream hotdogs/qwen3.6-27b-fable5-lora adapter on your GPU — "
                "closest match to the HuggingFace weights. Playbook inspired by "
                "Glint-Research/Fable-5-traces. $0 run + $0 LLM."
            ),
            highlights=json.dumps(
                [
                    "hotdogs/qwen3.6-27b-fable5-lora",
                    "Glint-Research/Fable-5-traces",
                    "All 4 steps on local GPU",
                    "$0 marketplace + $0 LLM",
                ]
            ),
            showcase_id=FREE_SHOWCASE_ID,
        )
    )


def downgrade() -> None:
    op.execute(
        sa.text(
            """
            UPDATE expert_skills
            SET description = :description
            WHERE id = CAST(:skill_id AS uuid)
            """
        ).bindparams(
            description=(
                "Free local Fable-5 LoRA agent: plan → implement → review → QA on "
                "hotdogs/qwen3.6-27b-fable5-lora via Ollama ($0 run fee, $0 LLM). "
                "Requires OLLAMA_ENABLED + GPU. No cloud fallback."
            ),
            skill_id=FREE_SKILL_ID,
        )
    )