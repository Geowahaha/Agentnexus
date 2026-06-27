# Image prompt template — MS Paint line-art 9:16 (Reels)

## Style block (copy into every prompt)

```
MS Paint beginner drawing style, white background, thick uneven black outlines,
stick-figure people with round heads, wobbly bodies, intentionally ugly and funny,
no shading, no gradients, no anime, no 3D, no professional illustration,
looks like a kid drew it in MS Paint, 9:16 vertical portrait aspect ratio,
scene:
```

## Rules

- **Never** add "beautiful", "detailed", "cinematic", "4K illustration".
- Match the **narrator line at that second** — not a generic recap.
- **Vertical only** — horizontal shots break Reels layout.
- Keep compositions **center-weighted** — faces/actions in middle safe zone (not cropped by UI chrome).

## Output table format (agent must produce)

| Timestamp | Narrator line | On-screen text | Full image prompt | Filename |
|-----------|---------------|----------------|-------------------|----------|
| 0:00 | Hook line… | HOOK TEXT | [style block + scene] | 0-00 |
| 0:02 | Next beat… | keyword | … | 0-02 |

## Optional automation note

Buyers may paste the prompt column into Higgsfield / GPT Image 2 batch tools. OBOLLA delivers the table — buyer runs the renderer.