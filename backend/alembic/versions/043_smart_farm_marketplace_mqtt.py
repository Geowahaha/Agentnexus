"""Smart farm QA pack, dataset marketplace skill, MQTT-ready config

Revision ID: 043_smart_farm_marketplace
Revises: 042_smart_farm_telemetry
Create Date: 2026-06-22

"""
import json
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "043_smart_farm_marketplace"
down_revision: Union[str, Sequence[str], None] = "042_smart_farm_telemetry"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

SYSTEM_USER_ID = "00000000-0000-4000-8000-000000000001"
QC_SKILL_ID = "4413b1c6-9b20-4be3-89d8-6059942d92b0"
DATASET_SKILL_ID = "33333333-3333-4333-8333-333333333311"

QC_STEPS = [
    {"id": "intake", "type": "llm", "model": "gemini-2.5-flash", "title": "Intake"},
    {"id": "work", "type": "llm", "model": "gemini-2.5-flash", "title": "Work"},
    {"id": "review", "type": "llm", "model": "grok-3-mini", "title": "Review"},
    {"id": "deliver", "type": "llm", "model": "grok-3-mini", "title": "Deliver"},
]

TH_QC = {
    "name": "Quality Check Flow · เช็กคุณภาพ Smart Farm",
    "description": (
        "โหลด sensor readings จาก Smart Farm DB อัตโนมัติ — ไม่ต้อง paste เอง "
        "เช็ก temp, humidity, UV, EC, pH, soil moisture, Brix ตาม schema เมล่อนญี่ปุ่น "
        "ได้ verdict READY / NEEDS_CORRECTION พร้อม P0 fixes"
    ),
}

TH_DATASET = {
    "name": "Japanese Melon Dataset Pack · ชุดข้อมูลเมล่อนญี่ปุ่น",
    "description": (
        "$4.99/รัน — export dataset จาก smart farm จริง จัดตาม greenhouse schema "
        "พร้อม download JSON/CSV นำไปป้อนระบบ IoT / automation ได้ทันที "
        "รองรับ HTTP ingest + MQTT TLS"
    ),
}


def upgrade() -> None:
    conn = op.get_bind()
    qc_crew = {
        "steps": QC_STEPS,
        "category": "quality",
        "input_mode": "task",
        "pipeline_label": "Telemetry → Checklist → Review → Verdict",
        "run_title": "Run Quality Flow",
        "skill_md": (
            "# Quality Check Flow — Smart Farm\n\n"
            "OBOLLA loads live sensor readings from your Smart Farm DB automatically.\n"
            "QA against Japanese melon greenhouse schema. Verdict: READY or NEEDS_CORRECTION."
        ),
    }
    conn.execute(
        sa.text(
            """
            UPDATE expert_skills
            SET pack_slug = 'quality-check-smart-farm',
                crew_config = CAST(:crew AS jsonb),
                i18n = COALESCE(i18n, '{}'::jsonb) || CAST(:i18n AS jsonb)
            WHERE slug = 'quality-check-flow-smart-famers'
               OR id = CAST(:id AS uuid)
            """
        ),
        {
            "id": QC_SKILL_ID,
            "crew": json.dumps(qc_crew),
            "i18n": json.dumps({"th": TH_QC}),
        },
    )

    dataset_crew = {
        "steps": QC_STEPS,
        "category": "research",
        "input_mode": "task",
        "pipeline_label": "Telemetry → Schema map → Export → Download",
        "run_title": "Run Dataset Export",
        "skill_md": (
            "# Japanese Melon Greenhouse Dataset Pack\n\n"
            "Export production telemetry as a marketplace dataset pack with download URL."
        ),
    }
    conn.execute(
        sa.text(
            """
            INSERT INTO expert_skills (
                id, slug, name, description, category, pack_slug, crew_config,
                capabilities, price_usd_per_run, owner_id, is_active, i18n, created_at, updated_at
            ) VALUES (
                CAST(:id AS uuid), :slug, :name, :description, :category, :pack_slug,
                CAST(:crew AS jsonb), CAST(:capabilities AS jsonb), :price, CAST(:owner AS uuid),
                true, CAST(:i18n AS jsonb), NOW(), NOW()
            )
            ON CONFLICT (slug) DO UPDATE SET
                name = EXCLUDED.name,
                description = EXCLUDED.description,
                pack_slug = EXCLUDED.pack_slug,
                crew_config = EXCLUDED.crew_config,
                price_usd_per_run = EXCLUDED.price_usd_per_run,
                i18n = EXCLUDED.i18n,
                updated_at = NOW()
            """
        ),
        {
            "id": DATASET_SKILL_ID,
            "slug": "japanese-melon-dataset-pack",
            "name": "Japanese Melon Greenhouse Dataset Pack",
            "description": (
                "$4.99/run — export real smart-farm telemetry aligned to Japanese melon "
                "greenhouse schema. JSON/CSV download ready for IoT automation. "
                "HTTP + MQTT TLS ingest supported."
            ),
            "category": "research",
            "pack_slug": "japanese-melon-dataset",
            "crew": json.dumps(dataset_crew),
            "capabilities": json.dumps(["smart-farm", "dataset", "iot", "qa"]),
            "price": "4.9900",
            "owner": SYSTEM_USER_ID,
            "i18n": json.dumps({"th": TH_DATASET}),
        },
    )


def downgrade() -> None:
    conn = op.get_bind()
    conn.execute(
        sa.text("DELETE FROM expert_skills WHERE id = CAST(:id AS uuid)"),
        {"id": DATASET_SKILL_ID},
    )
    conn.execute(
        sa.text(
            """
            UPDATE expert_skills
            SET pack_slug = 'custom'
            WHERE id = CAST(:id AS uuid)
            """
        ),
        {"id": QC_SKILL_ID},
    )