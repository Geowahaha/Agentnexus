"""Fable-5 showcase: Gemini/Grok copy and sample output

Revision ID: 022_fable5_showcase
Revises: 021_fable5_gemini_grok
Create Date: 2026-06-20

"""
import json
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "022_fable5_showcase"
down_revision: Union[str, Sequence[str], None] = "021_fable5_gemini_grok"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

SHOWCASE_ID = "55555555-5555-4555-8555-555555555505"

SAMPLE_OUTPUT = """## Planner Agent
**Goal:** Add `GET /health` to FastAPI returning `{"status":"ok"}` with pytest coverage.

**Exploration notes:**
- Read `backend/app/main.py` — route registration
- Grep `test_` under `backend/tests/` — pytest layout

**Plan:**
1. Add `@app.get("/health")` in `main.py` → verify: `curl localhost:8000/health`
2. Create `tests/test_health.py` → verify: `pytest -q tests/test_health.py`

## Implementer Agent
```python
@app.get("/health")
def health():
    return {"status": "ok"}
```

```bash
cd backend && pytest -q tests/test_health.py
```

## Code Reviewer
**Score:** 8/10 — solid; optional DB ping for production readiness.

## QA Gate
| Check | Result |
|-------|--------|
| Tests listed | PASS |
| No secrets | PASS |
| **Verdict** | **READY** |"""

SHOWCASE_STATS = {
    "score": "READY",
    "time_saved": "~2 hours vs manual spec",
    "deliverables_count": "Plan + code + review + QA",
    "runtime": "2–5 minutes",
    "engines": "Gemini 2.5 Flash + Grok 3 Mini",
}


def upgrade() -> None:
    op.execute(
        sa.text(
            """
            UPDATE skill_showcases
            SET summary = :summary,
                metric_label = :metric_label,
                metric_value = :metric_value,
                highlights = CAST(:highlights AS jsonb),
                sample_output = :sample_output,
                deliverables = CAST(:deliverables AS jsonb),
                stats = CAST(:stats AS jsonb),
                sort_order = -1,
                is_featured = true
            WHERE id = CAST(:showcase_id AS uuid)
            """
        ).bindparams(
            summary=(
                "Describe a coding task in plain language. Fable-5 pipeline returns "
                "a step plan, implementation snippets, code review, and QA verdict — "
                "free marketplace fee on Gemini 2.5 Flash + Grok 3 Mini."
            ),
            metric_label="QA verdict",
            metric_value="READY",
            highlights=json.dumps(
                [
                    "Fable-5 agent traces",
                    "Gemini 2.5 Flash (plan + code)",
                    "Grok 3 Mini (review + QA)",
                    "$0 marketplace fee",
                ]
            ),
            sample_output=SAMPLE_OUTPUT,
            deliverables=json.dumps(
                [
                    "Exploration notes + step plan",
                    "Copy-paste code / diffs",
                    "Code review score + patches",
                    "QA checklist + READY verdict",
                ]
            ),
            stats=json.dumps(SHOWCASE_STATS),
            showcase_id=SHOWCASE_ID,
        )
    )


def downgrade() -> None:
    op.execute(
        sa.text(
            """
            UPDATE skill_showcases
            SET summary = :summary,
                highlights = CAST(:highlights AS jsonb),
                sample_output = :sample_output,
                deliverables = CAST(:deliverables AS jsonb),
                stats = CAST(:stats AS jsonb),
                sort_order = 0
            WHERE id = CAST(:showcase_id AS uuid)
            """
        ).bindparams(
            summary=(
                "Describe a coding task in plain language. Fable-5 pipeline returns "
                "a step plan, implementation snippets, code review, and QA verdict — "
                "free to run; $0 LLM cost with local Ollama + fable5 LoRA."
            ),
            highlights=json.dumps(
                [
                    "Fable-5 agent traces",
                    "Local Qwen3.6 + LoRA",
                    "Cloud fallback",
                    "$0 marketplace fee",
                ]
            ),
            sample_output=(
                "## Planner Agent\n**Goal:** Add health check endpoint to FastAPI app.\n\n"
                "## QA Gate\nVerdict: **READY** — tests pass, no secrets."
            ),
            deliverables=json.dumps(
                [
                    "Step-by-step plan",
                    "Copy-paste code / diffs",
                    "Code review score",
                    "QA checklist + verdict",
                ]
            ),
            stats=json.dumps(
                {
                    "score": "READY",
                    "time_saved": "~2 hours vs manual spec",
                    "deliverables_count": "Plan + code + review + QA",
                    "runtime": "2–5 minutes",
                }
            ),
            showcase_id=SHOWCASE_ID,
        )
    )