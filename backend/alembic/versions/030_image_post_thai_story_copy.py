"""Image Post — Thai story-episode copy default

Revision ID: 030_image_post_thai_story
Revises: 029_image_post_generate
Create Date: 2026-06-20

"""
import json
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "030_image_post_thai_story"
down_revision: Union[str, Sequence[str], None] = "029_image_post_generate"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

IMAGE_POST_SKILL_ID = "33333333-3333-4333-8333-333333333307"

RUN_HINT = (
    "บอกหัวข้อ (ข่าว AI / เทรนด์โลก) + แพลตฟอร์ม — "
    "ได้เรื่องเล่า 1 ตอน ภาษาไทยธรรมชาติ + รูป Grok Imagine "
    "(ใส่คำว่า 'แคปชั่น' ถ้าต้องการแบบโฆษณา)"
)


def upgrade() -> None:
    op.execute(
        sa.text(
            """
            UPDATE expert_skills
            SET crew_config = jsonb_set(
                crew_config,
                '{run_hint}',
                CAST(:run_hint AS jsonb),
                true
            )
            WHERE id = CAST(:skill_id AS uuid)
            """
        ).bindparams(run_hint=json.dumps(RUN_HINT), skill_id=IMAGE_POST_SKILL_ID)
    )


def downgrade() -> None:
    old_hint = (
        "บอกหัวข้อ + แพลตฟอร์ม — ได้แคปชัน + รูปจริงจาก Grok Imagine (1:1 หรือ 4:5)"
    )
    op.execute(
        sa.text(
            """
            UPDATE expert_skills
            SET crew_config = jsonb_set(
                crew_config,
                '{run_hint}',
                CAST(:run_hint AS jsonb),
                true
            )
            WHERE id = CAST(:skill_id AS uuid)
            """
        ).bindparams(run_hint=json.dumps(old_hint), skill_id=IMAGE_POST_SKILL_ID)
    )