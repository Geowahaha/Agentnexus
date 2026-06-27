"""OBOLLA Attribution Charter — upstream credits per skill pack."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from app.expert_skills.pack_loader import load_skill_pack

PACKS_ROOT = Path(__file__).resolve().parent / "packs"

CHARTER_SUMMARY = (
    "OBOLLA orchestrates agent flows; upstream models, datasets, and tools keep "
    "their credit. Free tiers use your GPU or open upstream weights — we do not "
    "re-train without saying so."
)

OBOLLA_LAYER = (
    "OBOLLA adds: multi-step pipeline, QA gate, marketplace delivery, optional "
    "Local Bridge, and billing — not the upstream weights themselves."
)


def _links_for_pack(pack_slug: str) -> list[dict[str, str]]:
    registry: dict[str, list[dict[str, str]]] = {
        "fable5-coding-agent": [
            {
                "label": "hotdogs/qwen3.6-27b-fable5-lora",
                "href": "https://huggingface.co/hotdogs/qwen3.6-27b-fable5-lora",
                "detail": "Runtime LoRA adapter (all four steps via Ollama)",
            },
            {
                "label": "Glint-Research/Fable-5-traces",
                "href": "https://huggingface.co/datasets/Glint-Research/Fable-5-traces",
                "detail": "Playbook patterns — explore → plan → edit → verify",
            },
        ],
        "fable5-coding-agent-premium": [
            {
                "label": "Glint-Research/Fable-5-traces",
                "href": "https://huggingface.co/datasets/Glint-Research/Fable-5-traces",
                "detail": "Pipeline format inspired by trace corpus (cloud GPT-4.1 + Grok)",
            },
            {
                "label": "OpenAI GPT-4.1",
                "href": "https://platform.openai.com/docs/models",
                "detail": "Plan + implement steps via platform API",
            },
            {
                "label": "xAI Grok 3 Mini",
                "href": "https://docs.x.ai/",
                "detail": "Review + QA steps via platform API",
            },
        ],
        "ai-visibility-2026": [
            {
                "label": "AIBotAuth Scanner",
                "href": "https://aibotauth.com",
                "detail": "Deterministic AI crawler / visibility scan (MCP tool)",
            },
            {
                "label": "SuccessCasting proof",
                "href": "https://aibotauth.com/proof/successcasting-com-8bb891af45a6",
                "detail": "Live client proof — 88/100",
            },
            {
                "label": "Pinpoint Accounting proof",
                "href": "https://aibotauth.com/proof/pinpointaccountingservice-com-c902cb05afc4",
                "detail": "Live client proof — 88/100",
            },
        ],
        "fix-bot-ai-agent-ready": [
            {
                "label": "isitagentready.com",
                "href": "https://isitagentready.com/",
                "detail": "Agent-readiness check taxonomy (Cloudflare scanner reference)",
            },
            {
                "label": "AIBotAuth Scanner",
                "href": "https://aibotauth.com",
                "detail": "Deterministic MCP scan + public proof badge",
            },
            {
                "label": "SuccessCasting proof (88/100)",
                "href": "https://aibotauth.com/proof/successcasting-com-8bb891af45a6",
                "detail": "Live OBOLLA client — public Agent-Ready proof",
            },
            {
                "label": "Pinpoint Accounting proof (88/100)",
                "href": "https://aibotauth.com/proof/pinpointaccountingservice-com-c902cb05afc4",
                "detail": "Live OBOLLA client — Thai accounting services site",
            },
        ],
        "agent-ready-auto-fix": [
            {
                "label": "isitagentready.com",
                "href": "https://isitagentready.com/",
                "detail": "Target rubric — 100% Level 5 Agent-Native",
            },
            {
                "label": "SuccessCasting 100% reference",
                "href": "https://www.successcasting.com",
                "detail": "Production playbook: 25% → 100% all categories",
            },
            {
                "label": "AIBotAuth Scanner",
                "href": "https://aibotauth.com",
                "detail": "Deterministic MCP scan step",
            },
        ],
        "seo-expert-analysis": [
            {
                "label": "Site intelligence crawl",
                "href": "https://obolla.com",
                "detail": "On-page extraction + scanner signals (OBOLLA pipeline)",
            },
        ],
        "ai-lineart-youtube-kemlife": [
            {
                "label": "KEMLIFE — AI Video methodology",
                "href": "https://course-kemlife.lovable.app/",
                "detail": "Workflow inspiration — faceless line-art YouTube (community notes)",
            },
            {
                "label": "Higgsfield / GPT Image 2",
                "href": "https://higgsfield.ai/",
                "detail": "Optional upstream image renderer (buyer runs locally)",
            },
        ],
        "ai-lineart-facebook-reel-kemlife": [
            {
                "label": "KEMLIFE — AI Video methodology",
                "href": "https://course-kemlife.lovable.app/",
                "detail": "Workflow inspiration — faceless line-art Reels (community notes)",
            },
            {
                "label": "Reference Facebook Reel",
                "href": "https://www.facebook.com/reel/2039899173277798",
                "detail": "Vertical short-form pattern shared by buyer",
            },
            {
                "label": "Higgsfield / GPT Image 2",
                "href": "https://higgsfield.ai/",
                "detail": "Optional 9:16 image renderer (buyer runs locally)",
            },
        ],
        "image-post-creator": [
            {
                "label": "xAI Grok Imagine",
                "href": "https://docs.x.ai/developers/model-capabilities/imagine",
                "detail": "In-pipeline image generation (grok-imagine-image-quality)",
            },
            {
                "label": "Canva / Midjourney",
                "href": "https://www.canva.com/",
                "detail": "Optional re-render if buyer wants a different style",
            },
        ],
        "short-post-creator": [
            {
                "label": "X (Twitter) compose",
                "href": "https://x.com/compose/post",
                "detail": "Native publishing surface for short posts",
            },
            {
                "label": "LinkedIn / Threads / Facebook",
                "href": "https://www.linkedin.com/",
                "detail": "Platform-native compose — buyer publishes",
            },
        ],
    }
    return registry.get(pack_slug, [])


def _pricing_honesty(pack_slug: str, price_usd: float) -> str:
    if pack_slug == "fix-bot-ai-agent-ready":
        return (
            "Free $0/run — includes public AIBotAuth proof link. "
            "Live clients: successcasting.com & pinpointaccountingservice.com. "
            "Upgrade to Auto Fix Pro $9.99 for Level-5 deploy pack."
        )
    if pack_slug == "agent-ready-auto-fix":
        return (
            f"${price_usd:.2f}/run marketplace fee plus LLM via credits. "
            "Includes proof badge. Growth Monitor upsell: ฿490/mo on AIBotAuth."
        )
    if pack_slug == "ai-visibility-2026":
        return (
            f"${price_usd:.2f}/run marketplace fee plus ~$0.12 LLM. "
            "Includes Agent-Ready proof URL. Verified on 2 live OBOLLA clients."
        )
    if pack_slug == "fable5-coding-agent":
        return (
            "Free marketplace fee; $0 LLM on your GPU via Ollama. "
            "Requires hotdogs LoRA — no cloud fallback."
        )
    if pack_slug == "fable5-coding-agent-premium":
        return (
            f"${price_usd:.0f}/run marketplace fee plus cloud LLM tokens. "
            "No GPU required — not the hotdogs LoRA weights."
        )
    if price_usd <= 0:
        return "Free run fee; LLM/tools billed per platform credits where applicable."
    return f"${price_usd:.2f}/run marketplace fee plus LLM/tool usage via credits."


@lru_cache
def _credits_md(pack_slug: str) -> str | None:
    path = PACKS_ROOT / pack_slug / "references" / "credits.md"
    if path.is_file():
        return path.read_text(encoding="utf-8")
    return None


def skill_attribution(*, pack_slug: str, price_usd_per_run: float = 0.0) -> dict:
    try:
        load_skill_pack(pack_slug)
        pack_ok = True
    except FileNotFoundError:
        pack_ok = False

    return {
        "charter_summary": CHARTER_SUMMARY,
        "pack_slug": pack_slug,
        "upstream": _links_for_pack(pack_slug),
        "obolla_layer": OBOLLA_LAYER,
        "pricing_honesty": _pricing_honesty(pack_slug, price_usd_per_run),
        "credits_markdown": _credits_md(pack_slug),
        "pack_loaded": pack_ok,
    }