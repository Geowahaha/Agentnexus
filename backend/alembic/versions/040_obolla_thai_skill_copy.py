"""Seed OBOLLA Thai copy (coffee-corner tone) for all marketplace skills

Revision ID: 040_obolla_thai_copy
Revises: 039_expert_skill_i18n
Create Date: 2026-06-22

"""
import json
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "040_obolla_thai_copy"
down_revision: Union[str, Sequence[str], None] = "039_expert_skill_i18n"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Keep in sync with app.expert_skills.thai_copy.CURATED_TH_BY_SLUG
COPY_BY_SLUG: dict[str, dict[str, str]] = {
    "fable5-coding-agent-premium": {
        "name": "โค้ดดิ้งเอเจนต์ Fable-5 แบบ Pro",
        "description": (
            "นั่งจิบกาแฟไปพลางสั่งงานได้เลย — หนึ่งรันช่วยวางแผน → เขียนโค้ด → รีวิว → เช็ก QA ให้ครบ "
            "($5 ต่อรัน) รันบน cloud ด้วย GPT-4.1 + Grok ไม่ต้องมี GPU ที่บ้าน เหมาะกับงาน dev จริงที่อยากได้ผลเร็ว"
        ),
    },
    "fable5-coding-agent": {
        "name": "โค้ดดิ้งเอเจนต์ Fable-5 ฟรี (รันที่เครื่องคุณ)",
        "description": (
            "ฟรีทั้งค่ารันและค่า LLM — ใช้ LoRA hotdogs ผ่าน Ollama บนเครื่องคุณ "
            "วางแผน → ลงมือ → รีวิว → QA ไม่มี cloud สำรอง ต้องตั้ง Ollama + LoRA ก่อนรัน"
        ),
    },
    "ai-visibility-2026": {
        "name": "ตรวจเว็บให้ AI เห็น — Audit 2026",
        "description": (
            "$2.50 ต่อรัน — สแกน AIBotAuth จริง แล้ว Claude สรุป Gemini จัดแพ็กแก้ Grok เช็ก QA "
            "ทุกรันได้ลิงก์ proof แชร์ลูกค้าได้ มีเคสจริง successcasting & pinpoint (คะแนน 88/100)"
        ),
    },
    "seo-expert-analysis": {
        "name": "วิเคราะห์ SEO ระดับมืออาชีพ",
        "description": (
            "หนึ่งรันได้รายงานพร้อมส่งลูกค้า — ดูคู่แข่ง หาช่องว่างคอนเทนต์ ตรวจเทคนิค SEO Core Web Vitals "
            "พร้อมแผนลงมือจัดลำดับความสำคัญและคาดการณ์ผลกระทบคร่าวๆ"
        ),
    },
    "audit-bottle-neck-www": {
        "name": "แก้เว็บให้ AI ค้นหาเจอ (FIX Web)",
        "description": (
            "สำหรับเว็บโรงงาน/ธุรกิจจริง — ช่วยจัด robots, metadata, เทคนิค SEO และนโยบายบอท "
            "ให้ AI crawler เข้าใจได้ โดยไม่เปิดข้อมูลส่วนตัวหรือปล่อยให้โมเดลเอาไปเทรนตามใจ"
        ),
    },
    "content-pipeline-for-creators": {
        "name": "โฟลว์คอนเทนต์สำหรับครีเอเตอร์",
        "description": (
            "งานซ้ำๆ แบบเดิม ส่งให้เอเจนต์ช่วย — ค้นคว้า → ร่าง → แก้ → เช็กลิสต์ก่อนเผยแพร่ "
            "เหมาะกับโพสต์ประจำที่อยากได้คุณภาพคงที่โดยไม่นั่งไล่ทุกขั้นเอง"
        ),
    },
    "ai-lineart-youtube-kemlife": {
        "name": "ช่อง YouTube การ์ตูนลายเส้น AI",
        "description": (
            "เทมเพลตช่อง faceless — หาเรื่อง → เขียนบทพร้อม timestamp → prompt ภาพสไตล์ MS Paint 16:9 → QA ก่อนปล่อย "
            "คุณรัน Higgsfield/CapCut เอง เอเจนต์จัดบทกับ prompt ให้"
        ),
    },
    "ai-lineart-facebook-reel-kemlife": {
        "name": "Facebook Reels การ์ตูนลายเส้น AI",
        "description": (
            "เทมเพลต Reels แนวตั้ง — hook → บท 30–90 วินาที → prompt ภาพ 9:16 → แคปชันแฮชแท็ก + QA "
            "คุณรัน Higgsfield/CapCut เอง เอเจนต์จัดบทกับ prompt ให้"
        ),
    },
    "image-post-creator": {
        "name": "สร้างโพสต์รูปโซเชียล",
        "description": (
            "บอกมุมที่อยากพูด — ได้แคปชัน CTA alt text แฮชแท็ก prompt ภาพ แล้วสร้างรูปจริงด้วย Grok Imagine "
            "เช็ก QA ก่อนโพสต์ รองรับ Instagram Facebook LinkedIn"
        ),
    },
    "short-post-creator": {
        "name": "สร้างโพสต์ข้อความสั้น",
        "description": (
            "บอกมุมกับแพลตฟอร์ม — ได้ 3 hook ต่างกัน ข้อความหลักสำรอง (+ thread ถ้าขอ) เช็ก QA ก่อนโพสต์ "
            "รองรับ X Threads LinkedIn Facebook"
        ),
    },
    "travel-photo-monetization-explorer": {
        "name": "หาแนวทำเงินจากรูปท่องเที่ยว",
        "description": (
            "มีรูปเที่ยวค้างอยู่ในมือถือ? หนึ่งรันช่วยไล่ไอเดียว่าจะนำไปขาย ลงสต็อก หรือทำคอนเทนต์ยังไง "
            "ได้แนวทางหลายแบบที่ทำได้จริง ไม่ฟันธงรายได้"
        ),
    },
    "quality-check-flow-smart-famers": {
        "name": "เช็กคุณภาพก่อนส่ง — Smart Farming",
        "description": (
            "ก่อนส่งมอบงาน smart farm — ช่วยตรวจสัญญาณอุณหภูมิ UV แสง ปุ๋ย ความชื้นอากาศ/ดิน "
            "ว่าครบและสมเหตุสมผลไหม เหมาะกับ flow เกษตรอัจฉริยะที่มีเซ็นเซอร์หลายตัว"
        ),
    },
    "fix-bot-ai-free": {
        "name": "สแกนบอท AI ฟรี + ลิงก์ proof",
        "description": (
            "ฟรี — ใส่ URL ได้ scorecard แบบ isitagentready รายการแก้ P0/P1/P2 ไฟล์ robots/llms/agents พร้อมวาง "
            "และลิงก์ proof จาก AIBotAuth แชร์ได้ มีเคสจริง successcasting & pinpoint อัปเกรด Auto Fix Pro $9.99 ได้"
        ),
    },
    "agent-ready-auto-fix": {
        "name": "แก้เว็บให้ Agent-Ready ครบชุด (Pro)",
        "description": (
            "$9.99 ต่อรัน — แผนช่องว่าง แพ็ก deploy ครบ robots llms protocol commerce คู่มือตาม stack "
            "เช็กลิสต์ verify ซ้ำ พร้อมลิงก์ proof อ้างอิง successcasting 25%→100% และ pinpoint 88/100"
        ),
    },
}


def upgrade() -> None:
    conn = op.get_bind()
    for slug, th in COPY_BY_SLUG.items():
        payload = json.dumps({"th": th}, ensure_ascii=False)
        conn.execute(
            sa.text(
                """
                UPDATE expert_skills
                SET i18n = CAST(:payload AS jsonb)
                WHERE slug = :slug
                """
            ),
            {"slug": slug, "payload": payload},
        )


def downgrade() -> None:
    conn = op.get_bind()
    for slug in COPY_BY_SLUG:
        conn.execute(
            sa.text(
                """
                UPDATE expert_skills
                SET i18n = i18n - 'th'
                WHERE slug = :slug
                """
            ),
            {"slug": slug},
        )