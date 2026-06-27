"""Runtime model tier resolution — unavailable premium falls back to standard price."""

from app.expert_skills.custom_defaults import build_default_crew_config
from app.expert_skills.model_tiers import (
    apply_model_tier_to_crew_config,
    effective_marketplace_price_usd,
    resolve_runtime_crew_config,
)


def test_downgrade_unavailable_openai_tier() -> None:
    base = build_default_crew_config(
        category="content",
        name="Content Creators",
        description="Research → draft → edit → publish checklist for a recurring task.",
    )
    tiered = apply_model_tier_to_crew_config(base, "gpt-5")
    resolved = resolve_runtime_crew_config(tiered)
    assert resolved.get("runtime_tier_downgraded") is True
    assert resolved.get("model_tier_id") == "standard"
    steps = resolved.get("steps") or []
    models = [s.get("model") for s in steps if s.get("type") == "llm"]
    assert "gemini-2.5-flash" in models
    assert "grok-3-mini" in models
    assert "gpt-5" not in models
    price = effective_marketplace_price_usd(listed_price_usd="4.49", crew_config=tiered)
    assert str(price) == "0.99"


def test_keep_tier_when_providers_ready(monkeypatch=None) -> None:
    base = build_default_crew_config(category="content", name="Test", description="Desc")
    tiered = apply_model_tier_to_crew_config(base, "sonnet-4.6")

    import app.expert_skills.model_tiers as mt

    original = mt._tier_runtime_ready

    def _always_ready(tier: dict) -> bool:
        return True

    def _model_ready(_model: str) -> bool:
        return True

    mt._tier_runtime_ready = _always_ready
    mt._model_provider_ready = _model_ready
    try:
        resolved = resolve_runtime_crew_config(tiered)
        assert resolved.get("runtime_tier_downgraded") is False
        models = [s.get("model") for s in resolved.get("steps") or [] if s.get("type") == "llm"]
        assert "claude-sonnet-4-6" in models
    finally:
        mt._tier_runtime_ready = original


if __name__ == "__main__":
    test_downgrade_unavailable_openai_tier()
    test_keep_tier_when_providers_ready()
    print("model tier runtime tests passed")