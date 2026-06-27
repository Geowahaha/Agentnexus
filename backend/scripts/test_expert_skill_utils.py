"""Unit tests for expert skill LLM fallback helpers."""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from langchain_core.messages import AIMessage, HumanMessage

from app.graphs.utils import (
    FABLE5_LOCAL_PACK,
    FABLE5_PREMIUM_PACK,
    assess_expert_skill_delivery,
    fallback_models_for,
    format_llm_error,
    hydrate_expert_skill_steps_from_final_output,
    invoke_llm_with_fallback,
    is_recoverable_llm_error,
    models_to_try,
)


class FakeFactory:
    def __init__(self, behaviors: dict[str, Exception | str]) -> None:
        self._behaviors = behaviors

    def get(self, model: str):
        behavior = self._behaviors.get(model)

        class FakeLLM:
            async def ainvoke(self, messages):
                if isinstance(behavior, Exception):
                    raise behavior
                return AIMessage(content=behavior or f"ok:{model}")

        return FakeLLM()


def test_fallback_models_include_primary_first() -> None:
    models = fallback_models_for("claude-sonnet-4-5-20250929")
    assert models[0] == "claude-sonnet-4-5-20250929"
    assert "gemini-2.5-flash" in models


def test_models_to_try_local_strict() -> None:
    models = models_to_try("qwen3.6-27b-fable5", pack_slug=FABLE5_LOCAL_PACK)
    assert models == ["qwen3.6-27b-fable5"]


def test_models_to_try_premium_chain() -> None:
    models = models_to_try("gpt-4.1", pack_slug=FABLE5_PREMIUM_PACK)
    assert models[0] == "gpt-4.1"
    assert "grok-3-mini" in models


def test_format_llm_error_anthropic_credits() -> None:
    err = Exception(
        "Error code: 403 - {'code': 'permission-denied', "
        "'error': 'Your team has reached its monthly spending limit.'}"
    )
    formatted = format_llm_error(err)
    assert "credits exhausted" in formatted.lower() or "spending limit" in formatted.lower()


def test_is_recoverable_llm_error() -> None:
    assert is_recoverable_llm_error(Exception("Error code: 403 permission-denied credits"))
    assert not is_recoverable_llm_error(Exception("invalid JSON in request body"))


async def test_invoke_llm_with_fallback_uses_secondary(monkeypatch=None) -> None:
    import app.graphs.utils as utils

    utils.provider_configured = lambda _factory, _model: True  # type: ignore[assignment]

    factory = FakeFactory(
        {
            "claude-sonnet-4-5-20250929": Exception(
                "Error code: 403 - permission-denied spending limit"
            ),
            "gemini-2.5-flash": "audit complete",
        }
    )
    response, model_used, warnings = await invoke_llm_with_fallback(
        factory,  # type: ignore[arg-type]
        primary_model="claude-sonnet-4-5-20250929",
        messages=[HumanMessage(content="audit")],
    )
    assert model_used == "gemini-2.5-flash"
    assert response.content == "audit complete"
    assert any("fallback" in w.lower() for w in warnings)


def test_assess_expert_skill_delivery_failed() -> None:
    state = {
        "workflow_type": "expert_skill",
        "final_output": "## Warnings\n- all models down",
        "intermediate_results": {
            "expert_skill_steps": {
                "research": "**Step failed**\ncredits",
                "report": "**Step failed**\ncredits",
            }
        },
    }
    crew = [{"id": "research", "type": "llm"}, {"id": "report", "type": "llm"}]
    result = assess_expert_skill_delivery(state, crew_steps=crew)
    assert result["delivery_quality"] == "failed"
    assert result["marketplace_fee_multiplier"] == 0.0


def test_assess_expert_skill_delivery_degraded() -> None:
    state = {
        "workflow_type": "expert_skill",
        "final_output": "## Researcher Agent\n" + ("insight " * 200),
        "intermediate_results": {
            "expert_skill_steps": {
                "research": "good research",
                "report": "**Step failed**\ncredits",
            }
        },
    }
    crew = [{"id": "research", "type": "llm"}, {"id": "report", "type": "llm"}]
    result = assess_expert_skill_delivery(state, crew_steps=crew)
    assert result["delivery_quality"] == "degraded"
    assert result["marketplace_fee_multiplier"] == 0.5


def test_hydrate_expert_skill_steps_from_final_output() -> None:
    state = {
        "workflow_type": "expert_skill",
        "final_output": "## Technical Scan\nscan data\n\n## Report Generator\nreport body",
        "intermediate_results": {},
    }
    hydrated = hydrate_expert_skill_steps_from_final_output(state)
    steps = hydrated["intermediate_results"]["expert_skill_steps"]
    assert "technical_scan" in steps
    assert "report_generator" in steps
    assert steps["report_generator"] == "report body"


def main() -> None:
    test_fallback_models_include_primary_first()
    test_models_to_try_local_strict()
    test_models_to_try_premium_chain()
    test_format_llm_error_anthropic_credits()
    test_is_recoverable_llm_error()
    asyncio.run(test_invoke_llm_with_fallback_uses_secondary())
    test_assess_expert_skill_delivery_failed()
    test_assess_expert_skill_delivery_degraded()
    test_hydrate_expert_skill_steps_from_final_output()
    print("test_expert_skill_utils: OK")


if __name__ == "__main__":
    try:
        main()
    except AssertionError as exc:
        print(f"FAILED: {exc}", file=sys.stderr)
        sys.exit(1)