---
name: ai-visibility-2026
description: Expert digital-marketing-agency playbook for making any website, brand, or social account rank in the AI-search era (2026 algorithms). Use this skill whenever the user asks about SEO, AEO, GEO, AIO, AI Overviews, AI Mode, LLM citations, AI crawlers, llms.txt, agent-readiness, Markdown for Agents, Content Signals, Web Bot Auth, MCP discovery, agentic commerce (x402/ACP/UCP), building a new website "the right way today", launching a social/brand account, auditing a site's AI visibility score, or asks "what must I build to be found by ChatGPT/Perplexity/Claude/Gemini/Google AI". Also trigger when interpreting agent-readiness scan results or designing scanner/audit features.
---

# AI Visibility 2026 — Agency-Grade Playbook

The 2026 discovery landscape is **five stacked layers**. A site that wins only layer 1 is invisible to half the buyers. Score each layer, fix bottom-up, and always ship the fix file, never just the finding.

| # | Layer | Who reads it | Core artifacts |
|---|---|---|---|
| 1 | Classic SEO | Googlebot, Bingbot | titles, schema, CWV, links |
| 2 | AI answer citation (AEO/GEO) | AI Overviews, AI Mode, ChatGPT, Perplexity, Claude | answer blocks, entities, E-E-A-T, freshness |
| 3 | AI crawler access | GPTBot, ClaudeBot, PerplexityBot, OAI-SearchBot, Google-Extended | robots.txt, Content-Signals, llms.txt, WAF rules |
| 4 | Agent readiness | Autonomous agents, MCP clients | Markdown negotiation, Link headers, /.well-known/* discovery, MCP Server Card, Agent Skills, WebMCP |
| 5 | Agentic commerce | Buying agents | x402, ACP, UCP, MPP, Pay-Per-Crawl |

## Workflow

1. **Identify the scenario** and read the matching reference (read more than one if the task spans layers):
   - New website build, or fixing an existing site → `references/new-website-blueprint.md` (day-one checklist + copy-paste files)
   - Getting cited by Google AI Overviews / AI Mode / LLMs → `references/ai-overviews-geo.md` (citation algorithm data + content formulas)
   - Agent-readiness, well-known endpoints, scanner results, MCP/commerce protocols → `references/agent-readiness.md` (every standard, exact paths, minimal valid files)
   - New social/brand account launch or social algorithm strategy → `references/social-branding-2026.md`
   - Building scanner/audit features, packaging or pricing agency services, certification/badge programs, Pay-Per-Crawl advisory → `references/agency-productization.md` (exact check specs + service ladder)
   - Building/registering/operating a verified bot or signed agent with cryptographic identity (Web Bot Auth, RFC 9421), Cloudflare Bot Directory submission, key directory setup, crawltest validation, delisting/activity rules → `references/verified-bot-operations.md`
   - **AgentNexus Marketplace paid run** ($2.50/run, URL in → deliverables out) → `references/marketplace-deliverables.md` (scorecard, P0/P1/P2, paste-ready files, bot before/after table, QA checklist)
2. **Score before prescribing.** When a site is given, check it (fetch robots.txt, llms.txt, homepage head, key /.well-known paths) or interpret the user's scan output. Map every finding to a layer.
3. **Prioritize bottom-up within budget.** Layer 3 blockers (bots blocked by WAF/robots) zero-out layers 2 and 4 — fix access first, then citation content, then agent discovery, then commerce.
4. **Ship fixes, not advice.** Every recommendation must come with the actual file content (robots.txt, llms.txt, JSON-LD, Link header line, well-known JSON) ready to deploy, using the templates in the references. Localize to the user's market and language (e.g., Thai SMEs: Thai content, LINE OA, PromptPay context).
5. **Define proof.** State the measurable check that verifies each fix (re-scan score, citation probe query, `curl -H "Accept: text/markdown"` test, DoH lookup).

## Non-negotiable 2026 rules (apply in every answer)

- **Answer-block formula** for any content meant to be cited: question heading → 20–40 word direct answer → 2–3 sentences of reasoning → list/table. Self-contained passages of ~134–167 words are the extraction unit AI engines lift.
- **One source of truth on access:** robots.txt + Content-Signal directives declare policy; CDN/WAF must agree. The #1 silent killer is a WAF blocking AI bots while robots.txt allows them.
- **Markdown negotiation is now table stakes on Cloudflare:** `Accept: text/markdown` should return `Content-Type: text/markdown` (one dashboard toggle in AI Crawl Control — but check the default Content-Signal it sets: `ai-train=yes, search=yes, ai-input=yes`).
- **E-E-A-T applies to ALL content categories** since the Dec 2025 core update, not just YMYL. Named authors, dates, citations to authoritative sources, and consistent entity identity (same NAP everywhere) are mandatory filters, not bonuses.
- **Freshness compounds:** content under ~3 months old is ~3× more likely to be cited; add visible "Updated" dates and actually update.
- **No fake compliance:** never recommend stuffing well-known files a site can't honor (e.g., an MCP Server Card pointing at no server). Empty discovery endpoints damage agent trust.

## Quick layer diagnosis from symptoms

- "Traffic down but rankings stable" → layer 2 (AI Overviews absorbing clicks; optimize for citation, measure share-of-voice in AI answers).
- "AI chatbots never mention us" → layers 2+3 (run citation probes; check bot access; check entity consistency).
- "Scanner says Level 1 / low agent score" → layer 4 (work through agent-readiness.md top-down: Markdown negotiation and Link headers first — they're cheapest).
- "Want agents to buy from us" → layer 5 (only after 1–4 are solid).
