---
name: seo-expert-analysis
description: Professional-grade SEO Expert Analysis for any website URL. Multi-agent pipeline covers competitor intelligence, content gap analysis, technical SEO audit (CWV, crawlability, on-page, schema), and prioritized action plans with impact forecasts. Use when the user wants a premium SEO audit, competitor analysis, technical SEO review, Core Web Vitals diagnosis, or downloadable SEO report — distinct from AI-bot visibility audits.
---

# SEO Expert Analysis — Agency Playbook

Premium SEO skill for AgentNexus marketplace runs. Five specialist agents collaborate after deterministic scans. **Do not clone backlink databases** — competitor intelligence comes from public SERP signals, site structure, and content patterns only.

## Analysis pillars

| Pillar | Weight | Primary agent |
|---|---|---|
| Competitor & market | 25% | Researcher → Analyzer |
| Content gap & opportunity | 25% | Analyzer |
| Technical SEO | 30% | Auditor |
| Performance (CWV) | 10% | Auditor |
| Action plan & forecast | 10% | Optimizer → Report |

## Workflow (marketplace run)

1. **Technical Scan** — `mcp.aibotauth.tech_audit` + `mcp.aibotauth.scan` for crawl signals
2. **Site Intelligence** — crawl customer URL; auto-extract title, meta, headings, internal links, keywords (unigrams + bigrams), search intent; optional web context for competitors
3. **Researcher** — use auto-extracted keywords as primary source; identify 3–5 competitors (no backlink DB). User may optionally override keywords in task — never required
4. **Analyzer** — content structure, gaps, competitor strengths/weaknesses, winnable queries
5. **Auditor** — technical + on-page rubric (see `references/technical-seo-rubric.md`, `references/on-page-rubric.md`)
6. **Optimizer** — P0/P1/P2 fixes with **predicted impact** (conservative ranges, never guarantee rankings)
7. **Report Generator** — executive summary, quick wins, long-term roadmap, professional markdown report

## Scoring model (0–100)

- **Technical** /25 — crawl, index, HTTPS, canonicals, robots, sitemap
- **On-page** /25 — titles, meta, headings, URLs, internal links
- **Content** /20 — depth, intent match, E-E-A-T signals, freshness
- **Performance** /15 — LCP, INP, CLS, TBT (from scan or stated metrics)
- **Competitive position** /15 — gap severity vs identified competitors

Overall = weighted sum. Always show sub-scores.

## Impact forecasting rules

- Use **ranges** not guarantees: e.g. "Fixing LCP 16s→3s: estimated 15–25% organic CTR improvement on mobile"
- Tie every P0 fix to a measurable verification (PSI, GSC, crawl test)
- Quick wins = <1 week effort; Long-term = 1–3 months

## References

- Deliverables format → `references/marketplace-deliverables.md`
- Technical rubric → `references/technical-seo-rubric.md`
- On-page rubric → `references/on-page-rubric.md`
- Competitor methodology → `references/competitor-analysis.md`