"""Fable-5 skill: Gemini/Grok as default engine

Revision ID: 021_fable5_gemini_grok
Revises: 020_fable5_coding
Create Date: 2026-06-19

"""
import json
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "021_fable5_gemini_grok"
down_revision: Union[str, Sequence[str], None] = "020_fable5_coding"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

EXPERT_SKILL_ID = "33333333-3333-4333-8333-333333333303"
SHOWCASE_ID = "55555555-5555-4555-8555-555555555505"

CREW_CONFIG = {
    "steps": [
        {
            "id": "plan",
            "type": "llm",
            "model": "gemini-2.5-flash",
            "title": "Planner Agent",
        },
        {
            "id": "implement",
            "type": "llm",
            "model": "gemini-2.5-flash",
            "title": "Implementer Agent",
        },
        {
            "id": "review",
            "type": "llm",
            "model": "grok-3-mini",
            "title": "Code Reviewer",
        },
        {
            "id": "qa",
            "type": "llm",
            "model": "grok-3-mini",
            "title": "QA Gate",
        },
    ]
}

CAPABILITIES = [
    "coding-agent",
    "tool-use",
    "multi-step-reasoning",
    "code-review",
    "fable5",
    "gemini",
    "grok",
]

DESCRIPTION = (
    "Free Fable-5 coding agent playbook: plan → implement → review → QA. "
    "Runs on Gemini 2.5 Flash (plan + code) and Grok 3 Mini (review + QA) — "
    "$0 marketplace fee. Optional local Ollama + fable5 LoRA when configured."
)


def upgrade() -> None:
    op.execute(
        sa.text(
            """
            UPDATE expert_skills
            SET description = :description,
                crew_config = CAST(:crew_config AS jsonb),
                capabilities = CAST(:capabilities AS jsonb)
            WHERE id = CAST(:skill_id AS uuid)
            """
        ).bindparams(
            description=DESCRIPTION,
            crew_config=json.dumps(CREW_CONFIG),
            capabilities=json.dumps(CAPABILITIES),
            skill_id=EXPERT_SKILL_ID,
        )
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
                "Describe a coding task in plain language. Fable-5 pipeline returns "
                "a step plan, implementation snippets, code review, and QA verdict — "
                "free to run on Gemini + Grok engines."
            ),
            highlights=json.dumps(
                [
                    "Fable-5 agent traces",
                    "Gemini 2.5 Flash engine",
                    "Grok 3 Mini review",
                    "$0 marketplace fee",
                ]
            ),
            showcase_id=SHOWCASE_ID,
        )
    )


def downgrade() -> None:
    old_crew = {
        "steps": [
            {"id": "plan", "type": "llm", "model": "qwen3.6-27b-fable5", "title": "Planner Agent"},
            {"id": "implement", "type": "llm", "model": "qwen3.6-27b-fable5", "title": "Implementer Agent"},
            {"id": "review", "type": "llm", "model": "gemini-2.5-flash", "title": "Code Reviewer"},
            {"id": "qa", "type": "llm", "model": "grok-3-mini", "title": "QA Gate"},
        ]
    }
    op.execute(
        sa.text(
            """
            UPDATE expert_skills
            SET description = :description,
                crew_config = CAST(:crew_config AS jsonb),
                capabilities = CAST(:capabilities AS jsonb)
            WHERE id = CAST(:skill_id AS uuid)
            """
        ).bindparams(
            description=(
                "Free Fable-5 coding agent flow: plan → implement → review → QA. "
                "Uses local Qwen3.6-27B + fable5 LoRA via Ollama when enabled ($0 LLM cost); "
                "falls back to cloud models automatically."
            ),
            crew_config=json.dumps(old_crew),
            capabilities=json.dumps(
                [
                    "coding-agent",
                    "tool-use",
                    "multi-step-reasoning",
                    "code-review",
                    "local-llm",
                    "fable5",
                ]
            ),
            skill_id=EXPERT_SKILL_ID,
        )
    )