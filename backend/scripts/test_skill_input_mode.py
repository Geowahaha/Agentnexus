"""Task-mode content flows must not require URLs."""

from app.expert_skills.input_mode import skill_requires_url


def test_content_custom_no_url() -> None:
    assert not skill_requires_url(
        pack_slug="custom",
        crew_config={
            "input_mode": "task",
            "steps": [
                {"id": "research", "type": "llm", "model": "gemini-2.5-flash", "title": "Research"},
            ],
        },
        category="content",
        slug="ai-lineart-youtube-kemlife",
    )


def test_seo_custom_requires_url() -> None:
    assert skill_requires_url(
        pack_slug="custom",
        crew_config={"input_mode": "url", "steps": [{"id": "scan", "type": "mcp", "tool": "mcp.aibotauth.scan"}]},
        category="seo",
        slug="my-seo-flow",
    )


if __name__ == "__main__":
    test_content_custom_no_url()
    test_seo_custom_requires_url()
    print("skill input mode tests passed")