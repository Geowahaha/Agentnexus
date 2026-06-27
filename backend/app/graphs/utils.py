import re
import time
from datetime import datetime, timezone
from decimal import Decimal

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AIMessage, BaseMessage

from app.core.config import settings
from app.core.llm import LLMFactory, resolve_provider
from app.core.pricing import calculate_cost_usd
from app.models.state import AgentNexusState

DEFAULT_LLM_FALLBACKS = ("grok-3-mini", "claude-haiku-4-5-20251001", "gpt-4o-mini")
DEFAULT_EXPERT_SKILL_FALLBACKS = ("gemini-2.5-flash", *DEFAULT_LLM_FALLBACKS)
STEP_FAILED_MARKER = "**Step failed**"
SEO_DELIVERABLE_LLM_STEPS = frozenset({"research", "analyze", "audit", "optimize", "report"})
FABLE5_DELIVERABLE_LLM_STEPS = frozenset({"plan", "implement", "review", "qa"})
FABLE5_LOCAL_PACK = "fable5-coding-agent"
FABLE5_PREMIUM_PACK = "fable5-coding-agent-premium"
PREMIUM_FALLBACK_CHAIN = ("gpt-4.1", "gpt-4o", "grok-3-mini", "gpt-4o-mini", "gemini-2.5-flash")
MCP_STEP_IDS = frozenset({"tech_scan", "visibility_scan", "site_intel", "scan"})


def extract_content(message: AIMessage) -> str:
    content = message.content
    if isinstance(content, str):
        return content
    return str(content)


def extract_usage(message: AIMessage) -> tuple[int, int, int]:
    usage = message.usage_metadata or {}
    input_tokens = int(usage.get("input_tokens", 0))
    output_tokens = int(usage.get("output_tokens", 0))
    total_tokens = int(usage.get("total_tokens", input_tokens + output_tokens))
    return input_tokens, output_tokens, total_tokens


def accumulate_usage(
    state: AgentNexusState,
    messages: list[AIMessage],
    model: str,
) -> dict:
    total_tokens = state["total_tokens"]
    total_cost_usd = state["total_cost_usd"]
    for message in messages:
        input_tokens, output_tokens, step_tokens = extract_usage(message)
        total_tokens += step_tokens
        total_cost_usd += calculate_cost_usd(model, input_tokens, output_tokens)
    return {
        "total_tokens": total_tokens,
        "total_cost_usd": total_cost_usd,
    }


def usage_updates(state: AgentNexusState, message: AIMessage, model: str) -> dict:
    input_tokens, output_tokens, total_tokens = extract_usage(message)
    step_cost = calculate_cost_usd(model, input_tokens, output_tokens)
    return {
        "total_tokens": state["total_tokens"] + total_tokens,
        "total_cost_usd": state["total_cost_usd"] + step_cost,
    }


def media_cost_updates(state: AgentNexusState, *, cost_usd: float) -> dict:
    return {
        "total_cost_usd": state["total_cost_usd"] + cost_usd,
    }


def running_updates(state: AgentNexusState, *, current_agent: str) -> dict:
    now = datetime.now(timezone.utc)
    return {
        "status": "running",
        "current_agent": current_agent,
        "updated_at": now,
        "intermediate_results": {
            **state.get("intermediate_results", {}),
            "started_at_monotonic": state.get("intermediate_results", {}).get(
                "started_at_monotonic", time.monotonic()
            ),
        },
    }


def execution_time_seconds(state: AgentNexusState) -> float | None:
    started_at = state.get("intermediate_results", {}).get("started_at_monotonic")
    if started_at is None:
        return None
    return time.monotonic() - started_at


def failed_updates(state: AgentNexusState, error: Exception) -> dict:
    return {
        "status": "failed",
        "error_message": format_llm_error(error),
        "execution_time_seconds": execution_time_seconds(state),
        "updated_at": datetime.now(timezone.utc),
    }


def format_llm_error(error: Exception) -> str:
    message = str(error).strip()
    lowered = message.lower()
    if "permission-denied" in lowered or (
        "403" in message and ("credit" in lowered or "spending limit" in lowered)
    ):
        provider = "Anthropic" if "anthropic" in lowered or "claude" in lowered else "LLM provider"
        return (
            f"{provider} API credits exhausted or monthly spending limit reached. "
            "Top up provider credits or the pipeline will fall back to another model."
        )
    if "401" in message and ("api key" in lowered or "unauthorized" in lowered):
        return "LLM API key is missing or invalid. Check your provider keys in backend .env."
    return message


def is_recoverable_llm_error(error: Exception) -> bool:
    message = str(error).lower()
    markers = (
        "permission-denied",
        "rate limit",
        "rate_limit",
        "resource_exhausted",
        "overloaded",
        "spending limit",
        "insufficient",
        "quota",
        "429",
        "503",
        "502",
        "timeout",
        "connection",
    )
    return any(marker in message for marker in markers) or (
        "403" in str(error) and ("credit" in message or "spending" in message)
    )


def fallback_models_for(primary_model: str) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for model in (primary_model, *DEFAULT_LLM_FALLBACKS, *DEFAULT_EXPERT_SKILL_FALLBACKS):
        if model in seen:
            continue
        seen.add(model)
        ordered.append(model)
    return ordered


def models_to_try(primary_model: str, *, pack_slug: str | None = None) -> list[str]:
    if pack_slug == FABLE5_LOCAL_PACK:
        return [primary_model]
    if pack_slug == FABLE5_PREMIUM_PACK:
        seen: set[str] = set()
        ordered: list[str] = []
        for model in (primary_model, *PREMIUM_FALLBACK_CHAIN):
            if model in seen:
                continue
            seen.add(model)
            ordered.append(model)
        return ordered
    return fallback_models_for(primary_model)


def provider_configured(factory: LLMFactory, model: str) -> bool:
    provider = resolve_provider(model)
    if provider == "ollama":
        return bool(settings.ollama_enabled)
    if provider == "anthropic":
        return bool(settings.anthropic_api_key)
    if provider == "google":
        return bool(settings.google_api_key or settings.gemini_api_key)
    if provider == "xai":
        return bool(settings.xai_api_key)
    return bool(settings.openai_api_key)


async def invoke_llm_with_fallback(
    factory: LLMFactory,
    *,
    primary_model: str,
    messages: list[BaseMessage],
    pack_slug: str | None = None,
) -> tuple[AIMessage, str, list[str]]:
    warnings: list[str] = []
    last_error: Exception | None = None

    for model in models_to_try(primary_model, pack_slug=pack_slug):
        if not provider_configured(factory, model):
            warnings.append(f"Skipped fallback model '{model}' — provider API key not configured.")
            continue
        llm: BaseChatModel = factory.get(model)
        try:
            response = await llm.ainvoke(messages)
            if not isinstance(response, AIMessage):
                response = AIMessage(content=str(getattr(response, "content", response)))
            if model != primary_model:
                warnings.append(
                    f"Primary model '{primary_model}' unavailable; used fallback '{model}'."
                )
            return response, model, warnings
        except Exception as exc:
            last_error = exc
            if not is_recoverable_llm_error(exc):
                raise
            warnings.append(f"Model '{model}' failed: {format_llm_error(exc)}")

    if last_error is not None:
        raise last_error
    raise RuntimeError(f"No configured LLM provider available for '{primary_model}'.")


def append_expert_skill_warnings(intermediate: dict, warnings: list[str]) -> dict:
    if not warnings:
        return intermediate
    existing = list(intermediate.get("expert_skill_warnings", []))
    for warning in warnings:
        if warning not in existing:
            existing.append(warning)
    return {**intermediate, "expert_skill_warnings": existing}


def _pipeline_step_ids(steps_out: dict, crew_steps: list[dict] | None) -> list[str]:
    if crew_steps:
        return [
            str(step["id"])
            for step in crew_steps
            if step.get("type") in ("llm", "image_gen") and step.get("id")
        ]
    return [
        step_id
        for step_id in steps_out
        if step_id not in MCP_STEP_IDS and not str(step_id).endswith("_scan")
    ]


def _llm_step_ids(steps_out: dict, crew_steps: list[dict] | None) -> list[str]:
    return _pipeline_step_ids(steps_out, crew_steps)


def assess_expert_skill_delivery(
    state: dict,
    *,
    crew_steps: list[dict] | None = None,
) -> dict:
    intermediate = dict(state.get("intermediate_results") or {})
    steps_out = dict(intermediate.get("expert_skill_steps") or {})
    llm_step_ids = _llm_step_ids(steps_out, crew_steps)

    failed_llm = [
        step_id
        for step_id in llm_step_ids
        if STEP_FAILED_MARKER in str(steps_out.get(step_id, ""))
    ]
    successful_llm = [
        step_id
        for step_id in llm_step_ids
        if step_id in steps_out and step_id not in failed_llm
    ]
    deliverable_ids = FABLE5_DELIVERABLE_LLM_STEPS | SEO_DELIVERABLE_LLM_STEPS
    deliverable_failed = [step_id for step_id in deliverable_ids if step_id in failed_llm]

    final_output = str(state.get("final_output") or "").strip()
    has_substantial_output = len(final_output) > 500 and not final_output.startswith("## Warnings")

    if llm_step_ids and not successful_llm:
        quality = "failed"
        multiplier = Decimal("0")
    elif len(deliverable_failed) >= 2 or (failed_llm and not has_substantial_output):
        quality = "degraded"
        multiplier = Decimal("0.25") if len(successful_llm) <= 1 else Decimal("0.5")
    elif failed_llm:
        quality = "degraded"
        multiplier = Decimal("0.5")
    else:
        quality = "full"
        multiplier = Decimal("1")

    return {
        "delivery_quality": quality,
        "marketplace_fee_multiplier": float(multiplier),
        "failed_llm_steps": failed_llm,
        "successful_llm_steps": successful_llm,
    }


def hydrate_expert_skill_steps_from_final_output(state: dict) -> dict:
    """Rebuild expert_skill_steps from final_output when checkpoint blobs are missing."""
    intermediate = dict(state.get("intermediate_results") or {})
    if intermediate.get("expert_skill_steps"):
        return state

    final_output = str(state.get("final_output") or "").strip()
    if not final_output or state.get("workflow_type") != "expert_skill":
        return state

    steps: dict[str, str] = {}
    for part in re.split(r"(?m)^## ", final_output):
        part = part.strip()
        if not part or part.startswith("Warnings"):
            continue
        title, _, body = part.partition("\n")
        slug = re.sub(r"[^a-z0-9]+", "_", title.lower()).strip("_") or "section"
        steps[slug] = body.strip()

    if not steps:
        return state

    return {
        **state,
        "intermediate_results": {
            **intermediate,
            "expert_skill_steps": steps,
            "hydrated_from_final_output": True,
        },
    }