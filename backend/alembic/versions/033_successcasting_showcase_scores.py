"""SuccessCasting showcase — 100% before/after scorecard

Revision ID: 033_successcasting_scores
Revises: 032_fix_bot_ai_free
Create Date: 2026-06-21

"""
import json
from typing import Sequence, Union

from alembic import op

revision: str = "033_successcasting_scores"
down_revision: Union[str, Sequence[str], None] = "032_fix_bot_ai_free"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

SHOWCASE_ID = "55555555-5555-4555-8555-555555555515"

BEFORE_AFTER = {
    "score_before": "25%",
    "score_after": "100%",
    "category_scores": {
        "before": {
            "discoverability": 25,
            "content": 0,
            "bot_access": 25,
            "protocol": 0,
            "commerce": 100,
            "overall": 25,
        },
        "after": {
            "discoverability": 100,
            "content": 100,
            "bot_access": 100,
            "protocol": 100,
            "commerce": 100,
            "overall": 100,
        },
    },
    "bots": [
        {"name": "GPTBot", "before": "200, no Content-Signal", "after": "200 + policy header"},
        {"name": "ClaudeBot", "before": "200, no Content-Signal", "after": "200 + policy header"},
        {"name": "PerplexityBot", "before": "200, no Content-Signal", "after": "200 + policy header"},
        {"name": "OAI-SearchBot", "before": "200, no Content-Signal", "after": "200 + policy header"},
        {"name": "ChatGPT-User", "before": "200, no Content-Signal", "after": "200 + policy header"},
        {"name": "Google-Extended", "before": "200, no Content-Signal", "after": "200 + policy header"},
    ],
    "fixes_applied": [
        "agents.txt published (404 → 200)",
        "Content-Signal: ai-train=no, search=yes, ai-input=yes on all public routes",
        "llms.txt — 28 Markdown links + agents.txt link",
        "robots.txt — Applebot + full AI crawler roster",
        "Link headers — llms.txt, ai.txt, agents.txt",
        "Markdown negotiation — Accept: text/markdown returns text/markdown",
        "Homepage H1: 2 → 1; /products H1: 0 → 1",
        "WebMCP data-tool* hints on RFQ form",
    ],
    "snapshots": {
        "before_file": "references/successcasting-before.json",
        "after_file": "references/successcasting-after.json",
        "audit_script": "scripts/audit-agent-ready.mjs",
    },
}

SAMPLE_OUTPUT = """## Before scan (25% overall — isitagentready categories)
| Category | Score |
|----------|-------|
| Discoverability | 25% (1/4) |
| Content | 0% (0/1) |
| Bot Access | 25% (1/4) |
| Protocol | 0% (0/3) |
| Commerce | N/A |
| **Overall** | **25%** |

P0: agents.txt 404 · Content-Signal missing · ai.txt ai-train=yes
P1: llms.txt bare URLs · no Link headers · no Markdown negotiation

## Fixes deployed
agents.txt · Content-Signal headers · llms.txt Markdown · robots Applebot · WebMCP hints

## After scan (100% every category — live 2026-06-21)
| Category | Score |
|----------|-------|
| Discoverability | 100% (4/4) |
| Content | 100% (1/1) |
| Bot Access | 100% (4/4) |
| Protocol | 100% (3/3) |
| Commerce | N/A (100%) |
| **Overall** | **100%** |

likelyIssues: [] · Verify: https://isitagentready.com/"""


def upgrade() -> None:
    before_after_json = json.dumps(BEFORE_AFTER).replace("'", "''")
    sample = SAMPLE_OUTPUT.replace("'", "''")
    op.execute(
        f"""
        UPDATE skill_showcases
        SET metric_label = 'Overall score',
            metric_value = '25% → 100%',
            summary = 'Documented before snapshot (25%%), production fixes, live after audit (100%% in every isitagentready category). Reference case for Fix Bot AI free scan.',
            highlights = '["25%% → 100%% all categories", "Live audit JSON saved", "successcasting.com", "isitagentready.com rubric"]'::jsonb,
            stats = '{{"score": "25%% → 100%%", "time_saved": "~3 hours", "deliverables_count": "5+ files", "runtime": "2–4 min"}}'::jsonb,
            before_after = '{before_after_json}'::jsonb,
            sample_output = '{sample}'
        WHERE id = '{SHOWCASE_ID}'
        """
    )


def downgrade() -> None:
    pass