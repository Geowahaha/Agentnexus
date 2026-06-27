---
name: short-post-creator
description: Short social text post creator — research → draft variants → polish → publish QA. X, Threads, LinkedIn, Facebook text posts.
---

# Short Post Creator

Help buyers ship **short-form text posts** that fit each platform's character limits and culture.

## Who this is for

- Creators posting on **X (Twitter), Threads, LinkedIn, Facebook** (text-first)
- Thai or English — match buyer language
- Micro-content: hooks, threads, hot takes, announcements

## Pipeline (4 LLM steps)

| Step | Output |
|------|--------|
| Research | Audience, angle, platform constraints, tone |
| Draft | 3 post variants (different hooks) |
| Edit | Polished primary + backup variant + thread split if needed |
| Publish QA | Length check, CTA, READY verdict |

Details: `references/workflow-steps.md`, `references/platform-formats.md`

## Buyer input (task mode)

Ask for (or infer):

1. **Topic / message** — what to communicate
2. **Platform** — X, Threads, LinkedIn, Facebook
3. **Tone** — witty, professional, educational, provocative
4. **Language** — Thai or English
5. **Optional** — thread (multi-tweet), emoji policy, brand voice

## Platform limits (enforce in edit step)

| Platform | Single post | Thread |
|----------|-------------|--------|
| X | 280 chars (or Premium 25k — default 280) | Numbered 1/N |
| Threads | 500 chars | Split at natural breaks |
| LinkedIn | ~3,000 chars | Short paragraphs |
| Facebook | ~500 chars for engagement | Optional follow-up comment |

## Marketplace deliverables

See `references/marketplace-deliverables.md`. End QA with **READY** or **NEEDS_CORRECTION**.