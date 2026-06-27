"""Free Creator Garden — companion coach + LLM composer (always $0)."""

from __future__ import annotations

import json
import re
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage

from app.core.llm import get_llm_factory
from app.expert_skills.custom_defaults import build_default_crew_config
from app.expert_skills.model_tiers import (
    apply_model_tier_to_crew_config,
    get_tier,
    list_garden_model_tiers,
    suggested_price_usd,
)
from app.graphs.utils import invoke_llm_with_fallback
from app.services.content_safety import sanitize_platform_text
from app.services.publish_insight_service import generate_publish_insight

COMPOSE_MODEL = "gemini-2.5-flash"
VALID_CATEGORIES = frozenset({"seo", "coding", "content", "support", "research", "quality"})


def _pick_category(identity: str, audience: str, problem: str) -> str:
    text = f"{identity} {audience} {problem}".lower()
    if any(w in text for w in ("seo", "google", "visibility", "website", "เว็บ", "ค้นหา")):
        return "seo"
    if any(w in text for w in ("code", "dev", "api", "python", "โค้ด", "พัฒนา")):
        return "coding"
    if any(
        w in text
        for w in (
            "write",
            "content",
            "blog",
            "เขียน",
            "บทความ",
            "youtube",
            "ยูทูบ",
            "facebook",
            "reel",
            "reels",
            "เฟซบุ๊ก",
            "การ์ตูน",
            "ลายเส้น",
            "faceless",
            "ms paint",
            "capcut",
            "kemlife",
            "ช่อง",
        )
    ):
        return "content"
    if any(w in text for w in ("support", "customer", "ช่วยเหลือ", "ลูกค้า")):
        return "support"
    if any(w in text for w in ("research", "วิจัย", "ข้อมูล", "analyze")):
        return "research"
    return "quality"


def _workflow_ideas(identity: str, audience: str, problem: str) -> list[dict[str, str]]:
    category = _pick_category(identity, audience, problem)
    audience_short = audience.strip()[:60] or "your audience"
    problem_short = problem.strip()[:80] or "a recurring task"

    templates: dict[str, list[dict[str, str]]] = {
        "seo": [
            {
                "name": f"AI visibility audit for {audience_short}",
                "pitch": f"Scan → audit → fix pack for {problem_short}. Buyers paste files today.",
                "steps": "Scan → Auditor → Fix pack → QA gate",
            },
            {
                "name": f"Local SEO action plan — {audience_short}",
                "pitch": "Technical scan + 90-day roadmap with schema and meta templates.",
                "steps": "Tech scan → Research → Analyze → Report",
            },
        ],
        "coding": [
            {
                "name": f"Coding agent for {audience_short}",
                "pitch": f"Plan → implement → review → QA for {problem_short}.",
                "steps": "Planner → Implementer → Code review → QA",
            },
            {
                "name": f"Bug triage assistant — {problem_short}",
                "pitch": "Read repo context, propose patch + tests, ship READY verdict.",
                "steps": "Explore → Plan → Patch → Review",
            },
        ],
        "content": [
            {
                "name": f"AI line-art Facebook Reels — {audience_short}",
                "pitch": (
                    f"Faceless MS Paint Reels: hook → 30–90s script "
                    f"→ 9:16 shot prompts → Reels caption QA for {problem_short}."
                ),
                "steps": "Hook → บทสั้น+เวลา → Prompt 9:16 → QA ปล่อย Reels",
            },
            {
                "name": f"AI line-art YouTube — {audience_short}",
                "pitch": (
                    f"Faceless MS Paint cartoon channel: topic → timestamped script "
                    f"→ 16:9 shot prompts → edit QA for {problem_short}."
                ),
                "steps": "หาเรื่อง → บท+เวลา → Prompt ภาพ → QA ปล่อย",
            },
            {
                "name": f"Content pipeline for {audience_short}",
                "pitch": f"Research → draft → edit → publish checklist for {problem_short}.",
                "steps": "Research → Draft → Edit → QA",
            },
        ],
        "support": [
            {
                "name": f"Support playbook — {audience_short}",
                "pitch": "Turn FAQs into step-by-step agent replies with escalation rules.",
                "steps": "Ingest → Classify → Reply draft → Human review",
            },
        ],
        "research": [
            {
                "name": f"Research brief for {audience_short}",
                "pitch": f"Structured report on {problem_short} with sources and next actions.",
                "steps": "Gather → Analyze → Summarize → QA",
            },
        ],
        "quality": [
            {
                "name": f"Quality check flow — {audience_short}",
                "pitch": f"Verify deliverables for {problem_short} before handoff to clients.",
                "steps": "Checklist → Run → Review → Verdict",
            },
        ],
    }
    return templates.get(category, templates["quality"])


def _companion_message(step: str, payload: dict[str, str]) -> tuple[str, str]:
    identity = payload.get("identity", "").strip()
    audience = payload.get("audience", "").strip()
    problem = payload.get("problem", "").strip()
    workflow_name = payload.get("workflow_name", "").strip()
    price_note = payload.get("price_note", "").strip()

    if step == "identity":
        if len(identity) < 8:
            return (
                "เล่าให้เราฟังอีกนิด — คุณเก่งเรื่องอะไร รักอะไร อยากให้คนอื่นจำคุณว่าอย่างไร",
                "Tell us a bit more — what are you good at, what do you love, how should people remember you?",
            )
        return (
            f"เยี่ยม — ตัวตนของคุณเริ่มชัดแล้ว: «{identity[:120]}» ขั้นต่อไป ใครที่คุณอยากช่วย?",
            f"Beautiful — your identity is taking shape: «{identity[:120]}» Who do you want to help next?",
        )

    if step == "audience":
        if len(audience) < 5:
            return (
                "คิดถึงคนหนึ่งที่คุณอยากช่วยจริงๆ — ร้านเล็กๆ ครู ช่าง หรือเพื่อนที่ไม่มีเวลา?",
                "Picture one real person you want to help — a shop owner, teacher, maker, or friend with no time.",
            )
        return (
            f"เราเห็นภาพแล้ว — คุณจะช่วย «{audience[:100]}» งานหนักอะไรที่พวกเขาทำซ้ำๆ ทุกวัน?",
            f"We see them — you'll help «{audience[:100]}». What heavy task do they repeat every day?",
        )

    if step == "problem":
        if len(problem) < 8:
            return (
                "อธิบายปัญหาที่ทำให้เขาเหนื่อย — เช่น audit เว็บ เขียนรายงาน หรือแก้บั๊กซ้ำๆ",
                "Describe the task that exhausts them — audits, reports, repetitive fixes, etc.",
            )
        return (
            "เราช่วยร่างไอเดีย agent workflow ให้แล้ว — เลือกอันที่รู้สึกว่า «นี่แหละคุณค่าที่แบ่งปันได้»",
            "We drafted agent workflow ideas — pick the one that feels like real value you can share.",
        )

    if step == "workflow":
        name = workflow_name or "your first flow"
        return (
            f"ไอเดีย «{name}» ดีมาก — ต่อไปตั้งราคาที่ซื่อสัตย์ (ฟรีถ้า local, จ่ายเมื่อใช้ cloud)",
            f"«{name}» is a strong start — price it honestly (free when local, paid when cloud APIs run).",
        )

    if step == "publish":
        return (
            "พร้อมแล้ว — เปิด creator studio แล้วเผยแพร่ flow แรกของคุณ เราอยู่ข้างคุณ",
            "You're ready — open creator studio and publish your first flow. We're beside you.",
        )

    price_hint = f" {price_note}" if price_note else ""
    return (
        f"ผมอยู่ข้างคุณในการสร้างมันครับ{price_hint}",
        f"We're beside you in building this.{price_hint}",
    )


def coach_creator_garden(step: str, answers: dict[str, Any]) -> dict[str, Any]:
    payload = {k: str(v or "") for k, v in answers.items()}
    message_th, message_en = _companion_message(step, payload)
    ideas: list[dict[str, str]] = []
    if step in ("problem", "workflow", "publish"):
        ideas = _workflow_ideas(
            payload.get("identity", ""),
            payload.get("audience", ""),
            payload.get("problem", ""),
        )

    suggested_name = ideas[0]["name"] if ideas else ""
    suggested_description = ideas[0]["pitch"] if ideas else ""
    category = _pick_category(
        payload.get("identity", ""),
        payload.get("audience", ""),
        payload.get("problem", ""),
    )

    draft_name = payload.get("workflow_name") or suggested_name
    draft_description = payload.get("workflow_description") or suggested_description
    suggested = _build_suggested_draft(
        identity=payload.get("identity", ""),
        audience=payload.get("audience", ""),
        problem=payload.get("problem", ""),
        workflow_name=draft_name,
        workflow_description=draft_description,
        category=category,
        model_tier_id="standard",
    )
    return {
        "message_th": message_th,
        "message_en": message_en,
        "workflow_ideas": ideas,
        "suggested_draft": suggested,
        "companion_th": "ผมอยู่ข้างคุณในการสร้างมันครับ",
        "model_tiers": list_garden_model_tiers(),
    }


def _capabilities_for_category(category: str) -> list[str]:
    mapping = {
        "seo": ["seo", "ai-visibility", "fix-pack"],
        "coding": ["coding-agent", "code-review", "qa"],
        "content": ["content", "research", "editing"],
        "support": ["support", "playbook", "qa"],
        "research": ["research", "analysis", "report"],
        "quality": ["quality", "checklist", "qa"],
    }
    return mapping.get(category, ["agent-flow", "qa"])


def _extract_json_object(text: str) -> dict[str, Any] | None:
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
        cleaned = re.sub(r"\s*```$", "", cleaned)
    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if start < 0 or end <= start:
        return None
    try:
        parsed = json.loads(cleaned[start : end + 1])
    except json.JSONDecodeError:
        return None
    return parsed if isinstance(parsed, dict) else None


def _normalize_category(value: str | None) -> str:
    cat = (value or "").strip().lower()
    return cat if cat in VALID_CATEGORIES else "quality"


def _build_suggested_draft(
    *,
    identity: str,
    audience: str,
    problem: str,
    workflow_name: str,
    workflow_description: str,
    category: str,
    skill_md: str | None = None,
    pipeline_label: str | None = None,
    model_tier_id: str = "standard",
    steps: list[dict] | None = None,
    input_mode: str | None = None,
    run_title: str | None = None,
) -> dict[str, Any]:
    crew_config = build_default_crew_config(
        category=category,
        name=workflow_name or "Custom flow",
        description=workflow_description or "Creator garden flow",
        skill_md=skill_md,
        pipeline_label=pipeline_label,
        input_mode=input_mode,
        run_title=run_title,
        steps=steps,
    )
    crew_config = apply_model_tier_to_crew_config(crew_config, model_tier_id)
    price = suggested_price_usd(model_tier_id)
    return {
        "identity": identity,
        "audience": audience,
        "problem": problem,
        "name": workflow_name,
        "description": workflow_description,
        "category": category,
        "capabilities": _capabilities_for_category(category),
        "input_mode": crew_config.get("input_mode"),
        "pipeline_label": crew_config.get("pipeline_label"),
        "run_title": crew_config.get("run_title"),
        "skill_md": crew_config.get("skill_md"),
        "crew_config": crew_config,
        "model_tier_id": model_tier_id,
        "suggested_price_usd": price,
    }


def _rule_compose_from_story(raw_story: str) -> dict[str, Any]:
    story = raw_story.strip()
    lines = [ln.strip() for ln in story.splitlines() if ln.strip()]
    identity = lines[0][:400] if lines else story[:400]
    audience = lines[1][:200] if len(lines) > 1 else ""
    problem = lines[2][:300] if len(lines) > 2 else (story[200:500] if len(story) > 200 else story)
    category = _pick_category(identity, audience, problem or story)
    ideas = _workflow_ideas(identity, audience, problem or story)
    idea = ideas[0] if ideas else {"name": "Custom agent flow", "pitch": story[:200]}
    return {
        "identity": identity,
        "audience": audience or "คนที่คุณอยากช่วย",
        "problem": problem or story[:300],
        "workflow_name": idea["name"],
        "workflow_description": idea["pitch"],
        "category": category,
        "message_th": (
            "เราจัดร่างจากเรื่องที่คุณเล่าแล้ว — กดปุ่มสร้างได้เลย หรือแก้ในช่องด้านล่างก่อนก็ได้ครับ"
        ),
        "message_en": (
            "We shaped a draft from your story — press create, or tweak the fields below first."
        ),
        "used_llm": False,
    }


async def _llm_compose_from_story(raw_story: str, locale: str) -> dict[str, Any] | None:
    if len(raw_story.strip()) < 12:
        return None
    lang_hint = "Respond in Thai for message_th; English for message_en." if locale == "th" else ""
    system = (
        "You are OBOLLA Companion — warm, respectful, professional. "
        "Retirees and new creators share life experience; turn it into a sellable agent flow. "
        "Return ONLY valid JSON with keys: "
        "identity, audience, problem, workflow_name, workflow_description, category, "
        "skill_md, pipeline_label, message_th, message_en. "
        "category must be one of: seo, coding, content, support, research, quality. "
        "skill_md: markdown playbook for the agent (Purpose, Pipeline, Buyer input, Deliverables). "
        "Keep workflow_name under 80 chars. Be encouraging, never condescending. "
        f"{lang_hint}"
    )
    human = f"Creator story (may be rough typing, Thai/English mixed OK):\n\n{raw_story[:6000]}"
    factory = get_llm_factory()
    try:
        response, _, _ = await invoke_llm_with_fallback(
            factory,
            primary_model=COMPOSE_MODEL,
            messages=[SystemMessage(content=system), HumanMessage(content=human)],
        )
        content = str(response.content or "")
        parsed = _extract_json_object(content)
        if not parsed:
            return None
        category = _normalize_category(str(parsed.get("category", "")))
        workflow_name = str(parsed.get("workflow_name") or parsed.get("name") or "").strip()
        workflow_description = str(parsed.get("workflow_description") or parsed.get("description") or "").strip()
        if not workflow_name:
            return None
        return {
            "identity": str(parsed.get("identity") or "").strip()[:500],
            "audience": str(parsed.get("audience") or "").strip()[:300],
            "problem": str(parsed.get("problem") or "").strip()[:500],
            "workflow_name": workflow_name[:120],
            "workflow_description": workflow_description[:800],
            "category": category,
            "skill_md": str(parsed.get("skill_md") or "").strip()[:8000] or None,
            "pipeline_label": str(parsed.get("pipeline_label") or "").strip()[:120] or None,
            "message_th": str(parsed.get("message_th") or "").strip()[:600],
            "message_en": str(parsed.get("message_en") or "").strip()[:600],
            "used_llm": True,
        }
    except Exception:
        return None


async def compose_creator_garden(
    *,
    raw_story: str,
    locale: str = "th",
    model_tier_id: str = "standard",
) -> dict[str, Any]:
    """Turn free-form story into a polished agent-flow draft — LLM with rule fallback."""
    story = raw_story.strip()
    if len(story) < 8:
        return {
            "message_th": "เล่าให้เราฟังอีกนิดครับ — คุณเก่งเรื่องอะไร อยากช่วยใคร งานอะไรที่ทำซ้ำจนเหนื่อย",
            "message_en": "Tell us a bit more — what you're good at, who you want to help, what heavy task repeats.",
            "workflow_ideas": [],
            "suggested_draft": {},
            "companion_th": "ผมอยู่ข้างคุณในการสร้างมันครับ",
            "composed": False,
            "used_llm": False,
        }

    composed = await _llm_compose_from_story(story, locale)
    if not composed:
        composed = _rule_compose_from_story(story)

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
    )

    message_th = sanitize_platform_text(
        composed.get("message_th")
        or f"จัดให้แล้วครับ — «{suggested['name']}» พร้อมสร้าง agent flow ได้เลย",
        fallback=f"จัดให้แล้วครับ — «{suggested['name']}» พร้อมสร้าง agent flow ได้เลย",
    )
    message_en = sanitize_platform_text(
        composed.get("message_en")
        or f"Done — «{suggested['name']}» is ready. Press create when it feels right.",
        fallback=f"Done — «{suggested['name']}» is ready. Press create when it feels right.",
    )

    value_insight = await generate_publish_insight(
        raw_story=story,
        locale=locale,
        workflow_name=suggested.get("name", ""),
        description=suggested.get("description", ""),
        category=suggested.get("category", "quality"),
        identity=suggested.get("identity", ""),
        audience=suggested.get("audience", ""),
        problem=suggested.get("problem", ""),
        model_tier_id=tier_id,
    )
    if value_insight.get("price_usd"):
        suggested["suggested_price_usd"] = value_insight["price_usd"]

    return {
        "message_th": message_th,
        "message_en": message_en,
        "workflow_ideas": ideas,
        "suggested_draft": suggested,
        "value_insight": value_insight,
        "companion_th": "ผมอยู่ข้างคุณในการสร้างมันครับ",
        "composed": True,
        "used_llm": bool(composed.get("used_llm")),
        "model_tiers": list_garden_model_tiers(),
    }