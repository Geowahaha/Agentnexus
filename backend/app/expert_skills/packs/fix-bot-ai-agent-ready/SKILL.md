---
name: fix-bot-ai-agent-ready
description: Free agent-readiness scan and fix pack aligned with isitagentready.com — robots.txt AI rules, Content Signals, llms.txt, Markdown negotiation, MCP/OAuth discovery, and commerce protocol checks. Use when the user wants a free bot/AI agent scan, Fix Bot AI, isitagentready-style audit, or deployable fixes for ChatGPT/Perplexity/Claude crawlers. Example reference site successcasting.com.
---

# Fix Bot AI — Free Agent-Ready Scan

Free marketplace run: **URL in → agent-readiness scorecard + paste-ready fix files out.**

Rubric mirrors [isitagentready.com](https://isitagentready.com/) (Cloudflare 12-check style) across five categories:

| Category | Checks |
|----------|--------|
| Discoverability | robots.txt, sitemap, Link headers, DNS-AID |
| Content Accessibility | Markdown negotiation (`Accept: text/markdown`) |
| Bot Access Control | AI bot rules, Content Signals, Web Bot Auth |
| Protocol Discovery | API Catalog, OAuth, auth.md, MCP Server Card, Agent Skills, WebMCP |
| Commerce | x402, MPP, UCP, ACP |

## Workflow

1. **Scan** — AIBotAuth MCP deterministic fetch (same engine family as paid AI Visibility).
2. **Audit** — Map findings to isitagentready categories; prioritize easy wins (robots.txt + llms.txt + Content-Signal).
3. **Fix pack** — Ship full file contents: robots.txt, llms.txt, agents.txt, ai.txt, JSON-LD, `_headers` / `next.config` snippets.
4. **QA** — Verify no invented endpoints, Markdown links in llms.txt, policy consistency (`ai-train=no, search=yes, ai-input=yes` unless buyer opts in).

Read before prescribing:

- `references/isitagentready-checklist.md` — exact check list and pass criteria
- `references/marketplace-deliverables.md` — free-run output format
- `references/successcasting-case-study.md` — production before/after example (www.successcasting.com)

## Non-negotiable rules

- **Easy wins first:** valid robots.txt with AI bot rules + sitemap + useful discovery metadata.
- **Policy one source of truth:** robots.txt, llms.txt, ai.txt, agents.txt, and `Content-Signal` header must agree.
- **Honest discovery:** never ship MCP Server Card / API Catalog unless those endpoints exist.
- **No secrets** in output — ever.
- **Reference scan:** buyers may also run https://isitagentready.com/ manually to compare scores.

## Upgrade path

Free run covers core access + discovery fixes. Paid **Agent-Ready Auto Fix Pro** ($9.99) ships the full Level 5 fix pack (protocol + commerce) with deploy guide — same playbook as successcasting.com 25% → 100%. **AI Visibility Audit 2026** ($2.50) adds deeper advisory.