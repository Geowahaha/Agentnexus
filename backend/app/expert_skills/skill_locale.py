"""Localized expert-skill copy (Thai first). Auto-translate once, persist in i18n JSONB."""

from __future__ import annotations

import json
import logging
import re
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage

from app.core.config import settings
from app.core.llm import LLMFactory
from app.models.expert_skill import ExpertSkill

logger = logging.getLogger(__name__)

_THAI_RE = re.compile(r"[\u0E00-\u0E7F]")


def _has_thai(text: str) -> bool:
    return bool(_THAI_RE.search(text or ""))


def pick_locale_copy(skill: ExpertSkill, lang: str | None) -> tuple[str, str, str]:
    """Return (name, description, display_locale). display_locale is th or en."""
    locale = (lang or "en").strip().lower()
    if locale != "th":
        return skill.name, skill.description, "en"

    th = (skill.i18n or {}).get("th") if isinstance(skill.i18n, dict) else None
    if isinstance(th, dict):
        name = str(th.get("name") or "").strip()
        desc = str(th.get("description") or "").strip()
        if name and desc:
            return name, desc, "th"

    if _has_thai(skill.name) and _has_thai(skill.description):
        return skill.name, skill.description, "th"

    return skill.name, skill.description, "en"


async def translate_skill_copy_to_th(name: str, description: str) -> dict[str, str] | None:
    if not settings.google_api_key and not settings.gemini_api_key:
        return None
    model = settings.default_model if settings.default_model.startswith("gemini") else "gemini-2.5-flash"
    llm = LLMFactory().get(model)
    system = SystemMessage(
        content=(
            "You translate marketplace product listings into natural Thai for general Thai readers. "
            "Keep proper nouns, URLs, and technical terms (GPT, Ollama, MCP) as appropriate. "
            "Return ONLY valid JSON: {\"name\": \"...\", \"description\": \"...\"}"
        )
    )
    human = HumanMessage(
        content=(
            f"Product name:\n{name}\n\n"
            f"Product description:\n{description}\n\n"
            "Translate both fields to Thai."
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
        if not th_name or not th_desc:
            return None
        return {"name": th_name, "description": th_desc}
    except Exception as exc:
        logger.warning("skill_locale translate failed: %s", exc)
        return None


def merge_i18n_locale(existing: dict[str, Any] | None, locale: str, patch: dict[str, str]) -> dict[str, Any]:
    merged = dict(existing or {})
    merged[locale] = {**(merged.get(locale) or {}), **patch}
    return merged