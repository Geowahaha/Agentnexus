"""AI line-art YouTube channel template (KEMLIFE-style)

Revision ID: 026_lineart_youtube
Revises: 025_community_cases
Create Date: 2026-06-20

"""
import json
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "026_lineart_youtube"
down_revision: Union[str, Sequence[str], None] = "025_community_cases"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

SYSTEM_USER_ID = "00000000-0000-4000-8000-000000000001"
EXPERT_SKILL_ID = "33333333-3333-4333-8333-333333333305"
SHOWCASE_ID = "55555555-5555-4555-8555-555555555511"

CREW_CONFIG = {
    "input_mode": "task",
    "pipeline_label": "หาเรื่อง → บท+เวลา → Prompt ภาพ → QA ปล่อยคลิป",
    "run_title": "รันเทมเพลตช่องการ์ตูนลายเส้น",
    "run_hint": "เล่า niche หรือหัวข้อคลิป — ได้บท timestamp + prompt ภาพ MS Paint 16:9",
    "steps": [
        {
            "id": "topic_research",
            "type": "llm",
            "model": "gemini-2.5-flash",
            "title": "Topic & Hook Research",
        },
        {
            "id": "script",
            "type": "llm",
            "model": "gemini-2.5-flash",
            "title": "Script + Timestamps",
        },
        {
            "id": "image_prompts",
            "type": "llm",
            "model": "grok-3-mini",
            "title": "Shot Prompts (16:9 MS Paint)",
        },
        {
            "id": "qa",
            "type": "llm",
            "model": "grok-3-mini",
            "title": "Edit & Publish QA",
        },
    ],
}

CAPABILITIES = [
    "content",
    "youtube",
    "faceless",
    "image-prompts",
    "video-prep",
    "thai-content",
    "editing",
]

DESCRIPTION = (
    "เทมเพลตช่อง YouTube การ์ตูนลายเส้นแบบ faceless — หาเรื่อง → เขียนบทพร้อม timestamp "
    "→ prompt ภาพ MS Paint 16:9 ทีละช็อต → checklist ตัดต่อ & QA ก่อนปล่อย. "
    "อิง workflow KEMLIFE (สรุปจาก Danny Why / สไตล์ Zenn). "
    "Buyer รัน Higgsfield/CapCut เอง — agent จัดบทและ prompt ให้."
)

SAMPLE_OUTPUT = """## Topic & Hook Research
**Angle 1:** ทำไมร่างกายคุณลืมความฝันใน 5 นาที — หัวข้อจิตวิทยาที่คนกดไม่ได้
**Hook pattern:** คำถามที่มีคำตอบเดียว + ความลับของร่างกาย

## Script + Timestamps
0:00 — คุณเคยฝันแล้วลืมทันทีไหม...
0:04 — สมองของคุณกำลังลบความทรงจำนั้นโดยเฉพาะ...
0:09 — นักวิทยาศาสตร์เรียกว่า active forgetting...

## Shot Prompts (16:9 MS Paint)
| Time | Line | Prompt | File |
| 0:00 | คุณเคยฝัน... | MS Paint beginner..., stick figure in bed confused | 0-00 |
| 0:04 | สมองลบ... | brain erasing dream bubble, ugly lines | 0-04 |

## Edit & Publish QA
**Title options:** ทำไมคุณลืมความฝันใน 5 นาที (ความจริงที่สมองไม่บอก)
**Verdict:** READY — 38 shots, all 16:9, sync map attached."""

SHOWCASE_STATS = {
    "score": "READY",
    "time_saved": "~6 hours vs manual script + prompts",
    "deliverables_count": "Hooks + script + prompt table + QA",
    "runtime": "5–8 minutes",
    "engines": "Gemini 2.5 Flash + Grok 3 Mini",
    "cost": "$0.99 run + ~$0.15 LLM",
}

BEFORE_AFTER = {
    "score_before": "ไอเดียคร่าวๆ — ยังไม่มีบท timestamp",
    "score_after": "READY — บท + 40+ prompt ภาพ MS Paint 16:9",
    "bots": [],
    "fixes_applied": [
        "3 hook titles with curiosity gap",
        "10-min script with 3–7s timestamp density",
        "Per-shot MS Paint prompts + filename map",
        "CapCut assembly + thumbnail title variants",
        "QA READY checklist",
    ],
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
                "slug": "ai-lineart-youtube-kemlife",
                "name": "ช่อง YouTube การ์ตูนลายเส้น AI (KEMLIFE)",
                "description": DESCRIPTION,
                "category": "content",
                "pack_slug": "ai-lineart-youtube-kemlife",
                "crew_config": CREW_CONFIG,
                "capabilities": json.dumps(CAPABILITIES),
                "price_usd_per_run": "0.99",
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
                "title": "ความลับของร่างกาย — คลิปลายเส้น 10 นาที",
                "site_name": "Faceless YouTube draft",
                "site_url": "",
                "summary": (
                    "จากไอเดียคร่าวๆ → บทพากย์พร้อม timestamp + 40 prompt ภาพ MS Paint 16:9 "
                    "พร้อมชื่อไฟล์สำหรับ CapCut — สไตล์ KEMLIFE / Zenn curiosity."
                ),
                "metric_label": "Before → After",
                "metric_value": "ไอเดีย → READY prompt pack",
                "highlights": [
                    "หัวข้อจิก + 3 title hooks",
                    "บท 8–13 นาที + timestamp ถี่",
                    "Prompt MS Paint ห้ามสวย",
                    "QA ก่อนอัป YouTube",
                ],
                "sort_order": -1,
                "is_featured": True,
                "is_active": True,
                "sample_output": SAMPLE_OUTPUT,
                "deliverables": [
                    "Topic & hook research",
                    "Timestamped voiceover script",
                    "Per-shot 16:9 image prompt table",
                    "Edit/publish QA + title/thumbnail",
                ],
                "stats": json.dumps(SHOWCASE_STATS),
                "before_after": json.dumps(BEFORE_AFTER),
            }
        ],
    )


def downgrade() -> None:
    op.execute(sa.text(f"DELETE FROM skill_showcases WHERE id = '{SHOWCASE_ID}'"))
    op.execute(sa.text(f"DELETE FROM expert_skills WHERE id = '{EXPERT_SKILL_ID}'"))