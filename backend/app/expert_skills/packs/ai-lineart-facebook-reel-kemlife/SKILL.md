---
name: ai-lineart-facebook-reel-kemlife
description: Faceless Facebook Reels kit — MS Paint-style line-art cartoons with AI. Hook research → short script → per-shot 9:16 image prompts → Reels caption/QA. KEMLIFE-style vertical shorts (reference reel workflow).
---

# AI Line-Art Facebook Reels Kit (KEMLIFE-style)

Help buyers run **faceless Facebook Reels** with deliberately **homemade MS Paint line-art** visuals — same ugly charm as the YouTube kit, but **vertical, fast, and hook-first**.

**Inspiration:** KEMLIFE community workflow + reference Reel pattern ([Facebook Reel example](https://www.facebook.com/reel/2039899173277798)). OBOLLA orchestrates script and prompt pipeline; image renderers and CapCut stay buyer-side tools.

## Who this is for

- Creators posting **Facebook Reels** (and cross-posting to Instagram Reels / TikTok)
- **History / psychology / curiosity** micro-stories (30–90 seconds)
- Thai or English — match buyer language in every deliverable
- Buyers who will **not** appear on camera

## Core rule (non-negotiable)

> **Do not make art pretty.** Thick uneven black lines, white background, round stick heads, wobbly bodies. If it looks professional, it failed.

## Pipeline (4 LLM steps)

| Step | Output |
|------|--------|
| Hook & Angle Research | 3–5 Reel concepts with **1-second hook** lines, why-it-stops-the-scroll, curiosity gap |
| Script + Timestamps | 30–90s voiceover with **dense** timestamps (`0:00`, `0:02`, `0:04`…) — **one timestamp = one image** |
| Shot Prompts | Per-timestamp image prompts, **9:16 vertical**, MS Paint style block + scene |
| Reels Publish QA | Filename map, CapCut vertical edit notes, on-screen text, caption + hashtags, READY checklist |

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
2. **Edit style** — fast cut, punch zoom, text-heavy, meme hold (Reels)
3. **Language** — Thai or English voiceover + on-screen text
4. **Target length** — default **45–60 seconds** (max 90s)
5. **Optional** — reference Reel or sub-topic angle

## Image prompt style block (prepend to every shot)

```
MS Paint beginner drawing style, white background, thick uneven black outlines,
stick-figure people with round heads, intentionally ugly and charming,
no shading, no gradients, no professional illustration, 9:16 vertical portrait,
scene: [WHAT THE NARRATOR SAYS AT THIS TIMESTAMP]
```

See `references/image-prompt-template.md` for batch tables and Higgsfield/CLI examples.

## External tools (buyer runs — not OBOLLA)

- **Script:** Notion, ChatGPT, or this agent flow
- **Image batch:** Higgsfield (`gpt_image_2`, `--aspect_ratio 9:16`) or any 9:16 image model
- **Voice:** ElevenLabs TTS or self-recorded
- **Edit:** CapCut (vertical timeline, burned-in hook text first 2s)
- **Publish:** Facebook Reels (caption + hashtags in QA pack)

## Marketplace deliverables

See `references/marketplace-deliverables.md`. End QA with **READY** or **NEEDS_CORRECTION**.