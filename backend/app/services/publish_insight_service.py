"""Pre-publish value research — trends, encouraging pricing rationale, DNA-aligned insight."""

from __future__ import annotations

import hashlib
import json
import re
from decimal import Decimal, ROUND_HALF_UP
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage

from app.core.llm import get_llm_factory
from app.expert_skills.model_tiers import GARDEN_BASE_PRICE_USD, suggested_price_usd
from app.graphs.utils import invoke_llm_with_fallback
from app.services.content_safety import sanitize_platform_text

INSIGHT_MODEL = "gemini-2.5-flash"

_CATEGORY_VALUE_BUMP: dict[str, Decimal] = {
    "seo": Decimal("1.75"),
    "coding": Decimal("1.25"),
    "research": Decimal("0.85"),
    "content": Decimal("0.55"),
    "support": Decimal("0.40"),
    "quality": Decimal("0.30"),
}

_TREND_CONTEXT_2026 = """
2026 AI agent marketplace signals (use for grounded, non-hype research):
- Buyers pay for repeatable outcomes (audit packs, drafts, checklists), not chat.
- Vertical micro-flows (one audience + one painful task) outperform generic assistants.
- Consent-first remote support and transparent per-run pricing build trust.
- Thai creators win with lived experience + local language nuance in deliverables.
- Multi-step pipelines with QA gates justify higher run fees than single-shot prompts.
- Agent-to-agent orchestration and creator-owned flows are growing vs monolithic chatbots.
"""


def _round_market_price(amount: Decimal) -> Decimal:
    """Round to .49 / .99 style pricing — never flat identical across different flows."""
    if amount < Decimal("0.99"):
        return Decimal("0.99")
    whole = int(amount)
    cents = amount - Decimal(whole)
    if cents < Decimal("0.50"):
        return Decimal(whole) + Decimal("0.49")
    return Decimal(whole) + Decimal("0.99")


_EXPERIENCE_MARKERS = (
    "ปี",
    "year",
    "ลูกค้า",
    "client",
    "โปรเจกต์",
    "project",
    "portfolio",
    "เคยทำ",
    "ประสบการณ์",
    "experience",
    "เชี่ยวชาญ",
    "expert",
    "มืออาชีพ",
    "professional",
)

_DELIVERABLE_MARKERS = (
    "checklist",
    "report",
    "draft",
    "audit",
    "template",
    "playbook",
    "รายงาน",
    "แบบร่าง",
    "เช็กลิสต์",
    "สรุป",
    "deliverable",
    "pipeline",
    "qa",
)

_TREND_MARKERS = (
    "ai agent",
    "automation",
    "reel",
    "youtube",
    "seo",
    "marketplace",
    "local",
    "thai",
    "ไทย",
    "sme",
    "creator",
    "workflow",
)


def _specificity_score(
    *,
    identity: str,
    audience: str,
    problem: str,
    description: str,
    raw_story: str,
) -> int:
    score = 0
    if len(identity.strip()) >= 30:
        score += 1
    if len(audience.strip()) >= 25:
        score += 1
    if len(problem.strip()) >= 40:
        score += 1
    if len(description.strip()) >= 60:
        score += 1
    if len(raw_story.strip()) >= 120:
        score += 1
    niche_markers = (
        "ร้าน",
        "ครู",
        "ฟรีแลนซ์",
        "SME",
        "clinic",
        "shop",
        "YouTube",
        "Reel",
        "audit",
        "SEO",
        "report",
        "บัญชี",
        "คลินิก",
    )
    blob = f"{identity} {audience} {problem} {description} {raw_story}".lower()
    if any(m.lower() in blob for m in niche_markers):
        score += 1
    return min(score, 5)


def _price_fingerprint(
    *,
    workflow_name: str,
    category: str,
    audience: str,
    model_tier_id: str,
) -> int:
    seed = f"{workflow_name}|{category}|{audience}|{model_tier_id}"
    return int(hashlib.sha256(seed.encode()).hexdigest()[:4], 16) % 7


def compute_value_score(
    *,
    category: str,
    identity: str,
    audience: str,
    problem: str,
    workflow_name: str,
    description: str,
    raw_story: str = "",
    market_boost: int = 0,
) -> tuple[int, list[dict[str, str]]]:
    """0–100 — richer story, experience, trends → higher score → higher allowed price."""
    blob = f"{identity} {audience} {problem} {description} {raw_story} {workflow_name}".lower()
    score = 0
    factors: list[dict[str, str]] = []

    spec = _specificity_score(
        identity=identity,
        audience=audience,
        problem=problem,
        description=description,
        raw_story=raw_story,
    )
    spec_pts = spec * 5
    score += spec_pts
    if spec >= 3:
        factors.append(
            {
                "key": "specificity",
                "th": "ข้อมูลแน่น — รู้ว่าช่วยใคร แก้อะไร",
                "en": "Dense positioning — clear who you help and what you fix",
            }
        )

    story_len = len(raw_story.strip())
    if story_len >= 500:
        score += 18
        factors.append({"key": "story", "th": "เล่าประสบการณ์ละเอียด — เราแปลงเป็น product ได้แม่นขึ้น", "en": "Rich story — we can shape a sharper product"})
    elif story_len >= 220:
        score += 12
    elif story_len >= 80:
        score += 6

    exp_hits = sum(1 for m in _EXPERIENCE_MARKERS if m.lower() in blob)
    if exp_hits >= 3:
        score += 14
        factors.append({"key": "experience", "th": "มีรากจากประสบการณ์จริง — คุณค่าสูงกว่า template ทั่วไป", "en": "Rooted in real experience — worth more than a generic template"})
    elif exp_hits >= 1:
        score += 7

    deliv_hits = sum(1 for m in _DELIVERABLE_MARKERS if m.lower() in blob)
    if deliv_hits >= 2:
        score += 10
        factors.append({"key": "deliverable", "th": "บอกผลลัพธ์ชัด — buyer รู้ว่าได้อะไรต่อรัน", "en": "Clear deliverables — buyers know what one run buys"})

    trend_hits = sum(1 for m in _TREND_MARKERS if m.lower() in blob)
    if trend_hits >= 3:
        score += 10
        factors.append({"key": "trend", "th": "เข้ากับเทรนด์ตลาดตอนนี้ — มีแนวโน้มถูกมองหา", "en": "Aligns with 2026 demand — easier to discover"})
    elif trend_hits >= 1:
        score += 5

    cat = (category or "quality").lower()
    cat_pts = {"seo": 8, "coding": 7, "research": 6, "content": 5, "support": 4, "quality": 3}.get(cat, 3)
    score += cat_pts

    boost = max(0, min(20, int(market_boost)))
    if boost >= 12:
        score += boost
        factors.append({"key": "wow", "th": "ไอเดียโดดเด่น / น่าสนใจในตลาด — ราคาแนะนำสูงขึ้นตามคุณค่า", "en": "Standout idea — higher suggested price reflects perceived wow"})
    elif boost >= 5:
        score += boost

    return min(100, score), factors


def _value_tier(score: int) -> str:
    if score >= 72:
        return "premium"
    if score >= 48:
        return "strong"
    if score >= 28:
        return "growing"
    return "starter"


def compute_personalized_price(
    *,
    category: str,
    identity: str,
    audience: str,
    problem: str,
    workflow_name: str,
    description: str,
    model_tier_id: str,
    raw_story: str = "",
    market_boost: int = 0,
) -> tuple[str, list[dict[str, str]], int, str]:
    """Return (price_usd, factors, value_score, value_tier)."""
    base = Decimal(str(suggested_price_usd(model_tier_id)))
    cat = (category or "quality").lower()
    bump = _CATEGORY_VALUE_BUMP.get(cat, Decimal("0.35"))
    value_score, value_factors = compute_value_score(
        category=category,
        identity=identity,
        audience=audience,
        problem=problem,
        workflow_name=workflow_name,
        description=description,
        raw_story=raw_story,
        market_boost=market_boost,
    )
    value_tier = _value_tier(value_score)
    value_premium = Decimal(value_score) * Decimal("0.055")
    spec = _specificity_score(
        identity=identity,
        audience=audience,
        problem=problem,
        description=description,
        raw_story=raw_story,
    )
    spec_addon = Decimal(spec) * Decimal("0.12")
    jitter = Decimal(_price_fingerprint(workflow_name=workflow_name, category=cat, audience=audience, model_tier_id=model_tier_id)) * Decimal("0.09")
    raw_total = base + bump + value_premium + spec_addon + jitter
    raw_total = min(raw_total, Decimal("24.99"))
    total = _round_market_price(raw_total)

    factors: list[dict[str, str]] = [
        {
            "key": "base",
            "th": f"ค่าพื้นฐาน flow + ชุดโมเดล (${base})",
            "en": f"Base flow + model tier (${base})",
        },
        {
            "key": "category",
            "th": f"หมวด {cat} — มูลค่าต่อรันที่ buyer คุ้นในตลาด (+${bump})",
            "en": f"{cat} category — typical buyer value per run (+${bump})",
        },
        {
            "key": "value_score",
            "th": f"คะแนนคุณค่า {value_score}/100 ({value_tier}) — ยิ่งแน่น ยิ่งแพงได้ตามจริง",
            "en": f"Value score {value_score}/100 ({value_tier}) — denser stories earn higher ceilings",
        },
    ]
    factors.extend(value_factors)
    if jitter > 0:
        factors.append(
            {
                "key": "unique",
                "th": "ราคาไม่ซ้ำใคร — สะท้อนเอกลักษณ์ flow ของคุณ",
                "en": "Unique to your flow — not a flat marketplace price",
            }
        )
    price_str = str(total.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))
    return price_str, factors, value_score, value_tier


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


def _rule_insight(
    *,
    locale: str,
    workflow_name: str,
    description: str,
    category: str,
    identity: str,
    audience: str,
    problem: str,
    price_usd: str,
    price_factors: list[dict[str, str]],
) -> dict[str, Any]:
    cat = category or "quality"
    trends_th = [
        f"ปี 2026 ผู้ซื้อจ่ายให้ flow ที่แก้งานซ้ำของ {audience or 'กลุ่มเป้าหมาย'} ได้จริง",
        "Agent แนวแคบ (หนึ่งปัญหา + หนึ่งผลลัพธ์) ขายดีกว่าผู้ช่วยทั่วไป",
        "ภาษาไทย + ประสบการณ์จริงของคุณ คือความต่างที่ AI ทั่วไปทำแทนไม่ได้",
    ]
    trends_en = [
        f"In 2026 buyers pay for flows that solve repeat work for {audience or 'your audience'}",
        "Narrow agents (one problem → one outcome) beat generic chat assistants",
        "Your lived experience + language nuance is what generic AI cannot copy",
    ]
    value_th = (
        f"«{workflow_name}» ยกประสบการณ์ของคุณ ({identity[:80] or 'ความเชี่ยวชาญของคุณ'}) "
        f"มาเป็น pipeline ที่ buyer รันแล้วได้ {description[:120] or 'ผลลัพธ์ที่จับต้องได้'} "
        f"— นี่คือสิ่งที่เราทำงานหนักให้หลังบ้าน เพื่อให้คุณไปใช้ชีวิตได้"
    )
    value_en = (
        f"«{workflow_name}» turns your experience ({identity[:80] or 'your expertise'}) "
        f"into a pipeline buyers can run for {description[:120] or 'concrete outcomes'} "
        f"— we do the heavy lifting behind the scenes so you can live your life."
    )
    encourage_th = (
        "ไอเดียของคุณมีรากจากชีวิตจริง — แค่เพิ่มตัวอย่าง input หนึ่งชุดก่อนเผยแพร่ "
        "flow จะดูน่าเชื่อถือขึ้นอีกขั้น เราอยู่ข้างคุณ"
    )
    encourage_en = (
        "Your idea is rooted in real life — add one example input before publishing "
        "and buyers will trust it even more. We are beside you."
    )
    factor_lines_th = [f["th"] for f in price_factors]
    factor_lines_en = [f["en"] for f in price_factors]
    return {
        "trend_signals_th": trends_th,
        "trend_signals_en": trends_en,
        "value_story_th": value_th,
        "value_story_en": value_en,
        "price_usd": price_usd,
        "price_rationale_th": " · ".join(factor_lines_th[:4]),
        "price_rationale_en": " · ".join(factor_lines_en[:4]),
        "encouragement_th": encourage_th,
        "encouragement_en": encourage_en,
        "future_fit_th": f"แนว {cat} ยังโตใน 2026–2027 เมื่อ creator เป็นเจ้าของ flow จริง",
        "future_fit_en": f"{cat} flows keep growing 2026–2027 as creators own real pipelines",
        "used_llm": False,
    }


async def _llm_insight(
    *,
    locale: str,
    raw_story: str,
    workflow_name: str,
    description: str,
    category: str,
    identity: str,
    audience: str,
    problem: str,
    price_usd: str,
    price_factors: list[dict[str, str]],
    model_tier_id: str,
) -> dict[str, Any] | None:
    lang = "Thai" if locale == "th" else "English"
    factor_blob = json.dumps(price_factors, ensure_ascii=False)
    system = (
        "You are OBOLLA Companion — warm, never condescending, never saying an idea is bad. "
        "We work vastly harder than the creator's short story to turn lived experience into a sellable agent flow. "
        "Research 2026 agent/creator trends and feasibility for THIS specific flow. "
        "Return ONLY valid JSON with keys: "
        "trend_signals (array of 3 objects with th, en — short trend bullets), "
        "value_story_th, value_story_en (2-3 sentences — why this has value, encouraging), "
        "price_rationale_th, price_rationale_en (explain the given price factors warmly, not judgmental), "
        "encouragement_th, encouragement_en (one sentence — motivate to improve, not criticize), "
        "future_fit_th, future_fit_en (one sentence — trend/future fit), "
        "market_boost (integer 0-20: how trendy, feasible, and wow this specific flow feels in 2026). "
        "Do NOT change the price number. Do NOT use hype like 100% guaranteed. "
        f"Primary language for warmth: {lang}."
    )
    human = (
        f"{_TREND_CONTEXT_2026}\n\n"
        f"Creator story:\n{raw_story[:4000]}\n\n"
        f"Flow name: {workflow_name}\n"
        f"Description: {description}\n"
        f"Category: {category}\n"
        f"Identity: {identity}\n"
        f"Audience: {audience}\n"
        f"Problem: {problem}\n"
        f"Model tier: {model_tier_id}\n"
        f"Suggested price USD (fixed): {price_usd}\n"
        f"Price factors JSON: {factor_blob}\n"
    )
    factory = get_llm_factory()
    try:
        response, _, _ = await invoke_llm_with_fallback(
            factory,
            primary_model=INSIGHT_MODEL,
            messages=[SystemMessage(content=system), HumanMessage(content=human)],
        )
        parsed = _extract_json_object(str(response.content or ""))
        if not parsed:
            return None
        trends_raw = parsed.get("trend_signals") or []
        trends_th: list[str] = []
        trends_en: list[str] = []
        if isinstance(trends_raw, list):
            for item in trends_raw[:4]:
                if isinstance(item, dict):
                    trends_th.append(str(item.get("th") or "").strip()[:200])
                    trends_en.append(str(item.get("en") or "").strip()[:200])
                elif isinstance(item, str):
                    trends_th.append(item[:200])
                    trends_en.append(item[:200])
        trends_th = [t for t in trends_th if t]
        trends_en = [t for t in trends_en if t]
        return {
            "trend_signals_th": trends_th,
            "trend_signals_en": trends_en,
            "value_story_th": sanitize_platform_text(str(parsed.get("value_story_th") or ""), fallback=""),
            "value_story_en": sanitize_platform_text(str(parsed.get("value_story_en") or ""), fallback=""),
            "price_usd": price_usd,
            "price_rationale_th": sanitize_platform_text(str(parsed.get("price_rationale_th") or ""), fallback=""),
            "price_rationale_en": sanitize_platform_text(str(parsed.get("price_rationale_en") or ""), fallback=""),
            "encouragement_th": sanitize_platform_text(str(parsed.get("encouragement_th") or ""), fallback=""),
            "encouragement_en": sanitize_platform_text(str(parsed.get("encouragement_en") or ""), fallback=""),
            "future_fit_th": sanitize_platform_text(str(parsed.get("future_fit_th") or ""), fallback=""),
            "future_fit_en": sanitize_platform_text(str(parsed.get("future_fit_en") or ""), fallback=""),
            "used_llm": True,
        }
    except Exception:
        return None


async def generate_publish_insight(
    *,
    raw_story: str = "",
    locale: str = "th",
    workflow_name: str,
    description: str,
    category: str,
    identity: str = "",
    audience: str = "",
    problem: str = "",
    model_tier_id: str = "standard",
) -> dict[str, Any]:
    """Trend research + encouraging value narrative + personalized price rationale."""
    loc = "th" if locale.lower().startswith("th") else "en"
    preview_price, preview_factors, preview_score, preview_tier = compute_personalized_price(
        category=category,
        identity=identity,
        audience=audience,
        problem=problem,
        workflow_name=workflow_name,
        description=description,
        model_tier_id=model_tier_id,
        raw_story=raw_story,
    )
    insight = await _llm_insight(
        locale=loc,
        raw_story=raw_story,
        workflow_name=workflow_name,
        description=description,
        category=category,
        identity=identity,
        audience=audience,
        problem=problem,
        price_usd=preview_price,
        price_factors=preview_factors,
        model_tier_id=model_tier_id,
    )
    market_boost = 0
    if insight and isinstance(insight.get("market_boost"), (int, float, str)):
        try:
            market_boost = int(insight["market_boost"])
        except (TypeError, ValueError):
            market_boost = 0
    price_usd, price_factors, value_score, value_tier = compute_personalized_price(
        category=category,
        identity=identity,
        audience=audience,
        problem=problem,
        workflow_name=workflow_name,
        description=description,
        model_tier_id=model_tier_id,
        raw_story=raw_story,
        market_boost=market_boost,
    )
    if not insight or not insight.get("value_story_th") and not insight.get("value_story_en"):
        insight = _rule_insight(
            locale=loc,
            workflow_name=workflow_name,
            description=description,
            category=category,
            identity=identity,
            audience=audience,
            problem=problem,
            price_usd=price_usd,
            price_factors=price_factors,
        )
    else:
        rule = _rule_insight(
            locale=loc,
            workflow_name=workflow_name,
            description=description,
            category=category,
            identity=identity,
            audience=audience,
            problem=problem,
            price_usd=price_usd,
            price_factors=price_factors,
        )
        if not insight.get("trend_signals_th"):
            insight["trend_signals_th"] = rule["trend_signals_th"]
        if not insight.get("trend_signals_en"):
            insight["trend_signals_en"] = rule["trend_signals_en"]
        if not insight.get("value_story_th"):
            insight["value_story_th"] = rule["value_story_th"]
        if not insight.get("value_story_en"):
            insight["value_story_en"] = rule["value_story_en"]
        if not insight.get("price_rationale_th"):
            insight["price_rationale_th"] = rule["price_rationale_th"]
        if not insight.get("encouragement_th"):
            insight["encouragement_th"] = rule["encouragement_th"]
        if not insight.get("encouragement_en"):
            insight["encouragement_en"] = rule["encouragement_en"]

    insight["price_usd"] = price_usd
    insight["max_price_usd"] = price_usd
    insight["pricing_ceiling_usd"] = price_usd
    insight["value_score"] = value_score
    insight["value_tier"] = value_tier
    insight["price_factors"] = price_factors
    insight["base_price_usd"] = str(GARDEN_BASE_PRICE_USD)
    insight["composed"] = True
    return insight


def build_creator_test_task(skill: Any) -> str:
    """Synthetic buyer task for pre-publish smoke run."""
    cc = skill.crew_config or {}
    input_mode = cc.get("input_mode") or "task"
    name = skill.name or "Agent flow"
    desc = skill.description or ""
    category = (skill.category or "general").lower()
    if input_mode == "url":
        return "https://example.com — run a full visibility audit demo for creator pre-publish test."
    if category == "content":
        return (
            f"[Creator pre-publish test] Run «{name}» once: {desc[:300]}. "
            "Produce a concise sample deliverable suitable for a marketplace preview."
        )
    if category == "coding":
        return (
            f"[Creator pre-publish test] Plan and outline (no repo access needed) for: {desc[:280]}. "
            "Return a structured implementation checklist."
        )
    if category == "seo":
        return "https://example.com — pre-publish SEO/visibility audit sample run."
    return (
        f"[Creator pre-publish test] Execute «{name}»: {desc[:320]}. "
        "Deliver a realistic sample output a buyer could expect from one run."
    )