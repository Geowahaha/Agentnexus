# Workflow steps (KEMLIFE-style faceless line-art YouTube)

## 1) Find the story first — do not rush production

- Spy on channels already winning in this niche (e.g. Zenn-style curiosity history).
- Use VPH / trending signals (vidIQ or similar) — pick topics where the **title alone** forces a click.
- Strong angles: human history, psychology, body secrets — "I need the answer" hooks.
- **Ugly art cannot save a weak topic.**

## 2) Write script, then timestamp every beat

- Write smooth narration first.
- Add timestamps: `0:00`, `0:03`, `0:07`, `0:12` … denser cuts = less boring video.
- **One timestamp = one image.**
- If audio exists, run through TurboScribe to get timed transcript.

## 3) Expand to image prompts per shot

- For each timestamp, one prompt that matches **exactly** what the voice says then.
- All prompts **16:9 horizontal** for YouTube.
- Prepend the MS Paint style block (see `image-prompt-template.md`).
- Output as a table: `time | narrator line | image prompt | suggested filename`.

## 4) Batch image generation (buyer-side automation)

Example CLI pattern (Higgsfield + GPT Image 2):

```
higgsfield generate create gpt_image_2 --prompt "MS Paint beginner..." --aspect_ratio 16:9 --wait
```

- Often **1 concurrent** image — queue sequentially until all shots done (e.g. 38 images).
- Claude Code or scripts can loop prompts from the table.

## 5) Download and name by timestamp

- Images may be URLs — download all to one folder.
- Filename = timestamp: `0-00.png`, `0-03.png`, `0-20.png` for instant CapCut alignment.

## 6) Voice, edit, upload

- TTS or record voiceover from script.
- Align images to audio in CapCut/DaVinci — image changes on every spoken beat.
- Light captions, soft background music, render 16:9.
- Title + thumbnail must punch — same curiosity as step 1.