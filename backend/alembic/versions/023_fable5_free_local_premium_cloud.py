"""Fable-5 split: free local LoRA + $5 premium OpenAI/Grok

Revision ID: 023_fable5_tiers
Revises: 022_fable5_showcase
Create Date: 2026-06-20

"""
import json
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "023_fable5_tiers"
down_revision: Union[str, Sequence[str], None] = "022_fable5_showcase"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

SYSTEM_USER_ID = "00000000-0000-4000-8000-000000000001"
FREE_SKILL_ID = "33333333-3333-4333-8333-333333333303"
FREE_SHOWCASE_ID = "55555555-5555-4555-8555-555555555505"
PREMIUM_SKILL_ID = "33333333-3333-4333-8333-333333333304"
PREMIUM_SHOWCASE_ID = "55555555-5555-4555-8555-555555555506"

FREE_CREW = {
    "steps": [
        {"id": "plan", "type": "llm", "model": "qwen3.6-27b-fable5", "title": "Planner Agent"},
        {"id": "implement", "type": "llm", "model": "qwen3.6-27b-fable5", "title": "Implementer Agent"},
        {"id": "review", "type": "llm", "model": "qwen3.6-27b-fable5", "title": "Code Reviewer"},
        {"id": "qa", "type": "llm", "model": "qwen3.6-27b-fable5", "title": "QA Gate"},
    ]
}

PREMIUM_CREW = {
    "steps": [
        {"id": "plan", "type": "llm", "model": "gpt-4.1", "title": "Planner Agent"},
        {"id": "implement", "type": "llm", "model": "gpt-4.1", "title": "Implementer Agent"},
        {"id": "review", "type": "llm", "model": "grok-3-mini", "title": "Code Reviewer"},
        {"id": "qa", "type": "llm", "model": "grok-3-mini", "title": "QA Gate"},
    ]
}

FREE_DESCRIPTION = (
    "Free local Fable-5 LoRA agent: plan → implement → review → QA on "
    "hotdogs/qwen3.6-27b-fable5-lora via Ollama ($0 run fee, $0 LLM). "
    "Requires OLLAMA_ENABLED + GPU. No cloud fallback."
)

PREMIUM_DESCRIPTION = (
    "Fable-5-style coding agent Pro ($5/run): plan → implement → review → QA. "
    "Cloud OpenAI GPT-4.1 (plan + code) + Grok 3 Mini (review + QA) — "
    "no GPU or Ollama required. Inspired by Fable-5 trace patterns."
)

FREE_SAMPLE = """## Planner Agent
**Engine:** qwen3.6-27b-fable5 (local LoRA)

**Exploration:** Read `main.py`; Grep `router` in `app/`.

**Plan:**
1. Add `GET /health` in `main.py`
2. Add `tests/test_health.py` → `pytest -q`

## Implementer Agent
```python
@app.get("/health")
def health():
    return {"status": "ok"}
```

## Code Reviewer
Score 8/10 — optional DB ping for prod.

## QA Gate
Verdict: **READY**"""

PREMIUM_SAMPLE = """## Planner Agent
**Engine:** GPT-4.1

**Exploration:** Map FastAPI route module; locate existing test layout.

**Plan:** 4 numbered steps with file paths + pytest verify commands.

## Implementer Agent
Full `main.py` patch + complete `tests/test_health.py` (no omissions).

## Code Reviewer (Grok 3 Mini)
Score 9/10 — security + edge cases covered; 1 P2 style nit.

## QA Gate
Verdict: **READY** — tests, types, no secrets."""


def upgrade() -> None:
    op.execute(
        sa.text(
            """
            UPDATE expert_skills
            SET name = :name,
                description = :description,
                crew_config = CAST(:crew_config AS jsonb),
                capabilities = CAST(:capabilities AS jsonb)
            WHERE id = CAST(:skill_id AS uuid)
            """
        ).bindparams(
            name="Fable-5 Coding Agent (Free — Local LoRA)",
            description=FREE_DESCRIPTION,
            crew_config=json.dumps(FREE_CREW),
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
            skill_id=FREE_SKILL_ID,
        )
    )
    op.execute(
        sa.text(
            """
            UPDATE skill_showcases
            SET title = :title,
                summary = :summary,
                highlights = CAST(:highlights AS jsonb),
                sample_output = :sample_output,
                deliverables = CAST(:deliverables AS jsonb),
                stats = CAST(:stats AS jsonb),
                sort_order = 1
            WHERE id = CAST(:showcase_id AS uuid)
            """
        ).bindparams(
            title="FastAPI health endpoint — local Fable-5 LoRA",
            summary=(
                "Runs on hotdogs/qwen3.6-27b-fable5-lora via Ollama — closest to the "
                "HuggingFace adapter. $0 run fee and $0 LLM when your GPU is configured."
            ),
            highlights=json.dumps(
                [
                    "qwen3.6-27b-fable5 LoRA",
                    "All 4 steps on local GPU",
                    "$0 marketplace + $0 LLM",
                    "Fable-5 trace patterns",
                ]
            ),
            sample_output=FREE_SAMPLE,
            deliverables=json.dumps(
                [
                    "Exploration notes + step plan",
                    "Copy-paste code / diffs",
                    "Local LoRA code review",
                    "QA checklist + verdict",
                ]
            ),
            stats=json.dumps(
                {
                    "score": "READY",
                    "engines": "qwen3.6-27b-fable5 (Ollama)",
                    "runtime": "3–8 minutes (GPU)",
                }
            ),
            showcase_id=FREE_SHOWCASE_ID,
        )
    )

    expert_skills = sa.table(
        "expert_skills",
        sa.column("id", postgresql.UUID),
        sa.column("slug", sa.String),
        sa.column("name", sa.String),
        sa.column("description", sa.Text),
        sa.column("category", sa.String),
        sa.column("pack_slug", sa.String),
        sa.column("crew_config", postgresql.JSONB),
        sa.column("capabilities", postgresql.JSONB),
        sa.column("price_usd_per_run", sa.Numeric),
        sa.column("owner_id", postgresql.UUID),
        sa.column("is_active", sa.Boolean),
    )
    op.bulk_insert(
        expert_skills,
        [
            {
                "id": PREMIUM_SKILL_ID,
                "slug": "fable5-coding-agent-premium",
                "name": "Fable-5 Coding Agent Pro",
                "description": PREMIUM_DESCRIPTION,
                "category": "coding",
                "pack_slug": "fable5-coding-agent-premium",
                "crew_config": PREMIUM_CREW,
                "capabilities": [
                    "coding-agent",
                    "tool-use",
                    "multi-step-reasoning",
                    "code-review",
                    "fable5",
                    "openai",
                    "grok",
                    "premium",
                ],
                "price_usd_per_run": "5.0000",
                "owner_id": SYSTEM_USER_ID,
                "is_active": True,
            }
        ],
    )

    showcases = sa.table(
        "skill_showcases",
        sa.column("id", postgresql.UUID),
        sa.column("expert_skill_id", postgresql.UUID),
        sa.column("title", sa.String),
        sa.column("site_name", sa.String),
        sa.column("site_url", sa.String),
        sa.column("summary", sa.Text),
        sa.column("metric_label", sa.String),
        sa.column("metric_value", sa.String),
        sa.column("highlights", postgresql.JSONB),
        sa.column("sort_order", sa.Integer),
        sa.column("is_featured", sa.Boolean),
        sa.column("is_active", sa.Boolean),
        sa.column("sample_output", sa.Text),
        sa.column("deliverables", postgresql.JSONB),
        sa.column("stats", postgresql.JSONB),
        sa.column("before_after", postgresql.JSONB),
    )
    op.bulk_insert(
        showcases,
        [
            {
                "id": PREMIUM_SHOWCASE_ID,
                "expert_skill_id": PREMIUM_SKILL_ID,
                "title": "Stripe webhook handler — cloud Pro pipeline",
                "site_name": "Sample API task",
                "site_url": "",
                "summary": (
                    "No GPU? Pro runs GPT-4.1 + Grok 3 Mini in the cloud. "
                    "Deeper plans, complete files, strict review — $5/run marketplace fee."
                ),
                "metric_label": "QA verdict",
                "metric_value": "READY",
                "highlights": [
                    "GPT-4.1 plan + implement",
                    "Grok 3 Mini review + QA",
                    "No Ollama required",
                    "$5/run — cloud premium",
                ],
                "sort_order": -2,
                "is_featured": True,
                "is_active": True,
                "sample_output": PREMIUM_SAMPLE,
                "deliverables": [
                    "Deep exploration + step plan",
                    "Production-grade code blocks",
                    "Senior code review + patches",
                    "Strict QA READY verdict",
                ],
                "stats": {
                    "score": "READY",
                    "engines": "GPT-4.1 + Grok 3 Mini",
                    "runtime": "3–6 minutes",
                },
                "before_after": None,
            }
        ],
    )


def downgrade() -> None:
    op.execute(f"DELETE FROM skill_showcases WHERE id = '{PREMIUM_SHOWCASE_ID}'")
    op.execute(f"DELETE FROM expert_skills WHERE id = '{PREMIUM_SKILL_ID}'")
    gemini_crew = {
        "steps": [
            {"id": "plan", "type": "llm", "model": "gemini-2.5-flash", "title": "Planner Agent"},
            {"id": "implement", "type": "llm", "model": "gemini-2.5-flash", "title": "Implementer Agent"},
            {"id": "review", "type": "llm", "model": "grok-3-mini", "title": "Code Reviewer"},
            {"id": "qa", "type": "llm", "model": "grok-3-mini", "title": "QA Gate"},
        ]
    }
    op.execute(
        sa.text(
            """
            UPDATE expert_skills
            SET name = 'Fable-5 Coding Agent (Free)',
                description = :description,
                crew_config = CAST(:crew_config AS jsonb),
                capabilities = CAST(:capabilities AS jsonb)
            WHERE id = CAST(:skill_id AS uuid)
            """
        ).bindparams(
            description=(
                "Free Fable-5 coding agent playbook: plan → implement → review → QA. "
                "Runs on Gemini 2.5 Flash (plan + code) and Grok 3 Mini (review + QA) — "
                "$0 marketplace fee. Optional local Ollama + fable5 LoRA when configured."
            ),
            crew_config=json.dumps(gemini_crew),
            capabilities=json.dumps(
                ["coding-agent", "tool-use", "multi-step-reasoning", "code-review", "fable5", "gemini", "grok"]
            ),
            skill_id=FREE_SKILL_ID,
        )
    )