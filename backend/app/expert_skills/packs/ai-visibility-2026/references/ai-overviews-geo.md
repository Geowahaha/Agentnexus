# Layer 2 — Google AI Overviews, AI Mode & LLM Citation (AEO/GEO), 2026

## The market reality (use these numbers when making the business case)

- AI Overviews appear on ~25–48% of queries (depending on study/quarter, doubling year-over-year) and reach ~2B monthly users.
- Organic CTR drops 34–61% on queries where an AI Overview appears — uncited pages absorb the loss.
- BUT: pages **cited inside** the AI Overview earn ~35% more clicks than a traditional ranking alone, and AI-referred traffic converts ~5× better (≈14% vs ≈3%) because the visitor arrives pre-qualified.
- ~74–76% of citations come from top-10 organic results — classic SEO still feeds the pool — yet ~14% of cited URLs don't rank organically at all, and many citations come from positions 4–20+. Citation is a separate track from rank-chasing.
- Content under ~3 months old is ~3× more likely to be cited. Freshness is a citation factor.
- Since the December 2025 core update, E-E-A-T requirements extend to ALL content categories.
- Google's own 2026 AI Optimization Guide confirms: there is no secret separate AI ranking system — quality + technical hygiene win both tracks; the difference is the citation pool reaches beyond the top 10, so extractability and trust decide who gets lifted.

## The citation selection factors (ranked by evidence strength)

1. **Semantic completeness** — self-contained passages (~134–167 words) that fully answer the query with no external context needed. Strongest single predictor.
2. **Extractable structure** — answer blocks, question headings (H2/H3 phrased as real buyer questions), lists, tables, comparison grids. The AI lifts units, not pages.
3. **E-E-A-T & entity density** — named author with credentials, organization entity consistent across the web (same name/address/phone/profile everywhere), ~15+ recognized entities per 1,000 words (named tools, standards, places, people, products).
4. **Multi-modal** — text + original images (+ video where natural) + structured data on the same page lifts selection substantially.
5. **Authoritative outbound citations** — pages that cite credible sources are themselves more trusted for citation.
6. **Freshness** — visible updated dates backed by real changes.
7. **Position in page** — ~44% of LLM citations come from the first 30% of the text. Front-load the answer; never bury the lede under a story intro.

## The answer-block formula (use verbatim as the content template)

```
## [Exact buyer question as the heading]
[Direct answer in 1–2 sentences, 20–40 words.]
[2–3 sentences of reasoning, evidence, or context — include a statistic or named source.]
[Optional: list or table covering the variants/edge cases.]
```

Every commercial page needs 3–7 of these blocks targeting the questions buyers actually ask AI engines ("best sand casting factory in Thailand for 50kg aluminum parts", "lead time for custom casting", "how to check casting quality").

## Schema that matters for citation

- `Organization` / `LocalBusiness` with full NAP, `sameAs` links to all social profiles, geo coordinates.
- `FAQPage` mirroring the on-page answer blocks (must match visible text).
- `Article`/`Product` with `author`, `datePublished`, `dateModified`.
- `HowTo` only where genuine procedures exist.
- Keep schema in HTML — note that pure-markdown bot views strip JSON-LD, one reason HTML stays the canonical version (see agent-readiness.md, Markdown for Agents caveats).

## Measuring layer 2 (define proof, not vibes)

- **Citation probes:** monthly, ask each engine (AI Overviews via incognito search, ChatGPT search, Perplexity, Claude w/ search, Gemini) 5–10 real buyer questions; record brand named? domain cited? position? which competitors appear?
- **Share of voice** = your citations ÷ total citations across your probe set; trend it.
- Track AI-referral traffic separately (utm/referrer patterns: chatgpt.com, perplexity.ai, gemini, copilot) — conversion rate here is the money metric.
- Server logs / Cloudflare AI Crawl Control analytics: are GPTBot, OAI-SearchBot, PerplexityBot, ClaudeBot actually fetching (and how often)? Crawl frequency is the leading indicator of citation.

## What Google explicitly killed (don't recommend these)

- Separate "AI versions" of pages for ranking purposes (the guide and Googlers reject special markup/files as ranking inputs — llms.txt etc. matter for *other engines and agents*, not Google ranking).
- Commodity content: generic how-tos identical to hundreds of existing pages. First-hand experience, proprietary data, and real photos are what Google names as the durable differentiator.
- Keyword-density tactics, AI-spun bulk pages, fake authors.
