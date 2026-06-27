"""OBOLLA Thai marketplace copy — coffee-corner tone, capability-honest."""

from __future__ import annotations

import json
import logging
import re
from pathlib import Path
from typing import TYPE_CHECKING

from langchain_core.messages import HumanMessage, SystemMessage

from app.core.config import settings
from app.core.llm import LLMFactory
from app.graphs.expert_skill_prompts import _THAI_HUMAN_COPY_RULES
from app.models.expert_skill import ExpertSkill

if TYPE_CHECKING:
    from app.repositories.expert_skill_repository import ExpertSkillRepository

logger = logging.getLogger(__name__)

_THAI_RE = re.compile(r"[\u0E00-\u0E7F]")
_REF_DIR = Path(__file__).resolve().parent / "references"
_IMAGE_POST_STYLE = (
    Path(__file__).resolve().parent
    / "packs"
    / "image-post-creator"
    / "references"
    / "thai-copy-style.md"
)

OBOLLA_THAI_VOICE = """
คุณเขียน copy ภาษาไทยให้ marketplace OBOLLA — โทนเหมือนเพื่อนนั่งคุยที่มุมกาแฟ

กฎหัวข้อ (name) — บังคับ:
- รูปแบบ: "{English product name} · {คำอธิบายไทยสั้นๆ}"
- เก็บชื่อสินค้าและศัพท์เทคนิคเป็นภาษาอังกฤษ ห้ามแปลทั้งก้อน เช่น Agent Flow, QA, SEO, pipeline
- ส่วนหลัง · เป็นคำอธิบายไทยสั้น ไม่ใช่คำแปลตรงทุกคำ

กฎ description:
- อธิบายง่าย เป็นกันเอง บอกชัดว่าหนึ่งรันได้อะไร ห้ามอวดเกินความสามารถจริง
- เก็บศัพท์เทคนิค ENG: AIBotAuth, Ollama, Grok, GPT, proof, Fix Pack, LoRA, GPU, hook, CTA
- ประโยคสั้น–กลาง อ่านบนมือถือได้สบาย ไม่ใช้คำการตลาดหวือหวา

Return ONLY JSON: {"name": "...", "description": "..."}
"""

# Curated by slug — source of truth; refreshed on deploy migration for platform skills.
CURATED_TH_BY_SLUG: dict[str, dict[str, str]] = {
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
            "โหลด sensor readings จาก Smart Farm DB อัตโนมัติ — ไม่ต้อง paste เอง "
            "เช็ก temp, humidity, UV, EC, pH, soil moisture, Brix ตาม schema เมล่อนญี่ปุ่น "
            "ได้ verdict READY / NEEDS_CORRECTION พร้อม P0 fixes"
        ),
    },
    "japanese-melon-dataset-pack": {
        "name": "Japanese Melon Dataset Pack · ชุดข้อมูลเมล่อนญี่ปุ่น",
        "description": (
            "$4.99/รัน — export dataset จาก smart farm จริง จัดตาม greenhouse schema "
            "พร้อม download JSON/CSV นำไปป้อนระบบ IoT / automation ได้ทันที "
            "รองรับ HTTP ingest + MQTT TLS"
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


def _has_thai(text: str) -> bool:
    return bool(_THAI_RE.search(text or ""))


def _load_style_refs() -> str:
    parts: list[str] = []
    for path in (_REF_DIR / "marketplace-thai-copy-style.md", _IMAGE_POST_STYLE):
        try:
            if path.is_file():
                parts.append(path.read_text(encoding="utf-8"))
        except OSError as exc:
            logger.warning("thai_copy: could not read %s: %s", path, exc)
    return "\n\n---\n\n".join(parts)


def _thai_copy_model() -> str:
    if settings.anthropic_api_key:
        return "claude-haiku-4-5-20251001"
    if settings.google_api_key or settings.gemini_api_key:
        return (
            settings.default_model
            if settings.default_model.startswith("gemini")
            else "gemini-2.5-flash"
        )
    return settings.default_model


def curated_thai_for_skill(skill: ExpertSkill) -> dict[str, str] | None:
    hit = CURATED_TH_BY_SLUG.get(skill.slug)
    if hit:
        return dict(hit)
    return None


async def generate_obolla_thai_copy(skill: ExpertSkill) -> dict[str, str] | None:
    curated = curated_thai_for_skill(skill)
    if curated:
        return curated

    has_llm = bool(
        settings.anthropic_api_key or settings.google_api_key or settings.gemini_api_key
    )
    if not has_llm:
        if _has_thai(skill.name) and _has_thai(skill.description):
            return {"name": skill.name.strip(), "description": skill.description.strip()}
        return None

    style_refs = _load_style_refs()
    system_text = (
        f"{OBOLLA_THAI_VOICE}\n\n"
        f"{_THAI_HUMAN_COPY_RULES}\n\n"
        f"Style references:\n{style_refs}"
    )
    llm = LLMFactory().get(_thai_copy_model())
    price = float(skill.price_usd_per_run or 0)
    category = skill.category or "general"
    pack = skill.pack_slug or "custom"
    system = SystemMessage(content=system_text)
    category_hint = {
        "support": "หมวดซัพพอร์ต/ที่ปรึกษา — เน้นว่าหนึ่งรันช่วยอะไรได้จริง ไม่สัญญารายได้หรือผลลัพธ์วัดไม่ได้",
        "content": "หมวดคอนเทนต์ — บอกขั้นตอนที่ได้และสิ่งที่ผู้ซื้อต้องทำเอง (ถ้ามี)",
        "seo": "หมวด SEO/visibility — บอก deliverable จริง เช่น proof, scorecard, Fix Pack",
        "coding": "หมวดโค้ด — บอก pipeline Plan→Implement→Review→QA และว่าต้องมี GPU/Ollama หรือไม่",
        "quality": "หมวด QA — บอกว่าเช็กอะไรก่อนส่งมอบ",
        "research": "หมวดวิจัย — บอกว่าได้รายงาน/บันทึกอะไร",
    }.get(category, "บอก deliverable ตรงๆ แบบเพื่อนแนะนำ")

    human = HumanMessage(
        content=(
            f"Category: {category}\nHint: {category_hint}\nPack: {pack}\nPrice USD per run: {price:.2f}\n\n"
            f"English name (keep in title before ·):\n{skill.name}\n\n"
            f"English description:\n{skill.description[:2000]}\n\n"
            "เขียน name แบบ ENG · ไทย และ description ภาษาไทยที่ตรงความสามารถจริง "
            "ห้ามแปลศัพท์เทคนิคเป็นภาษาไทย ห้ามเพิ่มฟีเจอร์ที่ไม่มีในต้นฉบับ"
        )
    )
    try:
        resp = await llm.ainvoke([system, human])
        raw = str(getattr(resp, "content", "") or "").strip()
        if raw.startswith("```"):
            raw = raw.split("```", 2)[1]
            if raw.startswith("json"):
                raw = raw[4:]
        data = json.loads(raw)
        th_name = str(data.get("name") or "").strip()
        th_desc = str(data.get("description") or "").strip()
        if th_name and th_desc:
            return {"name": th_name, "description": th_desc}
    except Exception as exc:
        logger.warning("generate_obolla_thai_copy failed slug=%s: %s", skill.slug, exc)

    if _has_thai(skill.name) and _has_thai(skill.description):
        return {"name": skill.name.strip(), "description": skill.description.strip()}
    return None


async def ensure_obolla_thai_i18n(repository: ExpertSkillRepository, skill: ExpertSkill) -> ExpertSkill:  # type: ignore[name-defined]
    patch = await generate_obolla_thai_copy(skill)
    if not patch:
        return skill
    updated = await repository.save_i18n_locale(skill.id, "th", patch)
    return updated or skill