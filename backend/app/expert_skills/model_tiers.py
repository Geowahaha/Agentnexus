"""Creator Garden model tiers — buyer price adds on top of base run fee."""

from __future__ import annotations

from copy import deepcopy
from decimal import Decimal
from typing import Any

from app.core.config import settings
from app.core.llm import resolve_provider

GARDEN_BASE_PRICE_USD = Decimal("0.99")
STANDARD_TIER_ID = "standard"


def _provider_ready(provider: str) -> bool:
    if provider == "openai":
        return bool(settings.openai_api_key)
    if provider == "anthropic":
        return bool(settings.anthropic_api_key)
    if provider == "google":
        return bool(settings.google_api_key or settings.gemini_api_key)
    if provider == "xai":
        return bool(settings.xai_api_key)
    if provider == "ollama":
        return bool(settings.ollama_enabled)
    if provider in ("kling", "seedance"):
        return False
    return True


def _tier_catalog() -> list[dict[str, Any]]:
    return [
        {
            "id": "standard",
            "kind": "llm",
            "addon_usd": "0.00",
            "label_en": "Standard (default)",
            "label_th": "มาตรฐาน (ค่าเริ่มต้น)",
            "engines_en": "Gemini 2.5 Flash + Grok 3 Mini",
            "engines_th": "Gemini 2.5 Flash + Grok 3 Mini",
            "hint_en": "Best value for most creator flows.",
            "hint_th": "คุ้มที่สุดสำหรับ flow ทั่วไป",
            "primary_model": "gemini-2.5-flash",
            "secondary_model": "grok-3-mini",
            "requires": ["google", "xai"],
        },
        {
            "id": "composer-2.5",
            "kind": "llm",
            "addon_usd": "1.50",
            "label_en": "Composer 2.5 class",
            "label_th": "Composer 2.5",
            "engines_en": "GPT-4.1 + Grok 3 Mini",
            "engines_th": "GPT-4.1 + Grok 3 Mini",
            "hint_en": "Deeper reasoning for structured agent flows.",
            "hint_th": "คิดลึกขึ้น — เหมาะ flow ที่มีหลายขั้น",
            "primary_model": "gpt-4.1",
            "secondary_model": "grok-3-mini",
            "requires": ["openai", "xai"],
        },
        {
            "id": "gpt-5",
            "kind": "llm",
            "addon_usd": "3.50",
            "label_en": "GPT-5",
            "label_th": "GPT-5",
            "engines_en": "GPT-5 + Grok 3 Mini QA",
            "engines_th": "GPT-5 + Grok 3 Mini ตรวจคุณภาพ",
            "hint_en": "Flagship OpenAI — premium buyer outcomes.",
            "hint_th": "ระดับพรีเมียม — ผลลัพธ์ละเอียดขึ้น",
            "primary_model": "gpt-5",
            "secondary_model": "grok-3-mini",
            "requires": ["openai", "xai"],
        },
        {
            "id": "sonnet-4.6",
            "kind": "llm",
            "addon_usd": "2.00",
            "label_en": "Claude Sonnet 4.6",
            "label_th": "Claude Sonnet 4.6",
            "engines_en": "Sonnet 4.6 + Haiku 4.5 QA",
            "engines_th": "Sonnet 4.6 + Haiku 4.5 ตรวจคุณภาพ",
            "hint_en": "Balanced Claude tier for writing & analysis.",
            "hint_th": "สมดุล — เขียนและวิเคราะห์เก่ง",
            "primary_model": "claude-sonnet-4-6",
            "secondary_model": "claude-haiku-4-5-20251001",
            "requires": ["anthropic"],
        },
        {
            "id": "opus",
            "kind": "llm",
            "addon_usd": "5.00",
            "label_en": "Claude Opus",
            "label_th": "Claude Opus",
            "engines_en": "Opus 4 + Sonnet 4.6 review",
            "engines_th": "Opus 4 + Sonnet 4.6 ตรวจทาน",
            "hint_en": "Highest Claude tier — complex expert flows.",
            "hint_th": "ระดับสูงสุด — งานเชี่ยวชาญซับซ้อน",
            "primary_model": "claude-opus-4-20250514",
            "secondary_model": "claude-sonnet-4-6",
            "requires": ["anthropic"],
        },
        {
            "id": "fable5-local",
            "kind": "local",
            "addon_usd": "0.00",
            "base_override_usd": "0.00",
            "label_en": "Fable-5 Local LoRA",
            "label_th": "Fable-5 Local (เครื่องคุณ)",
            "engines_en": "qwen3.6-27b-fable5 via Ollama",
            "engines_th": "qwen3.6-27b-fable5 บน Ollama",
            "hint_en": "$0 cloud — buyer runs on their GPU.",
            "hint_th": "ฟรีคลาวด์ — ผู้ซื้อรันบน GPU ตัวเอง",
            "primary_model": "qwen3.6-27b-fable5",
            "secondary_model": "qwen3.6-27b-fable5",
            "requires": ["ollama"],
            "force_unavailable": True,
            "unavailable_reason_en": "Server Ollama not enabled — choose when you host locally.",
            "unavailable_reason_th": "เซิร์ฟเวอร์ยังไม่เปิด Ollama — เลือกเมื่อรันบนเครื่องตัวเอง",
        },
        {
            "id": "fable5-pro",
            "kind": "llm",
            "addon_usd": "4.01",
            "label_en": "Fable-5 Pro (cloud)",
            "label_th": "Fable-5 Pro (คลาวด์)",
            "engines_en": "GPT-4.1 + Grok 3 Mini",
            "engines_th": "GPT-4.1 + Grok 3 Mini",
            "hint_en": "Same stack as flagship $5 coding agent.",
            "hint_th": "ชุดเดียวกับ coding agent $5",
            "primary_model": "gpt-4.1",
            "secondary_model": "grok-3-mini",
            "requires": ["openai", "xai"],
        },
        {
            "id": "kling",
            "kind": "video",
            "addon_usd": "8.00",
            "label_en": "KLING video",
            "label_th": "KLING วิดีโอ",
            "engines_en": "Script → KLING render → QA",
            "engines_th": "สคริปต์ → เรนเดอร์ KLING → ตรวจคุณภาพ",
            "hint_en": "Short-form video flows (beta).",
            "hint_th": "flow วิดีโอสั้น (เบต้า)",
            "primary_model": "gemini-2.5-flash",
            "secondary_model": "grok-3-mini",
            "media_provider": "kling",
            "requires": ["google", "kling"],
            "force_unavailable": True,
            "unavailable_reason_en": "KLING integration coming soon — preview pricing now.",
            "unavailable_reason_th": "KLING กำลังเชื่อมต่อ — ดูราคาล่วงหน้าได้",
        },
        {
            "id": "seedance",
            "kind": "video",
            "addon_usd": "6.00",
            "label_en": "Seedance video",
            "label_th": "Seedance วิดีโอ",
            "engines_en": "Brief → Seedance motion → QA",
            "engines_th": "บรีฟ → โมชัน Seedance → ตรวจคุณภาพ",
            "hint_en": "Dance / motion promos (beta).",
            "hint_th": "โปรโมทโมชัน / น่าเต้น (เบต้า)",
            "primary_model": "gemini-2.5-flash",
            "secondary_model": "grok-3-mini",
            "media_provider": "seedance",
            "requires": ["google", "seedance"],
            "force_unavailable": True,
            "unavailable_reason_en": "Seedance integration coming soon — preview pricing now.",
            "unavailable_reason_th": "Seedance กำลังเชื่อมต่อ — ดูราคาล่วงหน้าได้",
        },
    ]


def _tier_available(tier: dict[str, Any]) -> tuple[bool, str | None, str | None]:
    if tier.get("force_unavailable"):
        return (
            False,
            tier.get("unavailable_reason_en"),
            tier.get("unavailable_reason_th"),
        )
    for provider in tier.get("requires", []):
        if not _provider_ready(provider):
            return (
                False,
                f"Provider '{provider}' is not configured on the server yet.",
                f"เซิร์ฟเวอร์ยังไม่ได้ตั้งค่า '{provider}'",
            )
    return True, None, None


def list_garden_model_tiers() -> list[dict[str, Any]]:
    base = str(GARDEN_BASE_PRICE_USD)
    out: list[dict[str, Any]] = []
    for tier in _tier_catalog():
        available, reason_en, reason_th = _tier_available(tier)
        base_price = Decimal(tier.get("base_override_usd") or base)
        addon = Decimal(tier["addon_usd"])
        suggested = (base_price + addon).quantize(Decimal("0.01"))
        out.append(
            {
                "id": tier["id"],
                "kind": tier["kind"],
                "addon_usd": str(addon),
                "suggested_price_usd": str(suggested),
                "label_en": tier["label_en"],
                "label_th": tier["label_th"],
                "engines_en": tier["engines_en"],
                "engines_th": tier["engines_th"],
                "hint_en": tier["hint_en"],
                "hint_th": tier["hint_th"],
                "available": available,
                "unavailable_reason_en": reason_en,
                "unavailable_reason_th": reason_th,
            }
        )
    return out


def get_tier(tier_id: str) -> dict[str, Any] | None:
    for tier in _tier_catalog():
        if tier["id"] == tier_id:
            return tier
    return None


def suggested_price_usd(tier_id: str) -> str:
    tier = get_tier(tier_id) or get_tier("standard")
    assert tier is not None
    base = Decimal(tier.get("base_override_usd") or GARDEN_BASE_PRICE_USD)
    addon = Decimal(tier["addon_usd"])
    return str((base + addon).quantize(Decimal("0.01")))


def _apply_models_to_steps(
    steps: list[dict[str, Any]],
    *,
    primary: str,
    secondary: str,
) -> list[dict[str, Any]]:
    llm_indexes = [i for i, step in enumerate(steps) if step.get("type") == "llm"]
    if not llm_indexes:
        return deepcopy(steps)
    split_at = llm_indexes[len(llm_indexes) // 2]
    result: list[dict[str, Any]] = []
    for i, step in enumerate(steps):
        if step.get("type") != "llm":
            result.append(dict(step))
            continue
        model = primary if i < split_at else secondary
        result.append({**step, "model": model})
    return result


def _video_steps(media_provider: str, *, primary: str, secondary: str) -> list[dict[str, Any]]:
    return [
        {"id": "brief", "type": "llm", "model": primary, "title": "Creative Brief"},
        {"id": "script", "type": "llm", "model": primary, "title": "Script & Storyboard"},
        {
            "id": "render",
            "type": "media",
            "provider": media_provider,
            "title": f"{media_provider.upper()} Render",
        },
        {"id": "qa", "type": "llm", "model": secondary, "title": "QA Gate"},
    ]


def apply_model_tier_to_crew_config(
    crew_config: dict[str, Any],
    tier_id: str,
) -> dict[str, Any]:
    tier = get_tier(tier_id) or get_tier("standard")
    assert tier is not None
    merged = deepcopy(crew_config)
    if not merged.get("steps"):
        from app.expert_skills.custom_defaults import build_default_crew_config

        defaults = build_default_crew_config(
            category=merged.get("category"),
            name=str(merged.get("name") or "Custom flow"),
            description=str(merged.get("skill_md") or merged.get("description") or "Creator flow"),
            skill_md=merged.get("skill_md"),
            pipeline_label=merged.get("pipeline_label"),
            input_mode=merged.get("input_mode"),
            run_title=merged.get("run_title"),
        )
        merged = {**defaults, **merged}
    primary = tier["primary_model"]
    secondary = tier["secondary_model"]

    if tier.get("kind") == "video" and tier.get("media_provider"):
        steps = _video_steps(tier["media_provider"], primary=primary, secondary=secondary)
        pipeline = f"Brief → Script → {tier['media_provider'].upper()} → QA"
        merged["steps"] = steps
        merged["pipeline_label"] = pipeline
        merged["media_provider"] = tier["media_provider"]
    else:
        steps = merged.get("steps") or []
        if isinstance(steps, list) and steps:
            merged["steps"] = _apply_models_to_steps(steps, primary=primary, secondary=secondary)

    merged["model_tier_id"] = tier["id"]
    merged["model_tier_label_en"] = tier["label_en"]
    merged["model_tier_label_th"] = tier["label_th"]
    merged["engines_en"] = tier["engines_en"]
    merged["engines_th"] = tier["engines_th"]
    return merged


def garden_model_tiers() -> dict[str, Any]:
    return {"tiers": list_garden_model_tiers(), "base_price_usd": str(GARDEN_BASE_PRICE_USD)}


def _model_provider_ready(model: str) -> bool:
    return _provider_ready(resolve_provider(model))


def _tier_runtime_ready(tier: dict[str, Any]) -> bool:
    if tier.get("force_unavailable"):
        return False
    for provider in tier.get("requires", []):
        if not _provider_ready(str(provider)):
            return False
    if tier.get("kind") == "video" and tier.get("media_provider"):
        if not _provider_ready(str(tier["media_provider"])):
            return False
    return True


def _downgrade_to_standard(crew_config: dict[str, Any], requested_tier_id: str, *, reason: str) -> dict[str, Any]:
    from app.expert_skills.custom_defaults import build_default_crew_config

    base = deepcopy(crew_config)
    requested = get_tier(requested_tier_id)
    if requested and requested.get("kind") == "video":
        defaults = build_default_crew_config(
            category=base.get("category"),
            name=str(base.get("name") or "Custom flow"),
            description=str(base.get("skill_md") or base.get("description") or "Creator flow"),
            skill_md=base.get("skill_md"),
            pipeline_label=base.get("pipeline_label"),
            input_mode=base.get("input_mode"),
            run_title=base.get("run_title"),
        )
        base["steps"] = defaults["steps"]
        base["pipeline_label"] = defaults["pipeline_label"]
        base.pop("media_provider", None)

    downgraded = apply_model_tier_to_crew_config(base, STANDARD_TIER_ID)
    downgraded["runtime_tier_downgraded"] = True
    downgraded["requested_model_tier_id"] = requested_tier_id
    downgraded["effective_marketplace_price_usd"] = str(GARDEN_BASE_PRICE_USD)
    downgraded["runtime_downgrade_reason"] = reason
    downgraded["runtime_note_en"] = (
        f"Requested tier «{requested_tier_id}» is not available on the server — "
        f"running on Standard engines at base price (${GARDEN_BASE_PRICE_USD})."
    )
    downgraded["runtime_note_th"] = (
        f"ชุด «{requested_tier_id}» ยังไม่พร้อมบนเซิร์ฟเวอร์ — "
        f"รันด้วยโมเดลมาตรฐาน ราคาพื้นฐาน ${GARDEN_BASE_PRICE_USD}"
    )
    return downgraded


def resolve_runtime_crew_config(crew_config: dict[str, Any] | None) -> dict[str, Any]:
    """Pick runnable models for this run; downgrade tier + price when providers are missing."""
    merged = deepcopy(crew_config or {})
    tier_id = str(merged.get("model_tier_id") or STANDARD_TIER_ID)
    if tier_id == STANDARD_TIER_ID:
        merged["runtime_tier_downgraded"] = False
        merged["requested_model_tier_id"] = STANDARD_TIER_ID
        return merged

    requested_tier = get_tier(tier_id)
    if requested_tier is None or not _tier_runtime_ready(requested_tier):
        return _downgrade_to_standard(merged, tier_id, reason="tier_unavailable")

    steps = merged.get("steps") or []
    if isinstance(steps, list):
        for step in steps:
            if step.get("type") != "llm":
                continue
            model = step.get("model")
            if model and not _model_provider_ready(str(model)):
                return _downgrade_to_standard(
                    merged,
                    tier_id,
                    reason=f"model_unavailable:{model}",
                )

    merged["runtime_tier_downgraded"] = False
    merged["requested_model_tier_id"] = tier_id
    return merged


def runtime_tier_meta(crew_config: dict[str, Any]) -> dict[str, Any]:
    return {
        "downgraded": bool(crew_config.get("runtime_tier_downgraded")),
        "requested_tier_id": crew_config.get("requested_model_tier_id")
        or crew_config.get("model_tier_id"),
        "effective_tier_id": crew_config.get("model_tier_id"),
        "effective_price_usd": crew_config.get("effective_marketplace_price_usd"),
        "reason": crew_config.get("runtime_downgrade_reason"),
        "note_en": crew_config.get("runtime_note_en"),
        "note_th": crew_config.get("runtime_note_th"),
    }


RUNTIME_CREW_KEYS = frozenset(
    {
        "runtime_tier_downgraded",
        "requested_model_tier_id",
        "effective_marketplace_price_usd",
        "runtime_downgrade_reason",
        "runtime_note_en",
        "runtime_note_th",
    }
)


def strip_runtime_crew_fields(crew_config: dict[str, Any] | None) -> dict[str, Any]:
    base = dict(crew_config or {})
    for key in RUNTIME_CREW_KEYS:
        base.pop(key, None)
    return base


def effective_marketplace_price_usd(
    *,
    listed_price_usd: Decimal | str | float,
    crew_config: dict[str, Any] | None,
    tier_runtime: dict[str, Any] | None = None,
) -> Decimal:
    if tier_runtime and tier_runtime.get("downgraded") and tier_runtime.get("effective_price_usd"):
        return Decimal(str(tier_runtime["effective_price_usd"]))
    resolved = resolve_runtime_crew_config(crew_config or {})
    if resolved.get("runtime_tier_downgraded") and resolved.get("effective_marketplace_price_usd"):
        return Decimal(str(resolved["effective_marketplace_price_usd"]))
    return Decimal(str(listed_price_usd))