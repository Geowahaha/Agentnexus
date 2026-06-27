"""Line-art skills — cleaner public names (credits stay in pack attribution)

Revision ID: 031_lineart_public_names
Revises: 030_image_post_thai_story
Create Date: 2026-06-20

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "031_lineart_public_names"
down_revision: Union[str, Sequence[str], None] = "030_image_post_thai_story"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

YOUTUBE_SKILL_ID = "33333333-3333-4333-8333-333333333305"
REEL_SKILL_ID = "33333333-3333-4333-8333-333333333306"


def upgrade() -> None:
    op.execute(
        sa.text(
            """
            UPDATE expert_skills
            SET name = :name, description = :description
            WHERE id = CAST(:skill_id AS uuid)
            """
        ).bindparams(
            skill_id=YOUTUBE_SKILL_ID,
            name="ช่อง YouTube การ์ตูนลายเส้น AI",
            description=(
                "เทมเพลตช่อง YouTube faceless — หาเรื่อง → บท timestamp → prompt ภาพ MS Paint 16:9 "
                "→ QA ปล่อยคลิป. Buyer รัน Higgsfield/CapCut เอง — agent จัดบทและ prompt ให้."
            ),
        )
    )
    op.execute(
        sa.text(
            """
            UPDATE expert_skills
            SET name = :name, description = :description
            WHERE id = CAST(:skill_id AS uuid)
            """
        ).bindparams(
            skill_id=REEL_SKILL_ID,
            name="Facebook Reels การ์ตูนลายเส้น AI",
            description=(
                "เทมเพลต Facebook Reels faceless — hook → บท 30–90s → prompt ภาพ MS Paint 9:16 "
                "→ caption/hashtag + QA. Buyer รัน Higgsfield/CapCut เอง — agent จัดบทและ prompt ให้."
            ),
        )
    )


def downgrade() -> None:
    op.execute(
        sa.text(
            """
            UPDATE expert_skills
            SET name = :name, description = :description
            WHERE id = CAST(:skill_id AS uuid)
            """
        ).bindparams(
            skill_id=YOUTUBE_SKILL_ID,
            name="ช่อง YouTube การ์ตูนลายเส้น AI (KEMLIFE)",
            description=(
                "เทมเพลตช่อง YouTube การ์ตูนลายเส้นแบบ faceless — หาเรื่อง → บท timestamp "
                "→ prompt ภาพ MS Paint 16:9 → QA ปล่อยคลิป. "
                "อิง workflow KEMLIFE (สรุปจาก Danny Why / สไตล์ Zenn). "
                "Buyer รัน Higgsfield/CapCut เอง — agent จัดบทและ prompt ให้."
            ),
        )
    )
    op.execute(
        sa.text(
            """
            UPDATE expert_skills
            SET name = :name, description = :description
            WHERE id = CAST(:skill_id AS uuid)
            """
        ).bindparams(
            skill_id=REEL_SKILL_ID,
            name="Facebook Reels การ์ตูนลายเส้น AI (KEMLIFE)",
            description=(
                "เทมเพลต Facebook Reels การ์ตูนลายเส้นแบบ faceless — hook วินาทีแรก → บท 30–90s "
                "→ prompt ภาพ MS Paint 9:16 → caption/hashtag + QA. "
                "อิง workflow KEMLIFE (Reels แนวตั้ง). Buyer รัน Higgsfield/CapCut เอง."
            ),
        )
    )