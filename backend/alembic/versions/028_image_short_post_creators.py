"""Image Post + Short Post creator agents

Revision ID: 028_image_short_post
Revises: 027_lineart_facebook_reel
Create Date: 2026-06-20

"""
import json
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "028_image_short_post"
down_revision: Union[str, Sequence[str], None] = "027_lineart_facebook_reel"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

SYSTEM_USER_ID = "00000000-0000-4000-8000-000000000001"
IMAGE_POST_SKILL_ID = "33333333-3333-4333-8333-333333333307"
SHORT_POST_SKILL_ID = "33333333-3333-4333-8333-333333333308"
IMAGE_POST_SHOWCASE_ID = "55555555-5555-4555-8555-555555555513"
SHORT_POST_SHOWCASE_ID = "55555555-5555-4555-8555-555555555514"

IMAGE_POST_CREW_CONFIG = {
    "input_mode": "task",
    "pipeline_label": "มุมโพสต์ → แคปชัน+CTA → Prompt ภาพ → QA ปล่อย",
    "run_title": "รัน Image Post Creator",
    "run_hint": "บอกหัวข้อ + แพลตฟอร์ม (IG/FB/LinkedIn) — ได้แคปชัน + prompt ภาพ 1:1 หรือ 4:5",
    "run_cta": "Run Image Post — ~$1.11",
    "steps": [
        {
            "id": "angle_research",
            "type": "llm",
            "model": "gemini-2.5-flash",
            "title": "Angle & Hook Research",
        },
        {
            "id": "caption_draft",
            "type": "llm",
            "model": "gemini-2.5-flash",
            "title": "Caption + CTA Draft",
        },
        {
            "id": "image_prompt",
            "type": "llm",
            "model": "grok-3-mini",
            "title": "Image Prompt (1:1 / 4:5)",
        },
        {
            "id": "qa",
            "type": "llm",
            "model": "grok-3-mini",
            "title": "Publish QA",
        },
    ],
}

SHORT_POST_CREW_CONFIG = {
    "input_mode": "task",
    "pipeline_label": "มุมโพสต์ → ร่าง 3 แบบ → ขัดเกลา → QA ปล่อย",
    "run_title": "รัน Short Post Creator",
    "run_hint": "บอกหัวข้อ + แพลตฟอร์ม (X/Threads/LinkedIn/FB) — ได้โพสต์สั้นพร้อมโพสต์",
    "run_cta": "Run Short Post — ~$0.61",
    "steps": [
        {
            "id": "research",
            "type": "llm",
            "model": "gemini-2.5-flash",
            "title": "Angle & Platform Research",
        },
        {
            "id": "draft",
            "type": "llm",
            "model": "gemini-2.5-flash",
            "title": "Draft Variants (3 hooks)",
        },
        {
            "id": "edit",
            "type": "llm",
            "model": "grok-3-mini",
            "title": "Polish + Thread Split",
        },
        {
            "id": "qa",
            "type": "llm",
            "model": "grok-3-mini",
            "title": "Publish QA",
        },
    ],
}

IMAGE_POST_CAPABILITIES = [
    "content",
    "social",
    "image-prompts",
    "caption",
    "copywriting",
    "thai-content",
]

SHORT_POST_CAPABILITIES = [
    "content",
    "social",
    "copywriting",
    "thai-content",
]

IMAGE_POST_DESCRIPTION = (
    "สร้างโพสต์รูปภาพโซเชียล — มุม hook → แคปชัน + CTA + alt text + hashtag "
    "→ prompt ภาพเต็ม (1:1 หรือ 4:5) → QA ก่อนโพสต์. "
    "รองรับ Instagram, Facebook, LinkedIn. Buyer render ภาพเอง (Grok Imagine, Canva ฯลฯ)."
)

SHORT_POST_DESCRIPTION = (
    "สร้างโพสต์ข้อความสั้น — มุม + ข้อจำกัดแพลตฟอร์ม → ร่าง 3 แบบ hook ต่างกัน "
    "→ ขัดเกลาโพสต์หลัก + backup (+ thread ถ้าขอ) → QA ก่อนโพสต์. "
    "รองรับ X, Threads, LinkedIn, Facebook."
)

IMAGE_POST_SAMPLE = """## Angle & Hook Research
**Angle 1:** 5 นาทีที่เปลี่ยนวันของคุณ — hook สำหรับ IG 4:5
**Recommended:** Angle 1 — visual นาฬิกา + คนเปลี่ยนท่าทาง

## Caption + CTA Draft
**Hook:** คุณไม่ต้องการเวลาเพิ่ม — คุณต้องการ 5 นาทีที่ถูกต้อง
**Body:** …
**CTA:** บันทึกโพสต์นี้แล้วลองพรุ่งนี้เช้า
**Alt:** นาฬิกา 5 นาทีกับคนเริ่มต้นวันใหม่
**Hashtags:** #productive #morningroutine #5minutes

## Image Prompt (4:5)
Minimal flat illustration, 4:5 portrait, soft morning light,
scene: person resetting alarm clock with calm smile,
text overlay: "5 นาที" centered top-third

## Publish QA
**Verdict:** READY — caption hook strong, prompt complete, 4:5 stated."""

SHORT_POST_SAMPLE = """## Angle & Platform Research
**Platform:** X (280 chars)
**Angle:** Hot take — multitasking ทำให้ช้าลง

## Draft Variants
**A (278 chars):** Multitasking ไม่ได้ทำให้คุณเร็วขึ้น — มันทำให้คุณผิดพลาดบ่อยขึ้น…
**B (265 chars):** …
**C (241 chars):** …

## Polish + Thread Split
**Primary:** [final 276-char post]
**Backup:** [variant B polished]

## Publish QA
**Verdict:** READY — within 280 chars, hook first line, CTA to reply."""

IMAGE_POST_STATS = {
    "score": "READY",
    "time_saved": "~45 min vs manual caption + prompt",
    "deliverables_count": "Angles + caption + image prompt + QA",
    "runtime": "3–5 minutes",
    "engines": "Gemini 2.5 Flash + Grok 3 Mini",
    "cost": "$0.99 run + ~$0.12 LLM",
}

SHORT_POST_STATS = {
    "score": "READY",
    "time_saved": "~20 min vs manual drafting",
    "deliverables_count": "3 variants + polished post + QA",
    "runtime": "2–4 minutes",
    "engines": "Gemini 2.5 Flash + Grok 3 Mini",
    "cost": "$0.49 run + ~$0.12 LLM",
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
                "id": IMAGE_POST_SKILL_ID,
                "slug": "image-post-creator",
                "name": "Image Post Creator",
                "description": IMAGE_POST_DESCRIPTION,
                "category": "content",
                "pack_slug": "image-post-creator",
                "crew_config": IMAGE_POST_CREW_CONFIG,
                "capabilities": json.dumps(IMAGE_POST_CAPABILITIES),
                "price_usd_per_run": "0.99",
                "owner_id": SYSTEM_USER_ID,
                "is_active": True,
            },
            {
                "id": SHORT_POST_SKILL_ID,
                "slug": "short-post-creator",
                "name": "Short Post Creator",
                "description": SHORT_POST_DESCRIPTION,
                "category": "content",
                "pack_slug": "short-post-creator",
                "crew_config": SHORT_POST_CREW_CONFIG,
                "capabilities": json.dumps(SHORT_POST_CAPABILITIES),
                "price_usd_per_run": "0.49",
                "owner_id": SYSTEM_USER_ID,
                "is_active": True,
            },
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
                "id": IMAGE_POST_SHOWCASE_ID,
                "expert_skill_id": IMAGE_POST_SKILL_ID,
                "title": "5 นาทีที่เปลี่ยนวัน — IG image post",
                "site_name": "Instagram feed draft",
                "site_url": "https://obolla.com",
                "summary": (
                    "จากไอเดียโพสต์ → มุม hook + แคปชัน CTA + prompt ภาพ 4:5 "
                    "พร้อม hashtag และ QA ก่อนโพสต์."
                ),
                "metric_label": "Before → After",
                "metric_value": "ไอเดีย → READY image post pack",
                "highlights": [
                    "3–5 scroll-stop angles",
                    "Caption + alt text + hashtags",
                    "Full 1:1 or 4:5 image prompt",
                    "Platform publish QA",
                ],
                "sort_order": 0,
                "is_featured": True,
                "is_active": True,
                "sample_output": IMAGE_POST_SAMPLE,
                "deliverables": [
                    "Angle & hook research",
                    "Caption + CTA + alt text",
                    "Image prompt with aspect ratio",
                    "Publish QA + READY verdict",
                ],
                "stats": json.dumps(IMAGE_POST_STATS),
                "before_after": json.dumps(
                    {
                        "score_before": "ไอเดียโพสต์ — ยังไม่มีแคปชัน",
                        "score_after": "READY — caption + image prompt pack",
                        "bots": [],
                        "fixes_applied": [
                            "Hook-first caption structure",
                            "Complete image prompt with aspect ratio",
                            "Hashtag set for target platform",
                            "QA READY verdict",
                        ],
                    }
                ),
            },
            {
                "id": SHORT_POST_SHOWCASE_ID,
                "expert_skill_id": SHORT_POST_SKILL_ID,
                "title": "Hot take multitasking — X post",
                "site_name": "X (Twitter) text draft",
                "site_url": "https://obolla.com",
                "summary": (
                    "จากหัวข้อ → 3 variants hook ต่างกัน → โพสต์หลักขัดเกลา "
                    "พร้อม char count และ QA ก่อนโพสต์."
                ),
                "metric_label": "Before → After",
                "metric_value": "หัวข้อ → READY short post",
                "highlights": [
                    "Platform char-limit aware",
                    "3 hook variants",
                    "Primary + backup polished copy",
                    "Thread split on request",
                ],
                "sort_order": 0,
                "is_featured": True,
                "is_active": True,
                "sample_output": SHORT_POST_SAMPLE,
                "deliverables": [
                    "Angle & platform research",
                    "3 draft variants with char counts",
                    "Polished primary + backup post",
                    "Publish QA + READY verdict",
                ],
                "stats": json.dumps(SHORT_POST_STATS),
                "before_after": json.dumps(
                    {
                        "score_before": "หัวข้อ — ยังไม่มีโพสต์สั้น",
                        "score_after": "READY — copy-paste post",
                        "bots": [],
                        "fixes_applied": [
                            "Hook-first line for X feed",
                            "Within 280-char limit",
                            "CTA to drive replies",
                            "QA READY verdict",
                        ],
                    }
                ),
            },
        ],
    )


def downgrade() -> None:
    op.execute(sa.text(f"DELETE FROM skill_showcases WHERE id = '{IMAGE_POST_SHOWCASE_ID}'"))
    op.execute(sa.text(f"DELETE FROM skill_showcases WHERE id = '{SHORT_POST_SHOWCASE_ID}'"))
    op.execute(sa.text(f"DELETE FROM expert_skills WHERE id = '{IMAGE_POST_SKILL_ID}'"))
    op.execute(sa.text(f"DELETE FROM expert_skills WHERE id = '{SHORT_POST_SKILL_ID}'"))