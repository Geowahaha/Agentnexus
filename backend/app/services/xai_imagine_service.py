"""xAI Grok Imagine image generation for expert skill pipelines."""

from __future__ import annotations

import re

import httpx

from app.core.config import settings
from app.core.pricing import calculate_image_cost_usd

XAI_IMAGES_URL = "https://api.x.ai/v1/images/generations"
DEFAULT_IMAGE_MODEL = "grok-imagine-image-quality"

_ASPECT_IN_PROMPT = re.compile(
    r"\b(\d{1,2}:\d{1,2})\s*(?:portrait|horizontal|vertical)?",
    re.IGNORECASE,
)
_FULL_PROMPT_BLOCK = re.compile(
    r"\*\*Full image prompt:\*\*\s*\n+(.+?)(?:\n\*\*|\n## |\Z)",
    re.IGNORECASE | re.DOTALL,
)
_SCENE_LINE = re.compile(r"^scene:\s*(.+)$", re.IGNORECASE | re.MULTILINE)

_SUPPORTED_ASPECTS = frozenset(
    {
        "1:1",
        "16:9",
        "9:16",
        "4:3",
        "3:4",
        "3:2",
        "2:3",
        "2:1",
        "1:2",
        "19.5:9",
        "9:19.5",
        "20:9",
        "9:20",
        "auto",
    }
)


class XaiImagineError(RuntimeError):
    pass


def extract_image_prompt_from_step_output(text: str) -> tuple[str, str | None]:
    """Parse LLM image_prompt step output into (prompt, aspect_ratio)."""
    cleaned = text.strip()
    if not cleaned:
        raise XaiImagineError("Image prompt step produced empty output.")

    match = _FULL_PROMPT_BLOCK.search(cleaned)
    if match:
        prompt = match.group(1).strip()
    else:
        lines = [line.strip() for line in cleaned.splitlines() if line.strip()]
        prompt_lines: list[str] = []
        for line in lines:
            lowered = line.lower()
            if lowered.startswith("## ") or lowered.startswith("**text-on-image"):
                break
            if lowered.startswith("|") or lowered.startswith("---"):
                continue
            prompt_lines.append(line)
        prompt = " ".join(prompt_lines).strip() if prompt_lines else cleaned

    prompt = re.sub(r"\s+", " ", prompt).strip()
    if len(prompt) < 20:
        raise XaiImagineError("Could not extract a usable image prompt from the prior step.")

    aspect: str | None = None
    for candidate in _ASPECT_IN_PROMPT.findall(prompt):
        normalized = candidate.strip()
        if normalized == "4:5":
            aspect = "3:4"
        elif normalized in _SUPPORTED_ASPECTS:
            aspect = normalized
        elif normalized not in _SUPPORTED_ASPECTS and aspect is None:
            aspect = "auto"
    return prompt, aspect


async def generate_image(
    *,
    prompt: str,
    model: str = DEFAULT_IMAGE_MODEL,
    aspect_ratio: str | None = None,
) -> dict[str, str | float]:
    if not settings.xai_api_key:
        raise XaiImagineError(
            "XAI_API_KEY is required for image generation. Set it in backend .env."
        )

    payload: dict[str, str | int] = {
        "model": model,
        "prompt": prompt,
    }
    if aspect_ratio and aspect_ratio in _SUPPORTED_ASPECTS:
        payload["aspect_ratio"] = aspect_ratio

    async with httpx.AsyncClient(timeout=120.0) as client:
        response = await client.post(
            XAI_IMAGES_URL,
            headers={
                "Authorization": f"Bearer {settings.xai_api_key}",
                "Content-Type": "application/json",
            },
            json=payload,
        )

    if response.status_code >= 400:
        detail = response.text[:500]
        raise XaiImagineError(
            f"xAI image generation failed (HTTP {response.status_code}): {detail}"
        )

    data = response.json()
    items = data.get("data") or []
    if not items:
        raise XaiImagineError("xAI image generation returned no images.")

    first = items[0]
    url = first.get("url")
    if not url:
        raise XaiImagineError("xAI image generation returned no image URL.")

    return {
        "url": str(url),
        "model": str(data.get("model") or model),
        "cost_usd": calculate_image_cost_usd(model),
    }