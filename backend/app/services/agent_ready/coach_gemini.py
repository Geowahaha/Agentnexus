from __future__ import annotations

import json
import logging
import re
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage

from app.core.config import settings
from app.core.llm import LLMFactory, has_llm_provider_configured
from app.expert_skills.thai_copy import OBOLLA_THAI_VOICE
from app.graphs.expert_skill_prompts import _THAI_HUMAN_COPY_RULES
from app.graphs.utils import invoke_llm_with_fallback

logger = logging.getLogger(__name__)

_THAI_RE = re.compile(r"[\u0E00-\u0E7F]")
COACH_MODEL = "gemini-2.5-flash"


def _coach_model() -> str:
    model = (settings.agent_ready_coach_model or COACH_MODEL).strip()
    if model.startswith("gemini"):
        return model
    return COACH_MODEL


def _slim_for_prompt(analyze: dict[str, Any], baseline: dict[str, Any]) -> dict[str, Any]:
    smart = analyze.get("smart_scorecard") or {}
    return {
        "url": analyze.get("url"),
        "scores": baseline.get("scores"),
        "scan_level": baseline.get("scan_level"),
        "scan_level_name": baseline.get("scan_level_name"),
        "delta_narrative_th": baseline.get("delta_narrative_th"),
        "priority_fixes": [
            {"priority": r.get("priority"), "path": r.get("path"), "problem": r.get("problem"), "fix": r.get("fix")}
            for r in (baseline.get("priority_fixes") or [])[:5]
        ],
        "weakest_layers": baseline.get("weakest_layers"),
        "revenue_queue": [
            {"priority": a.get("priority"), "action": a.get("action"), "revenue": a.get("revenue")}
            for a in (baseline.get("revenue_queue") or [])[:4]
        ],
        "honest_verdict": smart.get("honest_verdict"),
        "growth_pillars": [
            {"label": p.get("label"), "percent": p.get("percent"), "revenue_link": p.get("revenue_link")}
            for p in ((smart.get("growth_scorecard") or {}).get("pillars") or [])[:5]
        ],
    }


async def enrich_coach_with_gemini(
    analyze: dict[str, Any],
    baseline: dict[str, Any],
    *,
    is_rescan: bool = False,
) -> dict[str, Any]:
    """Gemini business Thai overlay — falls back to rule-based baseline on any error."""
    out = dict(baseline)
    if not has_llm_provider_configured():
        out["gemini_enriched"] = False
        return out
    google_key = settings.google_api_key or settings.gemini_api_key
    if not google_key:
        out["gemini_enriched"] = False
        return out

    context = _slim_for_prompt(analyze, baseline)
    scan_kind = "re-scan (free follow-up)" if is_rescan else "first paid scan"
    system = SystemMessage(
        content=(
            f"{OBOLLA_THAI_VOICE}\n\n{_THAI_HUMAN_COPY_RULES}\n\n"
            "You are OBOLLA Agent Coach for Agent-Ready / revenue growth.\n"
            "Write ONLY valid JSON (no markdown fences). Tone: Thai business coffee-corner — "
            "ตรงประเด็น เน้นรายได้ ROI ไม่โอ้อวด ไม่สัญญาผลที่วัดไม่ได้.\n"
            "Fields:\n"
            "- headline_th_business (string, ≤120 chars)\n"
            "- executive_summary_th_business (string, 2-4 sentences, Thai)\n"
            "- revenue_insight_th (string, 1-2 sentences linking score gaps to money)\n"
            "- next_steps_th_business (array of 3-5 short imperative strings in Thai)\n"
            "- email_subject_th (string, for re-scan notification email)\n"
            "- email_body_plain_th (string, 4-8 lines plain text Thai summary for email; include scores and top action)"
        )
    )
    human = HumanMessage(
        content=(
            f"Scan type: {scan_kind}\n"
            f"Site data JSON:\n{json.dumps(context, ensure_ascii=False, indent=2)}\n\n"
            "ตอบ JSON เท่านั้น"
        )
    )
    try:
        factory = LLMFactory()
        response, model_used, _warnings = await invoke_llm_with_fallback(
            factory,
            primary_model=_coach_model(),
            messages=[system, human],
            pack_slug="agent-ready-auto-fix",
        )
        raw = str(getattr(response, "content", "") or "").strip()
        if raw.startswith("```"):
            raw = raw.split("```", 2)[1]
            if raw.lstrip().startswith("json"):
                raw = raw.split("\n", 1)[-1]
        data = json.loads(raw)
        if not isinstance(data, dict):
            raise ValueError("coach gemini response not an object")

        headline_biz = str(data.get("headline_th_business") or "").strip()
        exec_biz = str(data.get("executive_summary_th_business") or "").strip()
        revenue_insight = str(data.get("revenue_insight_th") or "").strip()
        steps_biz = data.get("next_steps_th_business")
        email_subject = str(data.get("email_subject_th") or "").strip()
        email_body = str(data.get("email_body_plain_th") or "").strip()

        if headline_biz and _THAI_RE.search(headline_biz):
            out["headline_th"] = headline_biz
            out["headline_th_business"] = headline_biz
        if exec_biz and _THAI_RE.search(exec_biz):
            out["executive_summary_th"] = exec_biz
            out["executive_summary_th_business"] = exec_biz
        if revenue_insight:
            out["revenue_insight_th"] = revenue_insight
        if isinstance(steps_biz, list) and steps_biz:
            cleaned = [str(s).strip() for s in steps_biz if str(s).strip()][:5]
            if cleaned:
                out["next_steps_th"] = cleaned
                out["next_steps_th_business"] = cleaned
        if email_subject:
            out["email_subject_th"] = email_subject
        if email_body:
            out["email_body_plain_th"] = email_body

        out["gemini_enriched"] = True
        out["gemini_model"] = model_used
    except Exception as exc:  # noqa: BLE001
        logger.warning("enrich_coach_with_gemini failed: %s", exc)
        out["gemini_enriched"] = False

    return out