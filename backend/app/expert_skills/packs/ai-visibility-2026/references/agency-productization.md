# Agency Productization — Turning the 2026 Stack into Sellable Services & Scanner Features

Use this when the user is an agency/tool-builder (not just a site owner): designing audit/scanner features, packaging services, or pricing AI-visibility work. Written for first-mover markets (e.g., Thai SMEs) where nobody else scores these layers yet.

## 1. Scanner check specs — Layer 3/4 checks to implement (exact test logic)

Each check: request → pass condition → fail message → the fix artifact your tool should auto-generate (finding must ship with the fix).

| Check | Test | Pass | Auto-generated fix |
|---|---|---|---|
| AI bot live access (per bot) | GET / with each AI bot UA (GPTBot, ClaudeBot, OAI-SearchBot, Claude-SearchBot, PerplexityBot, ChatGPT-User, Google-Extended, Bingbot) | HTTP 200 + same content as browser UA (compare title/word count; flag cloaking & 403/503/challenge pages) | WAF allowlist instructions per CDN + corrected robots.txt |
| robots.txt AI rules | GET /robots.txt; parse User-agent groups | Explicit rules for ≥5 major AI bots (wildcard-only = partial credit) | Full 2026 robots.txt |
| Content Signals | Parse robots.txt for `Content-Signal:` lines; also check `Content-Signal` response header on / | Valid `search/ai-input/ai-train` directives present | Directive line matching owner's stated policy |
| llms.txt | GET /llms.txt | 200, text/markdown or text/plain, H1 + ≥1 link section; cross-check links resolve | Generated llms.txt from sitemap + page summaries |
| Markdown negotiation | GET / with `Accept: text/markdown` | `Content-Type: text/markdown` (record `x-markdown-tokens` if present; report token savings vs HTML) | Cloudflare toggle instructions OR .md sibling-page middleware |
| Link headers (RFC 8288) | HEAD /; parse `Link` header | ≥1 relevant rel (llms-txt, api-catalog, service-doc) pointing at a 200 resource | `_headers` / nginx config line |
| Well-known sweep | GET /.well-known/{api-catalog, mcp/server-card.json, agent-skills/index.json, oauth-authorization-server, oauth-protected-resource, acp.json, ucp, http-message-signatures-directory} + /auth.md + /openapi.json | Per-file: 200 + correct content-type + minimal schema validity; ALSO verify advertised endpoints respond (dead pointer = worse than absent, score negative) | Minimal valid file for each the client can honestly support |
| DNS-AID | DoH (cloudflare-dns.com/dns-query, accept: application/dns-json) SVCB/HTTPS/TXT at `_index._agents.`, `_mcp._agents.`, `_a2a._agents.` on apex + www; check AD flag for DNSSEC | ≥1 valid record whose endpoint answers | DNS record values + DNSSEC enablement steps |
| WebMCP | Headless render; check `navigator.modelContext` tool registrations after load | ≥1 tool with name/description/inputSchema/execute | Starter quote-form tool JS snippet |
| Bot identity (advanced) | Check /.well-known/http-message-signatures-directory | 200 + valid JWKS-style directory | n/a for most SMBs; note as informational |

Scoring guidance: weight access checks (bot 200s, robots) highest — they gate everything; well-knowns score only when honest (live endpoints); commerce protocols informational-only until adoption matures. Re-scan after fix = the before/after proof artifact.

**Differentiator for the scanner itself:** sign your own scanner's requests with Web Bot Auth (RFC 9421) and publish your directory. You become one of the first verified-identity audit bots — gets you through bot defenses legitimately and is a credibility line in every report.

## 2. The flagship upsell — "Agent-Ready in Half a Day" (MCP via Cloudflare AI Search)

Package: index the client's site in a Cloudflare AI Search instance (managed storage + web crawl + built-in MCP endpoint + public ask endpoint + embeddable search UI) → publish MCP Server Card → add DNS-AID records → re-scan. Client goes from 0/7 on API/MCP discovery to a working "ask this business anything" capability without writing a server. Deliverables: the live ask widget on their site, the server card, the re-scan certificate. This is the highest perceived-value/effort ratio service in the 2026 stack.

## 3. Service ladder (first-mover SME market template)

1. **Free scan** (lead magnet) → shareable score page with the agency's branding = viral loop. Add an embeddable **"Agent-Ready" badge** (score + level, links to the scan) — every client site that displays it is a backlink + advertisement; certification framing creates the category and the agency owns the rubric.
2. **Fix Pack** (fixed price): P0/P1 items — robots/Content-Signals/llms.txt/WAF alignment/Link headers/Markdown toggle + schema. Deliver before/after scan as proof.
3. **Citation Engine** (monthly): answer-block content production in the market language + monthly citation probes across engines + share-of-voice report. The probe report IS the retention product — visibility scores are abstract; "Gemini named your competitor, not you, for 'โรงหล่อทราย โคราช'" is visceral.
4. **Agent-Ready upgrade** (project): the §2 package.
5. **Commerce-Ready** (project, e-commerce only): ACP discovery + Stripe/PromptPay flow when agentic checkout reaches the market.

Localization notes (Thai SME archetype): bundle LINE OA setup/rich menu into Fix Pack (the conversion channel), PromptPay for billing, Google Business Profile + NAP cleanup as mandatory P0 (entity layer), probe queries written in Thai buyer phrasing.

## 4. Monetization advisory you can sell to publishers

For content-heavy clients losing traffic to AI: present the three-way choice per crawler — allow (visibility), block (withhold), charge (Cloudflare Pay-Per-Crawl 402 / x402). Most SMEs should allow answer-engines and decide deliberately on training bots; media/IP clients are the charge candidates. Charging consulting fees to configure this is a real 2026 service line.
