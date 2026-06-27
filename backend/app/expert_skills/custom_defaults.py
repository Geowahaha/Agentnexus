"""Default crew_config for creator-owned custom agent flows (garden, not site-audit)."""

from __future__ import annotations

CONTENT_STEPS = [
    {"id": "research", "type": "llm", "model": "gemini-2.5-flash", "title": "Research"},
    {"id": "draft", "type": "llm", "model": "gemini-2.5-flash", "title": "Draft"},
    {"id": "edit", "type": "llm", "model": "grok-3-mini", "title": "Edit & Polish"},
    {"id": "qa", "type": "llm", "model": "grok-3-mini", "title": "QA Gate"},
]

CODING_STEPS = [
    {"id": "plan", "type": "llm", "model": "gemini-2.5-flash", "title": "Planner"},
    {"id": "implement", "type": "llm", "model": "gemini-2.5-flash", "title": "Implementer"},
    {"id": "review", "type": "llm", "model": "grok-3-mini", "title": "Code Review"},
    {"id": "qa", "type": "llm", "model": "grok-3-mini", "title": "QA Gate"},
]

RESEARCH_STEPS = [
    {"id": "gather", "type": "llm", "model": "gemini-2.5-flash", "title": "Gather"},
    {"id": "analyze", "type": "llm", "model": "gemini-2.5-flash", "title": "Analyze"},
    {"id": "synthesize", "type": "llm", "model": "grok-3-mini", "title": "Synthesize"},
    {"id": "qa", "type": "llm", "model": "grok-3-mini", "title": "QA Report"},
]

GENERIC_TASK_STEPS = [
    {"id": "intake", "type": "llm", "model": "gemini-2.5-flash", "title": "Intake"},
    {"id": "work", "type": "llm", "model": "gemini-2.5-flash", "title": "Work"},
    {"id": "review", "type": "llm", "model": "grok-3-mini", "title": "Review"},
    {"id": "deliver", "type": "llm", "model": "grok-3-mini", "title": "Deliver"},
]

SEO_STEPS = [
    {"id": "scan", "type": "mcp", "tool": "mcp.aibotauth.scan", "title": "AIBotAuth Scan"},
    {"id": "analyze", "type": "llm", "model": "claude-sonnet-4-5-20250929", "title": "Auditor"},
    {"id": "improve", "type": "llm", "model": "gemini-2.5-flash", "title": "Fix Pack Generator"},
    {"id": "qa", "type": "llm", "model": "grok-3-mini", "title": "QA Challenger"},
]

CATEGORY_META: dict[str, dict] = {
    "content": {
        "input_mode": "task",
        "pipeline_label": "Research → Draft → Edit → Publish",
        "run_title": "Run Content Pipeline",
        "steps": CONTENT_STEPS,
    },
    "coding": {
        "input_mode": "task",
        "pipeline_label": "Plan → Implement → Review → QA",
        "run_title": "Run Agent Flow",
        "steps": CODING_STEPS,
    },
    "research": {
        "input_mode": "task",
        "pipeline_label": "Gather → Analyze → Synthesize → Report",
        "run_title": "Run Research Flow",
        "steps": RESEARCH_STEPS,
    },
    "quality": {
        "input_mode": "task",
        "pipeline_label": "Checklist → Run → Review → Verdict",
        "run_title": "Run Quality Flow",
        "steps": GENERIC_TASK_STEPS,
    },
    "support": {
        "input_mode": "task",
        "pipeline_label": "Ingest → Classify → Reply → Review",
        "run_title": "Run Support Flow",
        "steps": GENERIC_TASK_STEPS,
    },
    "seo": {
        "input_mode": "url",
        "pipeline_label": "Scan → Audit → Fix Pack → QA",
        "run_title": "Run Visibility Audit",
        "steps": SEO_STEPS,
    },
}

DEFAULT_META = {
    "input_mode": "task",
    "pipeline_label": "Intake → Work → Review → Deliver",
    "run_title": "Run Agent Flow",
    "steps": GENERIC_TASK_STEPS,
}


def build_skill_md(*, name: str, description: str, category: str | None, pipeline_label: str) -> str:
    cat = category or "general"
    return (
        f"# {name}\n\n"
        f"## Purpose\n{description}\n\n"
        f"## Pipeline\n{pipeline_label}\n\n"
        f"## Category\n{cat}\n\n"
        f"## Buyer input\n"
        f"Describe the task in plain language — what to research, draft, edit, or deliver.\n\n"
        f"## Deliverables\n"
        f"- Structured output per pipeline step\n"
        f"- QA-verified before marketplace delivery\n"
    )


def build_default_crew_config(
    *,
    category: str | None,
    name: str,
    description: str,
    skill_md: str | None = None,
    pipeline_label: str | None = None,
    input_mode: str | None = None,
    run_title: str | None = None,
    steps: list[dict] | None = None,
) -> dict:
    meta = CATEGORY_META.get(category or "", DEFAULT_META)
    pipeline = pipeline_label or meta["pipeline_label"]
    mode = input_mode or meta["input_mode"]
    title = run_title or meta["run_title"]
    md = skill_md or build_skill_md(
        name=name,
        description=description,
        category=category,
        pipeline_label=pipeline,
    )
    return {
        "category": category,
        "input_mode": mode,
        "pipeline_label": pipeline,
        "run_title": title,
        "skill_md": md,
        "steps": list(steps) if steps else list(meta["steps"]),
    }


def resolve_crew_config(
    pack_slug: str,
    crew_config: dict | None,
    *,
    category: str | None = None,
    name: str = "",
    description: str = "",
) -> dict:
    base = dict(crew_config or {})
    if pack_slug != "custom":
        return base
    if base.get("steps"):
        from app.expert_skills.model_tiers import resolve_runtime_crew_config

        return resolve_runtime_crew_config(base)
    defaults = build_default_crew_config(
        category=base.get("category") or category,
        name=name or "Custom flow",
        description=description or base.get("skill_md") or "",
        skill_md=base.get("skill_md"),
        pipeline_label=base.get("pipeline_label"),
        input_mode=base.get("input_mode"),
        run_title=base.get("run_title"),
    )
    merged = {**defaults, **base}
    if not merged.get("skill_md"):
        merged["skill_md"] = defaults["skill_md"]
    if not merged.get("steps"):
        merged["steps"] = defaults["steps"]
    from app.expert_skills.model_tiers import resolve_runtime_crew_config

    return resolve_runtime_crew_config(merged)


def skill_context_text(pack_slug: str, crew_config: dict) -> str:
    inline = crew_config.get("skill_md")
    if isinstance(inline, str) and inline.strip():
        text = inline.strip()
        return text[:11997] + "..." if len(text) > 12000 else text
    from app.expert_skills.pack_loader import reference_summary

    try:
        return reference_summary(pack_slug)
    except FileNotFoundError:
        return str(crew_config.get("description") or "Creator agent flow playbook.")