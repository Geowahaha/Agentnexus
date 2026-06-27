---
name: image-post-creator
description: Social image post creator — angle research → caption + CTA → image prompt → Grok Imagine generation → publish QA. Facebook, Instagram, LinkedIn static posts.
---

# Image Post Creator

Help buyers ship **static social image posts** with scroll-stopping visuals and copy-paste-ready captions.

## Who this is for

- Creators posting on **Facebook, Instagram, LinkedIn** (image + caption)
- Thai or English — match buyer language in every deliverable
- Buyers who want **generated images inside OBOLLA** (Grok Imagine via xAI API)

## Pipeline (4 LLM + 1 image_gen)

| Step | Output |
|------|--------|
| Angle Research | 3–5 post angles with hook, audience fit, visual concept |
| Caption Draft | Primary caption + CTA + alt text + hashtag set |
| Image Prompt | Full image prompt(s) — 1:1 or 4:5, style block + scene |
| **Generate Image** | **Real image URL** from `grok-imagine-image-quality` (~$0.05/image) |
| Publish QA | Platform checklist + image URL check, READY verdict |

Details: `references/workflow-steps.md`, `references/image-prompt-template.md`, `references/platform-formats.md`

## Buyer input (task mode)

Ask for (or infer):

1. **Topic / product** — e.g. ข่าวอัปเดต AI, เทรนด์โลก, lifestyle insight
2. **Platform** — Instagram, Facebook, LinkedIn (default: Instagram 4:5)
3. **Copy mode** — default for Thai: **เรื่องเล่า 1 ตอน** (micro-story tied to image). Use classic caption only if buyer asks.
4. **Language** — Thai must sound **human** (see `references/thai-copy-style.md`) — never stiff translated Thai
5. **Optional** — brand colors, avoid list, reference style

## Thai copy (critical)

For Thai runs, write like a Thai creator covering **AI news / global trends** in one episode — conversational, image-grounded, not ad copy. Full rules: `references/thai-copy-style.md`

## Image prompt rules

- One hero image by default; carousel (2–5 slides) only if buyer asks
- Include aspect ratio in every prompt (`1:1` feed or `4:5` portrait)
- Describe text-on-image separately from background scene when needed
- No placeholders — full prompt ready for any image model

## Image generation (OBOLLA)

- **Grok Imagine** (`grok-imagine-image-quality`) via xAI API — billed ~$0.05/image + wallet credits
- Temporary URL — buyer should download promptly for scheduling

## External tools (buyer runs — optional)

- **Re-render:** Canva, Midjourney if buyer wants a different style
- **Schedule:** Meta Business Suite, Buffer, Later

## Marketplace deliverables

See `references/marketplace-deliverables.md`. End QA with **READY** or **NEEDS_CORRECTION**.