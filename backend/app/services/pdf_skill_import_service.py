"""Import creator PDFs into agent-flow drafts — free Companion path (no file stored)."""

from __future__ import annotations

from io import BytesIO
from typing import Any

from fastapi import UploadFile
from langchain_core.messages import HumanMessage, SystemMessage
from pypdf import PdfReader

from app.core.llm import get_llm_factory
from app.expert_skills.model_tiers import get_tier, list_garden_model_tiers
from app.graphs.utils import invoke_llm_with_fallback
from app.services.content_safety import sanitize_platform_text
from app.services.creator_garden_service import (
    COMPOSE_MODEL,
    _build_suggested_draft,
    _extract_json_object,
    _normalize_category,
    _rule_compose_from_story,
    _workflow_ideas,
)

MAX_PDF_BYTES = 10 * 1024 * 1024
MAX_PDF_CHARS = 24_000
ALLOWED_PDF_TYPES = frozenset({"application/pdf", "application/octet-stream"})


def _is_pdf_upload(upload: UploadFile, data: bytes) -> bool:
    content_type = (upload.content_type or "").split(";")[0].strip().lower()
    filename = (upload.filename or "").lower()
    if filename.endswith(".pdf"):
        return True
    if content_type in ALLOWED_PDF_TYPES and data[:4] == b"%PDF":
        return True
    return content_type == "application/pdf"


def extract_pdf_text(data: bytes, *, max_chars: int = MAX_PDF_CHARS) -> tuple[str, int]:
    reader = PdfReader(BytesIO(data))
    parts: list[str] = []
    for page in reader.pages:
        parts.append((page.extract_text() or "").strip())
    full = "\n\n".join(p for p in parts if p).strip()
    page_count = len(reader.pages)
    if len(full) > max_chars:
        full = full[: max_chars - 20] + "\n\n[…truncated…]"
    return full, page_count


def _normalize_steps(raw_steps: Any) -> list[dict[str, str]] | None:
    if not isinstance(raw_steps, list) or not raw_steps:
        return None
    steps: list[dict[str, str]] = []
    for item in raw_steps[:8]:
        if not isinstance(item, dict):
            continue
        step_id = str(item.get("id") or "").strip()[:40]
        step_type = str(item.get("type") or "llm").strip().lower()
        title = str(item.get("title") or "").strip()[:80]
        if not step_id or not title:
            continue
        step: dict[str, str] = {"id": step_id, "type": step_type, "title": title}
        if step_type == "llm":
            model = str(item.get("model") or "gemini-2.5-flash").strip()
            step["model"] = model[:60]
        elif step_type == "mcp":
            tool = str(item.get("tool") or "").strip()
            if tool:
                step["tool"] = tool[:120]
        steps.append(step)
    return steps or None


async def _llm_compose_from_pdf(
    *,
    pdf_text: str,
    filename: str,
    locale: str,
) -> dict[str, Any] | None:
    if len(pdf_text.strip()) < 40:
        return None
    lang_hint = "Respond in Thai for message_th and source_summary_th; English for message_en and source_summary_en."
    if locale != "th":
        lang_hint = "Respond in English for message_en and source_summary_en; Thai for message_th and source_summary_th."
    system = (
        "You are OBOLLA Companion — turn uploaded PDF methodology into a sellable agent flow draft. "
        "Extract the real workflow (steps, buyer input, deliverables, tools mentioned). "
        "Return ONLY valid JSON with keys: "
        "identity, audience, problem, workflow_name, workflow_description, category, "
        "input_mode, pipeline_label, run_title, skill_md, steps, "
        "message_th, message_en, source_summary_th, source_summary_en. "
        "category: seo|coding|content|support|research|quality. "
        "input_mode: task or url (url only for website-scan workflows). "
        "skill_md: rich markdown playbook (Purpose, Pipeline, Buyer input, Deliverables, Tools, QA). "
        "steps: 3-6 objects {id, type, model?, title} — type llm or mcp; use gemini-2.5-flash and grok-3-mini. "
        "Be warm and respectful — retirees and new creators upload life/work notes. "
        f"{lang_hint}"
    )
    human = (
        f"PDF filename: {filename}\n\n"
        f"Extracted text:\n\n{pdf_text[:MAX_PDF_CHARS]}"
    )
    factory = get_llm_factory()
    try:
        response, _, _ = await invoke_llm_with_fallback(
            factory,
            primary_model=COMPOSE_MODEL,
            messages=[SystemMessage(content=system), HumanMessage(content=human)],
        )
        parsed = _extract_json_object(str(response.content or ""))
        if not parsed:
            return None
        workflow_name = str(parsed.get("workflow_name") or parsed.get("name") or "").strip()
        if not workflow_name:
            return None
        category = _normalize_category(str(parsed.get("category", "")))
        steps = _normalize_steps(parsed.get("steps"))
        input_mode = str(parsed.get("input_mode") or "").strip().lower()
        if input_mode not in ("task", "url"):
            input_mode = "url" if category == "seo" else "task"
        return {
            "identity": str(parsed.get("identity") or "").strip()[:500],
            "audience": str(parsed.get("audience") or "").strip()[:300],
            "problem": str(parsed.get("problem") or "").strip()[:500],
            "workflow_name": workflow_name[:120],
            "workflow_description": str(parsed.get("workflow_description") or parsed.get("description") or "").strip()[:800],
            "category": category,
            "input_mode": input_mode,
            "skill_md": str(parsed.get("skill_md") or "").strip()[:12_000] or None,
            "pipeline_label": str(parsed.get("pipeline_label") or "").strip()[:120] or None,
            "run_title": str(parsed.get("run_title") or "").strip()[:120] or None,
            "steps": steps,
            "message_th": str(parsed.get("message_th") or "").strip()[:600],
            "message_en": str(parsed.get("message_en") or "").strip()[:600],
            "source_summary_th": str(parsed.get("source_summary_th") or "").strip()[:1200],
            "source_summary_en": str(parsed.get("source_summary_en") or "").strip()[:1200],
            "used_llm": True,
        }
    except Exception:
        return None


async def import_skill_from_pdf(
    *,
    upload: UploadFile,
    locale: str = "th",
    model_tier_id: str = "standard",
) -> dict[str, Any]:
    data = await upload.read()
    filename = upload.filename or "document.pdf"

    if not data:
        return _error_response(
            locale,
            th="ไฟล์ว่างครับ — ลองเลือก PDF อีกครั้ง",
            en="The file is empty — please choose another PDF.",
        )
    if len(data) > MAX_PDF_BYTES:
        return _error_response(
            locale,
            th=f"ไฟล์ใหญ่เกิน {MAX_PDF_BYTES // (1024 * 1024)}MB — ลองย่อหรือแบ่งไฟล์",
            en=f"File exceeds {MAX_PDF_BYTES // (1024 * 1024)}MB — try a smaller export.",
        )
    if not _is_pdf_upload(upload, data):
        return _error_response(
            locale,
            th="รองรับเฉพาะไฟล์ PDF ครับ",
            en="Only PDF files are supported.",
        )

    try:
        pdf_text, page_count = extract_pdf_text(data)
    except Exception:
        return _error_response(
            locale,
            th="อ่าน PDF ไม่ได้ — ลอง export ใหม่หรือส่งไฟล์ที่เลือกข้อความได้",
            en="Could not read this PDF — try re-exporting with selectable text.",
        )

    if len(pdf_text.strip()) < 40:
        return _error_response(
            locale,
            th="PDF นี้แทบไม่มีข้อความ — อาจเป็นภาพสแกน ลอง OCR หรือพิมพ์สรุปในช่องด้านล่างแทน",
            en="This PDF has little extractable text — try OCR or paste a summary below.",
            pdf_meta={"filename": filename, "page_count": page_count, "char_count": len(pdf_text)},
        )

    composed = await _llm_compose_from_pdf(pdf_text=pdf_text, filename=filename, locale=locale)
    if not composed:
        composed = _rule_compose_from_story(pdf_text[:6000])
        composed["source_summary_th"] = pdf_text[:800]
        composed["source_summary_en"] = pdf_text[:800]
        composed["message_th"] = (
            "อ่าน PDF แล้ว — จัดร่างเบื้องต้นให้แล้วครับ ตรวจ pipeline ด้านล่างก่อนกดสร้าง"
        )
        composed["message_en"] = (
            "We read your PDF and drafted a starter flow — review the pipeline below before creating."
        )

    ideas = _workflow_ideas(
        composed.get("identity", ""),
        composed.get("audience", ""),
        composed.get("problem", ""),
    )
    tier_id = model_tier_id if get_tier(model_tier_id) else "standard"
    suggested = _build_suggested_draft(
        identity=composed.get("identity", ""),
        audience=composed.get("audience", ""),
        problem=composed.get("problem", ""),
        workflow_name=composed.get("workflow_name", ""),
        workflow_description=composed.get("workflow_description", ""),
        category=composed.get("category", "quality"),
        skill_md=composed.get("skill_md"),
        pipeline_label=composed.get("pipeline_label"),
        model_tier_id=tier_id,
        steps=composed.get("steps"),
        input_mode=composed.get("input_mode"),
        run_title=composed.get("run_title"),
    )

    message_th = sanitize_platform_text(
        composed.get("message_th")
        or f"อ่าน «{filename}» แล้ว — «{suggested['name']}» พร้อมสร้าง agent flow",
        fallback=f"อ่าน «{filename}» แล้ว — «{suggested['name']}» พร้อมสร้าง agent flow",
    )
    message_en = sanitize_platform_text(
        composed.get("message_en")
        or f"Read «{filename}» — «{suggested['name']}» is ready to create.",
        fallback=f"Read «{filename}» — «{suggested['name']}» is ready to create.",
    )

    summary_th = str(composed.get("source_summary_th") or pdf_text[:600]).strip()
    summary_en = str(composed.get("source_summary_en") or pdf_text[:600]).strip()

    return {
        "message_th": message_th,
        "message_en": message_en,
        "workflow_ideas": ideas,
        "suggested_draft": suggested,
        "companion_th": "ผมอยู่ข้างคุณในการสร้างมันครับ",
        "composed": True,
        "used_llm": bool(composed.get("used_llm")),
        "model_tiers": list_garden_model_tiers(),
        "pdf_import": {
            "filename": filename,
            "page_count": page_count,
            "char_count": len(pdf_text),
            "summary_th": summary_th[:1200],
            "summary_en": summary_en[:1200],
        },
    }


def _error_response(locale: str, *, th: str, en: str, pdf_meta: dict | None = None) -> dict[str, Any]:
    return {
        "message_th": th,
        "message_en": en,
        "workflow_ideas": [],
        "suggested_draft": {},
        "companion_th": "ผมอยู่ข้างคุณในการสร้างมันครับ",
        "composed": False,
        "used_llm": False,
        "model_tiers": list_garden_model_tiers(),
        "pdf_import": pdf_meta,
        "error": en if locale != "th" else th,
    }