"""Unit tests for expert skill prompt routing."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.graphs.expert_skill_prompts import build_llm_prompt, extract_task_keywords


def test_extract_task_keywords() -> None:
    assert extract_task_keywords("https://x.com keywords: casting iron, foundry") == "casting iron, foundry"
    assert extract_task_keywords("https://x.com") is None


def test_seo_research_prompt() -> None:
    role, task = build_llm_prompt(
        pack_slug="seo-expert-analysis",
        step_id="research",
        skill_context="# SEO playbook",
        target_url="https://example.com",
        task_description="https://example.com",
        step_outputs={"tech_scan": "ok"},
        prior="",
    )
    assert "Researcher Agent" in role
    assert "competitors" in task.lower()
    assert "example.com" in task


def test_fable5_local_plan_prompt() -> None:
    role, task = build_llm_prompt(
        pack_slug="fable5-coding-agent",
        step_id="plan",
        skill_context="# Fable-5 playbook",
        target_url=None,
        task_description="Add health endpoint to FastAPI",
        step_outputs={},
        prior="",
    )
    assert "Planner Agent" in role
    assert "fable5" in role.lower() or "LoRA" in role
    assert "Exploration" in task
    assert "health" in task.lower()


def test_fable5_premium_plan_prompt() -> None:
    role, task = build_llm_prompt(
        pack_slug="fable5-coding-agent-premium",
        step_id="plan",
        skill_context="# Fable-5 Pro",
        target_url=None,
        task_description="Add health endpoint to FastAPI",
        step_outputs={},
        prior="",
    )
    assert "GPT-4.1" in role
    assert "Test strategy" in task


def test_fable5_premium_implement_prompt() -> None:
    role, task = build_llm_prompt(
        pack_slug="fable5-coding-agent-premium",
        step_id="implement",
        skill_context="# Fable-5 Pro",
        target_url=None,
        task_description="Add health endpoint to FastAPI",
        step_outputs={"plan": "1. Add route\n2. Add test"},
        prior="",
    )
    assert "GPT-4.1" in role
    assert "tests" in task.lower()


def test_fable5_implement_prompt() -> None:
    role, task = build_llm_prompt(
        pack_slug="fable5-coding-agent",
        step_id="implement",
        skill_context="# Fable-5 playbook",
        target_url=None,
        task_description="Add health endpoint to FastAPI",
        step_outputs={"plan": "1. Add route\n2. Add test"},
        prior="",
    )
    assert "Implementer Agent" in role
    assert "Approved plan" in task
    assert "Bash commands" in task


def test_fable5_premium_review_prompt() -> None:
    role, task = build_llm_prompt(
        pack_slug="fable5-coding-agent-premium",
        step_id="review",
        skill_context="# Fable-5 Pro",
        target_url=None,
        task_description="Add health endpoint to FastAPI",
        step_outputs={},
        prior="plan + code output",
    )
    assert "Grok" in role
    assert "P0/P1/P2" in task


def test_fable5_qa_prompt() -> None:
    role, task = build_llm_prompt(
        pack_slug="fable5-coding-agent-premium",
        step_id="qa",
        skill_context="# Fable-5 Pro",
        target_url=None,
        task_description="Add health endpoint to FastAPI",
        step_outputs={},
        prior="plan + implement + review output",
    )
    assert "QA Gate" in role
    assert "Grok" in role
    assert "READY or NEEDS_CORRECTION" in task


def test_kemlife_topic_research_not_qa() -> None:
    role, task = build_llm_prompt(
        pack_slug="ai-lineart-youtube-kemlife",
        step_id="topic_research",
        skill_context="# KEMLIFE YouTube kit",
        target_url=None,
        task_description="[OBOLLA_PRESETS]\nหัวข้อ: ความลับของร่างกาย\n[/OBOLLA_PRESETS]",
        step_outputs={},
        prior="",
    )
    assert "Topic" in role or "Hook" in role
    assert "QA" not in role
    assert "3–5" in task or "3-5" in task
    assert "missing" not in task.lower()


def test_kemlife_script_uses_prior_hooks() -> None:
    role, task = build_llm_prompt(
        pack_slug="ai-lineart-youtube-kemlife",
        step_id="script",
        skill_context="# KEMLIFE YouTube kit",
        target_url=None,
        task_description="ทำคลิปเรื่องลืมความฝัน",
        step_outputs={"topic_research": "## Angle 1\nทำไมลืมความฝัน"},
        prior="### topic_research\n## Angle 1",
    )
    assert "Script" in role
    assert "timestamp" in task.lower()
    assert "Angle 1" in task or "topic_research" in task


def test_custom_content_research_not_qa() -> None:
    role, task = build_llm_prompt(
        pack_slug="custom",
        step_id="research",
        skill_context="# Custom blog pipeline",
        target_url=None,
        task_description="Draft blog for coffee shops",
        step_outputs={},
        prior="",
    )
    assert "Research" in role or "Intake" in role
    assert "QA this expert skill run" not in task


def test_image_post_thai_story_caption_mode() -> None:
    role, task = build_llm_prompt(
        pack_slug="image-post-creator",
        step_id="caption_draft",
        skill_context="# Image Post + thai-copy-style.md",
        target_url=None,
        task_description="ข่าวอัปเดตวงการ AI เทรนด์โลกตอนนี้ โพสต์ IG ภาษาไทย",
        step_outputs={"angle_research": "## Angle 1\nDopamine menu trend"},
        prior="",
    )
    assert "story" in task.lower() or "เรื่องเล่า" in task
    assert "human" in role.lower() or "translated" in role.lower() or "Thai" in role
    assert "NEEDS_CORRECTION" not in task


def test_image_post_angle_research_not_qa() -> None:
    role, task = build_llm_prompt(
        pack_slug="image-post-creator",
        step_id="angle_research",
        skill_context="# Image Post Creator",
        target_url=None,
        task_description="โพสต์ IG เรื่อง 5 นาทีตอนเช้า",
        step_outputs={},
        prior="",
    )
    assert "Angle" in role or "Hook" in role
    assert "QA this expert skill run" not in task
    assert "3–5" in task or "3-5" in task


def test_short_post_draft_variants() -> None:
    role, task = build_llm_prompt(
        pack_slug="short-post-creator",
        step_id="draft",
        skill_context="# Short Post Creator",
        target_url=None,
        task_description="Hot take multitasking สำหรับ X",
        step_outputs={"research": "## Platform: X\n280 chars"},
        prior="",
    )
    assert "Draft" in role or "Variants" in role
    assert "Variant" in task or "variant" in task
    assert "character" in task.lower()


def test_ai_visibility_analyze_prompt() -> None:
    role, task = build_llm_prompt(
        pack_slug="ai-visibility-2026",
        step_id="analyze",
        skill_context="# AI visibility",
        target_url="https://example.com",
        task_description="https://example.com",
        step_outputs={"scan": "score 85"},
        prior="",
    )
    assert "paid AI Visibility" in role
    assert "Scorecard" in task


def test_fix_bot_ai_free_analyze_prompt() -> None:
    role, task = build_llm_prompt(
        pack_slug="fix-bot-ai-agent-ready",
        step_id="analyze",
        skill_context="# Fix Bot AI",
        target_url="https://successcasting.com",
        task_description="https://successcasting.com",
        step_outputs={"scan": "agents.txt 404"},
        prior="",
    )
    assert "Fix Bot AI" in role
    assert "isitagentready" in task


def main() -> None:
    test_extract_task_keywords()
    test_seo_research_prompt()
    test_fable5_local_plan_prompt()
    test_fable5_premium_plan_prompt()
    test_fable5_implement_prompt()
    test_fable5_premium_implement_prompt()
    test_fable5_premium_review_prompt()
    test_fable5_qa_prompt()
    test_kemlife_topic_research_not_qa()
    test_kemlife_script_uses_prior_hooks()
    test_custom_content_research_not_qa()
    test_image_post_thai_story_caption_mode()
    test_image_post_angle_research_not_qa()
    test_short_post_draft_variants()
    test_ai_visibility_analyze_prompt()
    test_fix_bot_ai_free_analyze_prompt()
    print("test_expert_skill_prompts: OK")


if __name__ == "__main__":
    main()