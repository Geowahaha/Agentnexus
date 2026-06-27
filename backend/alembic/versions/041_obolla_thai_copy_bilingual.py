"""Refresh OBOLLA Thai copy — bilingual ENG · Thai titles, keep technical terms

Revision ID: 041_obolla_thai_bilingual
Revises: 040_obolla_thai_copy
Create Date: 2026-06-22

"""
import json
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "041_obolla_thai_bilingual"
down_revision: Union[str, Sequence[str], None] = "040_obolla_thai_copy"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Keep in sync with app.expert_skills.thai_copy.CURATED_TH_BY_SLUG
COPY_BY_SLUG: dict[str, dict[str, str]] = {
    "fable5-coding-agent-premium": {
        "name": "Fable-5 Coding Agent Pro · โค้ดดิ้งเอเจนต์แบบ Pro",
        "description": (
            "นั่งจิบกาแฟไปพลางสั่งงานได้ — หนึ่งรันได้ Plan → Implement → Review → QA ครบ "
            "($5/รัน) รันบน cloud ด้วย GPT-4.1 + Grok ไม่ต้องมี GPU ที่บ้าน เหมาะงาน dev ที่อยากได้ผลเร็ว"
        ),
    },
    "fable5-coding-agent": {
        "name": "Fable-5 Coding Agent (Free) · รันฟรีบนเครื่องคุณ",
        "description": (
            "ฟรีทั้งค่ารันและค่า LLM — ใช้ LoRA hotdogs ผ่าน Ollama บนเครื่องคุณ "
            "Plan → Implement → Review → QA ไม่มี cloud fallback ต้องตั้ง Ollama + LoRA ก่อนรัน"
        ),
    },
    "ai-visibility-2026": {
        "name": "AI Visibility Audit 2026 · ตรวจให้ AI เห็นเว็บ",
        "description": (
            "$2.50/รัน — สแกน AIBotAuth จริง Claude สรุป Gemini จัด Fix Pack Grok เช็ก QA "
            "ทุกรันได้ลิงก์ proof แชร์ลูกค้าได้ มีเคสจริง successcasting & pinpoint (88/100)"
        ),
    },
    "seo-expert-analysis": {
        "name": "SEO Expert Analysis · วิเคราะห์ SEO ระดับโปร",
        "description": (
            "หนึ่งรันได้รายงานพร้อมส่งลูกค้า — ดูคู่แข่ง หา content gap ตรวจ technical SEO + Core Web Vitals "
            "พร้อม action plan จัดลำดับความสำคัญ"
        ),
    },
    "audit-bottle-neck-www": {
        "name": "FIX Web · แก้เว็บให้ AI crawler เข้าใจ",
        "description": (
            "สำหรับเว็บโรงงาน/ธุรกิจจริง — ช่วยจัด robots.txt, metadata, technical SEO และ bot policy "
            "ให้ AI crawler เข้าใจได้ โดยไม่เปิดข้อมูลส่วนตัวหรือปล่อยให้โมเดลเอาไป train"
        ),
    },
    "content-pipeline-for-creators": {
        "name": "Content Pipeline · โฟลว์คอนเทนต์ครีเอเตอร์",
        "description": (
            "งานซ้ำๆ แบบเดิม ส่งให้ agent ช่วย — Research → Draft → Edit → Publish checklist "
            "เหมาะโพสต์ประจำที่อยากได้คุณภาพคงที่โดยไม่นั่งไล่ทุกขั้นเอง"
        ),
    },
    "ai-lineart-youtube-kemlife": {
        "name": "AI Lineart YouTube · ช่อง YouTube การ์ตูนลายเส้น",
        "description": (
            "เทมเพลตช่อง faceless — หาเรื่อง → บทพร้อม timestamp → image prompt สไตล์ MS Paint 16:9 → QA ก่อนปล่อย "
            "คุณรัน Higgsfield/CapCut เอง agent จัดบทกับ prompt ให้"
        ),
    },
    "ai-lineart-facebook-reel-kemlife": {
        "name": "AI Lineart Facebook Reels · รีลส์การ์ตูนลายเส้น",
        "description": (
            "เทมเพลต Reels แนวตั้ง — hook → บท 30–90 วินาที → image prompt 9:16 → caption + hashtag + QA "
            "คุณรัน Higgsfield/CapCut เอง agent จัดบทกับ prompt ให้"
        ),
    },
    "image-post-creator": {
        "name": "Image Post Creator · สร้างโพสต์รูปโซเชียล",
        "description": (
            "บอกมุมที่อยากพูด — ได้ caption, CTA, alt text, hashtag, image prompt แล้วสร้างรูปจริงด้วย Grok Imagine "
            "เช็ก QA ก่อนโพสต์ รองรับ Instagram, Facebook, LinkedIn"
        ),
    },
    "short-post-creator": {
        "name": "Short Post Creator · สร้างโพสต์ข้อความสั้น",
        "description": (
            "บอกมุมกับแพลตฟอร์ม — ได้ 3 hook ต่างกัน ข้อความหลักสำรอง (+ thread ถ้าขอ) เช็ก QA ก่อนโพสต์ "
            "รองรับ X, Threads, LinkedIn, Facebook"
        ),
    },
    "travel-photo-monetization-explorer": {
        "name": "Travel Photo Monetization · หาแนวทำเงินจากรูปเที่ยว",
        "description": (
            "มีรูปเที่ยวค้างในมือถือ? หนึ่งรันช่วยไล่ไอเดียว่าจะนำไปขาย ลง stock หรือทำ content ยังไง "
            "ได้แนวทางหลายแบบที่ทำได้จริง ไม่ฟันธงรายได้"
        ),
    },
    "quality-check-flow-smart-famers": {
        "name": "Quality Check Flow · เช็กคุณภาพ Smart Farm",
        "description": (
            "ก่อนส่งมอบงาน smart farm — ช่วยตรวจสัญญาณอุณหภูมิ, UV, แสง, ปุ๋ย, ความชื้นอากาศ/ดิน "
            "ว่าครบและสมเหตุสมผลไหม เหมาะ flow เกษตรอัจฉริยะที่มีเซ็นเซอร์หลายตัว"
        ),
    },
    "fix-bot-ai-free": {
        "name": "Fix Bot AI · สแกน Agent ฟรี + proof",
        "description": (
            "ฟรี — ใส่ URL ได้ scorecard แบบ isitagentready รายการแก้ P0/P1/P2 ไฟล์ robots/llms/agents พร้อมวาง "
            "และลิงก์ proof จาก AIBotAuth แชร์ได้ มีเคสจริง successcasting & pinpoint "
            "อัปเกรด Agent-Ready Auto Fix Pro $9.99 ได้"
        ),
    },
    "agent-ready-auto-fix": {
        "name": "Agent-Ready Auto Fix Pro · แก้เว็บครบชุด",
        "description": (
            "$9.99/รัน — gap plan, deploy pack ครบ robots, llms.txt, protocol, commerce คู่มือตาม stack "
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
                SET i18n = COALESCE(i18n, '{}'::jsonb) || CAST(:payload AS jsonb)
                WHERE slug = :slug
                """
            ),
            {"slug": slug, "payload": payload},
        )


def downgrade() -> None:
    conn = op.get_bind()
    for slug, th in COPY_BY_SLUG.items():
        payload = json.dumps({"th": th}, ensure_ascii=False)
        conn.execute(
            sa.text(
                """
                UPDATE expert_skills
                SET i18n = COALESCE(i18n, '{}'::jsonb) || CAST(:payload AS jsonb)
                WHERE slug = :slug
                """
            ),
            {"slug": slug, "payload": payload},
        )