# isitagentready.com — Check Reference

Source: https://isitagentready.com/ (Cloudflare agent-readiness scanner).

## Discoverability

| Check | Path / signal | Pass criteria |
|-------|---------------|---------------|
| robots.txt | `/robots.txt` | 200; explicit AI bot rules; sitemap directive |
| Sitemap | `/sitemap.xml` or robots Sitemap line | 200 or valid index |
| Link headers | `Link` response header | Discovery hints (agents.txt, llms.txt) where applicable |
| DNS-AID | DNS records | Optional; document if absent |

## Content Accessibility

| Check | Test | Pass criteria |
|-------|------|---------------|
| Markdown negotiation | `Accept: text/markdown` on HTML pages | Returns `text/markdown` when enabled (e.g. Cloudflare Markdown for Agents) |

## Bot Access Control

| Check | Signal | Pass criteria |
|-------|--------|---------------|
| AI bot rules | robots.txt | GPTBot, ClaudeBot, PerplexityBot, OAI-SearchBot, Google-Extended addressed |
| Content Signals | robots.txt or `Content-Signal` header | `search`, `ai-input`, `ai-train` explicit and consistent |
| Web Bot Auth | HTTP signature headers | Optional for SMB; note N/A if not implemented |

## Protocol Discovery

| Check | Path | Pass criteria |
|-------|------|---------------|
| API Catalog | RFC 9727 well-known | Only if site has public API |
| OAuth discovery | `/.well-known/oauth-*` | Only if OAuth exists |
| auth.md | `/auth.md` or well-known | Document auth for agents if applicable |
| MCP Server Card | well-known MCP card | Only if MCP server is live |
| Agent Skills | skills index | Only if published |
| WebMCP | form `data-tool*` hints | Optional UX signal |

## Commerce

x402, MPP, UCP, ACP — N/A unless site sells via agentic commerce. Do not fake.

## Scoring guidance for OBOLLA free run

- Count PASS / FAIL / N/A per category.
- Overall readiness = weighted by **Bot Access** + **Discoverability** first.
- If HTTP 401/403/522 on homepage, banner **limited audit** — P0 = access.