"""Fable-5 coding agent free expert skill

Revision ID: 020_fable5_coding
Revises: 019_local_agent_bridge
Create Date: 2026-06-19

"""
import json
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "020_fable5_coding"
down_revision: Union[str, Sequence[str], None] = "019_local_agent_bridge"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

SYSTEM_USER_ID = "00000000-0000-4000-8000-000000000001"
EXPERT_SKILL_ID = "33333333-3333-4333-8333-333333333303"
SHOWCASE_ID = "55555555-5555-4555-8555-555555555505"

CREW_CONFIG = {
    "steps": [
        {
            "id": "plan",
            "type": "llm",
            "model": "qwen3.6-27b-fable5",
            "title": "Planner Agent",
        },
        {
            "id": "implement",
            "type": "llm",
            "model": "qwen3.6-27b-fable5",
            "title": "Implementer Agent",
        },
        {
            "id": "review",
            "type": "llm",
            "model": "gemini-2.5-flash",
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
    "local-llm",
    "fable5",
]

DESCRIPTION = (
    "Free Fable-5 coding agent flow: plan → implement → review → QA. "
    "Uses local Qwen3.6-27B + fable5 LoRA via Ollama when enabled ($0 LLM cost); "
    "falls back to cloud models automatically."
)

SAMPLE_OUTPUT = """## Planner Agent
**Goal:** Add health check endpoint to FastAPI app.

**Plan:**
1. Create `GET /health` returning `{"status":"ok"}`
2. Add pytest in `tests/test_health.py`
3. Verify: `pytest -q`

## Implementer Agent
```python
@app.get("/health")
def health():
    return {"status": "ok"}
```

## Code Reviewer
Score: 8/10 — add DB ping optional for production.

## QA Gate
Verdict: **READY** — tests pass, no secrets."""

SHOWCASE_STATS = {
    "score": "READY",
    "time_saved": "~2 hours vs manual spec",
    "deliverables_count": "Plan + code + review + QA",
    "runtime": "2–5 minutes",
}


def upgrade() -> None:
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
                "id": EXPERT_SKILL_ID,
                "slug": "fable5-coding-agent",
                "name": "Fable-5 Coding Agent (Free)",
                "description": DESCRIPTION,
                "category": "coding",
                "pack_slug": "fable5-coding-agent",
                "crew_config": CREW_CONFIG,
                "capabilities": CAPABILITIES,
                "price_usd_per_run": "0.0000",
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
                "id": SHOWCASE_ID,
                "expert_skill_id": EXPERT_SKILL_ID,
                "title": "FastAPI health endpoint — agent plan + code",
                "site_name": "Sample API task",
                "site_url": "",
                "summary": (
                    "Describe a coding task in plain language. Fable-5 pipeline returns "
                    "a step plan, implementation snippets, code review, and QA verdict — "
                    "free to run; $0 LLM cost with local Ollama + fable5 LoRA."
                ),
                "metric_label": "QA verdict",
                "metric_value": "READY",
                "highlights": [
                    "Fable-5 agent traces",
                    "Local Qwen3.6 + LoRA",
                    "Cloud fallback",
                    "$0 marketplace fee",
                ],
                "sort_order": 0,
                "is_featured": True,
                "is_active": True,
                "sample_output": SAMPLE_OUTPUT,
                "deliverables": [
                    "Step-by-step plan",
                    "Copy-paste code / diffs",
                    "Code review score",
                    "QA checklist + verdict",
                ],
                "stats": SHOWCASE_STATS,
                "before_after": None,
            }
        ],
    )


def downgrade() -> None:
    op.execute(f"DELETE FROM skill_showcases WHERE id = '{SHOWCASE_ID}'")
    op.execute(f"DELETE FROM expert_skills WHERE id = '{EXPERT_SKILL_ID}'")