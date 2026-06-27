"""Image Post Creator — add Grok Imagine image_gen step

Revision ID: 029_image_post_generate
Revises: 028_image_short_post
Create Date: 2026-06-20

"""
import json
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "029_image_post_generate"
down_revision: Union[str, Sequence[str], None] = "028_image_short_post"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

IMAGE_POST_SKILL_ID = "33333333-3333-4333-8333-333333333307"

UPDATED_CREW_CONFIG = {
    "input_mode": "task",
    "pipeline_label": "มุมโพสต์ → แคปชัน → Prompt → Gen รูป → QA",
    "run_title": "รัน Image Post Creator",
    "run_hint": "บอกหัวข้อ + แพลตฟอร์ม — ได้แคปชัน + รูปจริงจาก Grok Imagine (1:1 หรือ 4:5)",
    "run_cta": "Run Image Post — ~$1.16",
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
            "id": "image_generate",
            "type": "image_gen",
            "provider": "xai",
            "model": "grok-imagine-image-quality",
            "prompt_step": "image_prompt",
            "title": "Generate Image (Grok Imagine)",
        },
        {
            "id": "qa",
            "type": "llm",
            "model": "grok-3-mini",
            "title": "Publish QA",
        },
    ],
}

UPDATED_DESCRIPTION = (
    "สร้างโพสต์รูปภาพโซเชียล — มุม hook → แคปชัน + CTA + alt text + hashtag "
    "→ prompt ภาพ → **สร้างรูปจริงด้วย Grok Imagine** → QA ก่อนโพสต์. "
    "รองรับ Instagram, Facebook, LinkedIn."
)


def upgrade() -> None:
    op.execute(
        sa.text(
            """
            UPDATE expert_skills
            SET
                description = :description,
                crew_config = CAST(:crew_config AS jsonb),
                capabilities = CAST(:capabilities AS jsonb)
            WHERE id = CAST(:skill_id AS uuid)
            """
        ).bindparams(
            skill_id=IMAGE_POST_SKILL_ID,
            description=UPDATED_DESCRIPTION,
            crew_config=json.dumps(UPDATED_CREW_CONFIG),
            capabilities=json.dumps(
                [
                    "content",
                    "social",
                    "image-prompts",
                    "image-generation",
                    "caption",
                    "copywriting",
                    "thai-content",
                ]
            ),
        )
    )


def downgrade() -> None:
    old_crew = {
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
    op.execute(
        sa.text(
            """
            UPDATE expert_skills
            SET
                description = :description,
                crew_config = CAST(:crew_config AS jsonb),
                capabilities = CAST(:capabilities AS jsonb)
            WHERE id = CAST(:skill_id AS uuid)
            """
        ).bindparams(
            skill_id=IMAGE_POST_SKILL_ID,
            description=(
                "สร้างโพสต์รูปภาพโซเชียล — มุม hook → แคปชัน + CTA + alt text + hashtag "
                "→ prompt ภาพเต็ม (1:1 หรือ 4:5) → QA ก่อนโพสต์. "
                "รองรับ Instagram, Facebook, LinkedIn. Buyer render ภาพเอง."
            ),
            crew_config=json.dumps(old_crew),
            capabilities=json.dumps(
                [
                    "content",
                    "social",
                    "image-prompts",
                    "caption",
                    "copywriting",
                    "thai-content",
                ]
            ),
        )
    )