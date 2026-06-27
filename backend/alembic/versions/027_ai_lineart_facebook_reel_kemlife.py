"""AI line-art Facebook Reels template (KEMLIFE-style)

Revision ID: 027_lineart_facebook_reel
Revises: 026_lineart_youtube
Create Date: 2026-06-20

"""
import json
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "027_lineart_facebook_reel"
down_revision: Union[str, Sequence[str], None] = "026_lineart_youtube"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

SYSTEM_USER_ID = "00000000-0000-4000-8000-000000000001"
EXPERT_SKILL_ID = "33333333-3333-4333-8333-333333333306"
SHOWCASE_ID = "55555555-5555-4555-8555-555555555512"

CREW_CONFIG = {
    "input_mode": "task",
    "pipeline_label": "Hook → บทสั้น+เวลา → Prompt 9:16 → QA ปล่อย Reels",
    "run_title": "รันเทมเพลต Facebook Reels การ์ตูนลายเส้น",
    "run_hint": "เล่า niche หรือหัวข้อ Reel — ได้บท 30–90s + prompt ภาพ MS Paint 9:16",
    "steps": [
        {
            "id": "hook_research",
            "type": "llm",
            "model": "gemini-2.5-flash",
            "title": "Hook & Angle Research",
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
            "title": "Shot Prompts (9:16 MS Paint)",
        },
        {
            "id": "qa",
            "type": "llm",
            "model": "grok-3-mini",
            "title": "Reels Publish QA",
        },
    ],
}

CAPABILITIES = [
    "content",
    "facebook",
    "reels",
    "faceless",
    "image-prompts",
    "video-prep",
    "thai-content",
    "editing",
]

DESCRIPTION = (
    "เทมเพลต Facebook Reels การ์ตูนลายเส้นแบบ faceless — hook วินาทีแรก → บท 30–90s พร้อม timestamp "
    "→ prompt ภาพ MS Paint 9:16 ทีละช็อต → caption/hashtag + QA ก่อนปล่อย. "
    "อิง workflow KEMLIFE (Reels แนวตั้ง). Buyer รัน Higgsfield/CapCut เอง — agent จัดบทและ prompt ให้."
)

SAMPLE_OUTPUT = """## Hook & Angle Research
**Angle 1:** ทำไมคุณลืมความฝันใน 5 นาที — hook วินาทีแรก
**Scroll-stop:** คำถามที่มีคำตอบเดียว + ความลับของร่างกาย

## Script + Timestamps
0:00 — คุณลืมความฝันทุกเช้า...
0:02 — ไม่ใช่เพราะความจำแย่...
0:05 — สมองลบมันโดยเฉพาะ...

## Shot Prompts (9:16 MS Paint)
| Time | Line | On-screen | Prompt | File |
| 0:00 | คุณลืม... | ลืมฝัน? | MS Paint..., stick figure waking confused | 0-00 |
| 0:02 | ไม่ใช่เพราะ... | สมองลบ | brain erasing bubble | 0-02 |

## Reels Publish QA
**Caption:** ทำไมคุณลืมความฝันทุกเช้า? สมองลบมันโดยเฉพาะ — อธิบายใน 60 วิ
**Hashtags:** #ความรู้ #จิตวิทยา #Reels
**Verdict:** READY — 22 shots, all 9:16, hook text at 0:00."""

SHOWCASE_STATS = {
    "score": "READY",
    "time_saved": "~4 hours vs manual script + prompts",
    "deliverables_count": "Hooks + script + 9:16 prompt table + Reels QA",
    "runtime": "4–7 minutes",
    "engines": "Gemini 2.5 Flash + Grok 3 Mini",
    "cost": "$0.99 run + ~$0.12 LLM",
}

BEFORE_AFTER = {
    "score_before": "ไอเดีย Reel — ยังไม่มี hook วินาทีแรก",
    "score_after": "READY — บท 60s + 20+ prompt ภาพ MS Paint 9:16",
    "bots": [],
    "fixes_applied": [
        "3 scroll-stop hooks with 1-second openers",
        "60s script with 1–3s timestamp density",
        "Per-shot MS Paint 9:16 prompts + on-screen text",
        "Facebook caption + hashtags + CapCut vertical checklist",
        "QA READY verdict",
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
                "slug": "ai-lineart-facebook-reel-kemlife",
                "name": "Facebook Reels การ์ตูนลายเส้น AI (KEMLIFE)",
                "description": DESCRIPTION,
                "category": "content",
                "pack_slug": "ai-lineart-facebook-reel-kemlife",
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
                "title": "ความลับของร่างกาย — Reel ลายเส้น 60 วิ",
                "site_name": "Faceless Facebook Reel draft",
                "site_url": "https://www.facebook.com/reel/2039899173277798",
                "summary": (
                    "จากไอเดีย Reel → บท 60s พร้อม hook วินาทีแรก + 20 prompt ภาพ MS Paint 9:16 "
                    "พร้อม caption/hashtag สำหรับ Facebook — สไตล์ KEMLIFE."
                ),
                "metric_label": "Before → After",
                "metric_value": "ไอเดีย → READY Reel pack",
                "highlights": [
                    "Hook วินาทีแรกหยุด scroll",
                    "บท 30–90s + timestamp ถี่",
                    "Prompt MS Paint 9:16 ห้ามสวย",
                    "Caption + hashtag + QA Reels",
                ],
                "sort_order": -1,
                "is_featured": True,
                "is_active": True,
                "sample_output": SAMPLE_OUTPUT,
                "deliverables": [
                    "Hook & angle research",
                    "Timestamped short script",
                    "Per-shot 9:16 image prompt table",
                    "Facebook Reels publish QA + caption",
                ],
                "stats": json.dumps(SHOWCASE_STATS),
                "before_after": json.dumps(BEFORE_AFTER),
            }
        ],
    )


def downgrade() -> None:
    op.execute(sa.text(f"DELETE FROM skill_showcases WHERE id = '{SHOWCASE_ID}'"))
    op.execute(sa.text(f"DELETE FROM expert_skills WHERE id = '{EXPERT_SKILL_ID}'"))