---
name: ai-lineart-youtube-kemlife
description: Faceless YouTube channel kit — MS Paint-style line-art cartoons with AI. Topic research → timestamped script → per-shot image prompts (16:9) → edit/publish QA. Inspired by KEMLIFE notes (Danny Why / Zenn-style workflow).
---

# AI Line-Art YouTube Channel Kit (KEMLIFE-style)

Help buyers run a **faceless YouTube channel** with deliberately **homemade MS Paint line-art** visuals — not polished illustration. The charm is rough stick-figure energy that makes people laugh and share.

**Inspiration:** Community notes from KEMLIFE (summarizing a Danny Why–style workflow). OBOLLA orchestrates the writing and prompt pipeline; image renderers (Higgsfield, GPT Image, etc.) and editors (CapCut, DaVinci) stay upstream tools the buyer runs locally.

## Who this is for

- Creators who want **history / psychology / curiosity** faceless videos (8–13 min)
- Thai or English channels — match the buyer's language in every deliverable
- Buyers who will **not** appear on camera

## Core rule (non-negotiable)

> **Do not make art pretty.** Thick uneven black lines, white background, round stick heads, wobbly bodies. If it looks professional, it failed.

## Pipeline (4 LLM steps)

| Step | Output |
|------|--------|
| Topic & Hook Research | 3–5 video angles with title hooks, why-it-clicks, competitor pattern (Zenn-style curiosity) |
| Script + Timestamps | Full voiceover script with dense timestamps (`0:00`, `0:03`, `0:07`…) — **one timestamp = one image** |
| Shot Prompts | Per-timestamp image prompts, 16:9, MS Paint style block + scene description |
| Edit & Publish QA | Filename map, CapCut/DaVinci assembly notes, title/thumbnail hooks, READY checklist |

Details: `references/workflow-steps.md`, `references/image-prompt-template.md`, `references/publish-checklist.md`

## Buyer input (task mode)

Buyers may pick **topic** and **edit style** presets in the marketplace UI (see `references/preset-catalog.md`). Task text may include:

```
[OBOLLA_PRESETS]
หัวข้อ: …
สไตล์ตัดต่อ: …
ภาษาบท: …
[/OBOLLA_PRESETS]
```

Ask for (or infer from presets + notes):

1. **Topic** — body secrets, psychology, history WTF, life hacks that backfire, or custom
2. **Edit style** — dense cuts, chapter beats, meme hold, slow-burn (YouTube)
3. **Language** — Thai or English voiceover
4. **Target length** — default 8–13 minutes
5. **Optional** — reference channel or sub-topic angle

## Image prompt style block (prepend to every shot)

```
MS Paint beginner drawing style, white background, thick uneven black outlines,
stick-figure people with round heads, intentionally ugly and charming,
no shading, no gradients, no professional illustration, 16:9 horizontal,
scene: [WHAT THE NARRATOR SAYS AT THIS TIMESTAMP]
```

See `references/image-prompt-template.md` for batch tables and Higgsfield/CLI examples.

## External tools (buyer runs — not OBOLLA)

- **Script:** Notion, ChatGPT, or this agent flow
- **Transcribe timestamps:** TurboScribe (optional)
- **Image batch:** Claude Code + Higgsfield (`gpt_image_2`, `--aspect_ratio 16:9`) or any 16:9 image model
- **Voice:** ElevenLabs TTS or self-recorded
- **Edit:** CapCut or DaVinci Resolve

## Marketplace deliverables

See `references/marketplace-deliverables.md`. End QA with **READY** or **NEEDS_CORRECTION**.