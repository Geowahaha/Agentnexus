# Workflow steps — KEMLIFE-style faceless line-art Facebook Reels

## 1) Hook first — scroll-stop in 1 second

- Study Reels that already win in your niche (KEMLIFE-style curiosity shorts).
- Pick topics where the **first spoken line** forces a pause — not a slow intro.
- Strong angles: body secrets, psychology "why you…", history WTF — one punchy question.
- **Ugly art cannot save a weak hook.**

## 2) Write micro-script, timestamp every beat

- Target **45–60 seconds** (15–30 shots); max 90s for complex stories.
- Timestamps every **1–3 seconds** — Reels punish slow image holds.
- **One timestamp = one image.**
- Line 1 (0:00–0:02) = hook on screen **and** in voice.

## 3) Expand to image prompts per shot

- For each timestamp, one prompt matching **exactly** what the voice says then.
- All prompts **9:16 vertical** for Facebook/Instagram Reels.
- Prepend the MS Paint style block (see `image-prompt-template.md`).
- Output table: `time | narrator line | on-screen text | image prompt | filename`.

## 4) Batch image generation (buyer-side)

Example CLI pattern (Higgsfield + GPT Image 2):

```
higgsfield generate create gpt_image_2 --prompt "MS Paint beginner..." --aspect_ratio 9:16 --wait
```

- Queue sequentially until all shots done (typically 15–35 images for 60s).

## 5) Download and name by timestamp

- Filename = timestamp: `0-00.png`, `0-02.png`, `0-05.png` for CapCut alignment.

## 6) Vertical edit + Facebook publish

- CapCut: 9:16 project, images on every beat, **bold hook text** first 2 seconds.
- Burn-in key words for muted viewers (short phrases, not paragraphs).
- Voice clear; music low; optional auto-captions as backup.
- Facebook Reels: paste caption + hashtags from QA pack; cross-post to IG if desired.