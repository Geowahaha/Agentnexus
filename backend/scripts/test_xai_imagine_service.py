"""Unit tests for xAI Imagine prompt extraction."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.pricing import calculate_image_cost_usd
from app.services.xai_imagine_service import extract_image_prompt_from_step_output

SAMPLE_OUTPUT = """## Image Prompt (4:5)
**Full image prompt:**

Clean minimalist aesthetic flat-lay photography, 4:5 portrait, scene: a simple off-white paper "Dopamine Menu" laid flat on a warm neutral beige linen background, four small curated items arranged neatly like menu sections — a ceramic cup of coffee, wireless earbuds, a small potted monstera plant, and a pair of clean white walking shoes — soft natural window light from the side, gentle shadows, warm neutral color palette with soft beige, cream, and muted green tones, highly detailed, crisp focus, modern lifestyle aesthetic, no text overlay, no watermark, no logo

**Text-on-image overlay:** None (visual relies on the physical menu paper and objects; all messaging lives in the caption)
"""


def test_extract_dopamine_menu_prompt() -> None:
    prompt, aspect = extract_image_prompt_from_step_output(SAMPLE_OUTPUT)
    assert "Dopamine Menu" in prompt
    assert "flat-lay" in prompt.lower() or "flat lay" in prompt.lower()
    assert aspect == "3:4"


def test_image_pricing() -> None:
    assert calculate_image_cost_usd("grok-imagine-image-quality") == 0.05


def main() -> None:
    test_extract_dopamine_menu_prompt()
    test_image_pricing()
    print("test_xai_imagine_service: OK")


if __name__ == "__main__":
    main()