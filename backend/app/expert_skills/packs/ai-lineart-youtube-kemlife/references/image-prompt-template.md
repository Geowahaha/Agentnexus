# Image prompt template — MS Paint line-art 16:9

## Style block (copy into every prompt)

```
MS Paint beginner drawing style, white background, thick uneven black outlines,
stick-figure people with round heads, wobbly bodies, intentionally ugly and funny,
no shading, no gradients, no anime, no 3D, no professional illustration,
looks like a kid drew it in MS Paint, 16:9 horizontal aspect ratio,
scene:
```

## Rules

- **Never** add "beautiful", "detailed", "cinematic", "4K illustration".
- Match the **narrator line at that second** — not a generic recap.
- Keep characters consistent within a video (same stick style).
- Horizontal only — vertical shots break YouTube layout.

## Output table format (agent must produce)

| Timestamp | Narrator line | Full image prompt | Filename |
|-----------|---------------|-------------------|----------|
| 0:00 | Hook line… | [style block + scene] | 0-00 |
| 0:03 | Next beat… | … | 0-03 |

## Optional automation note

Buyers may paste the prompt column into Higgsfield / GPT Image 2 batch tools. OBOLLA delivers the table — buyer runs the renderer.