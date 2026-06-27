"""Whether an expert skill run expects a URL or plain-language task."""

from __future__ import annotations

from app.expert_skills.custom_defaults import resolve_crew_config

TASK_ONLY_SLUGS = frozenset(
    {
        "fable5-coding-agent",
        "fable5-coding-agent-premium",
        "content-pipeline-for-creators",
        "ai-lineart-youtube-kemlife",
        "ai-lineart-facebook-reel-kemlife",
    }
)

TASK_CATEGORIES = frozenset({"content", "coding", "research", "quality", "support"})


def skill_requires_url(
    *,
    pack_slug: str,
    crew_config: dict | None,
    category: str | None = None,
    slug: str = "",
    name: str = "",
    description: str = "",
) -> bool:
    if slug in TASK_ONLY_SLUGS:
        return False

    resolved = resolve_crew_config(
        pack_slug,
        crew_config,
        category=category,
        name=name,
        description=description,
    )
    mode = resolved.get("input_mode")
    if mode == "task":
        return False
    if mode == "url":
        return True

    steps = resolved.get("steps") or []
    if any(step.get("type") == "mcp" for step in steps):
        return True

    if pack_slug == "custom":
        return category == "seo"

    return category == "seo" or pack_slug in {
        "seo-expert-analysis",
        "ai-visibility-audit",
        "fix-bot-ai-agent-ready",
        "agent-ready-auto-fix",
    }