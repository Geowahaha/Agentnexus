# Layers 3–5 — AI Crawler Access, Agent Readiness & Agentic Commerce (2026 standards)

Every standard below is something live scanners (e.g., isitagentready.com-style tools, Cloudflare's 12-check rubric) actually test. For each: what it is, the exact path/header, a minimal valid implementation, and whether a typical SMB should ship it. Implement honestly — never publish discovery files pointing at capabilities that don't exist.

## Table of contents
1. Layer 3 — Access: robots.txt AI rules · Content Signals · llms.txt · WAF alignment · Cloudflare AI Crawl Control · Web Bot Auth
2. Layer 4 — Discovery: Markdown for Agents · Link headers (RFC 8288) · DNS-AID · API Catalog (RFC 9727) · OAuth/OIDC discovery · auth.md · MCP Server Card · Agent Skills index · WebMCP · NLWeb/AI Search
3. Layer 5 — Commerce: Pay-Per-Crawl · x402 · MPP · UCP · ACP
4. Priority matrix for SMBs

---

## 1. LAYER 3 — ACCESS

### robots.txt with explicit AI bot rules
Wildcard `User-Agent: *` technically covers AI bots, but explicit rules score higher on audits and let you differentiate training vs search crawlers. The 2026 bot roster to address: GPTBot, OAI-SearchBot, ChatGPT-User, ClaudeBot, Claude-SearchBot, Claude-User, PerplexityBot, Perplexity-User, Google-Extended, GoogleOther, Bingbot, Meta-ExternalAgent, Amazonbot, Applebot-Extended, Bytespider, CCBot.

Standard SMB policy (visibility-maximizing — allow search/answer crawlers, owner decides on training):
```
# Answer/search engine crawlers — ALLOW (these drive citations & customers)
User-agent: OAI-SearchBot
Allow: /
User-agent: ChatGPT-User
Allow: /
User-agent: Claude-SearchBot
Allow: /
User-agent: Claude-User
Allow: /
User-agent: PerplexityBot
Allow: /
User-agent: Perplexity-User
Allow: /

# Training-only crawlers — owner's choice (Allow for max visibility; Disallow to withhold training data)
User-agent: GPTBot
Allow: /
User-agent: ClaudeBot
Allow: /
User-agent: Google-Extended
Allow: /
User-agent: CCBot
Disallow: /

User-agent: *
Allow: /
Disallow: /admin
Disallow: /api

Content-Signal: search=yes, ai-input=yes, ai-train=yes
Sitemap: https://example.com/sitemap.xml
```

### Content Signals (contentsignals.org, IETF draft)
Machine-readable usage policy inside robots.txt (or as an HTTP `Content-Signal` response header). Three directives: `search` (indexing/answering), `ai-input` (RAG/agentic use at inference), `ai-train` (model training). Cloudflare can inject these network-wide. **Caveat:** enabling Cloudflare's Markdown for Agents currently sets `Content-Signal: ai-train=yes, search=yes, ai-input=yes` by default on converted responses — review before toggling if the client restricts training use.

### llms.txt (+ llms-full.txt)
`/llms.txt` = curated markdown map of the site for LLMs: H1 site name, blockquote summary, sections of `[Title](url): one-line description`. `/llms-full.txt` = full flattened content. Not a Google ranking input; widely read by other engines/agents and dirt-cheap. Keep it in sync with the sitemap. Cloudflare's own docs ship both per-product — the reference implementation pattern.

**2026 audit rule:** always use Markdown link syntax — never bare URLs on their own line. Production audits show bare-URL llms.txt files score lower on Structure and are harder for agents to follow.

Minimal valid example:
```markdown
# Pinpoint Accounting Service

> Full-service accounting for small businesses in the Pacific Northwest.

## Key pages
- [Home](https://example.com/): Services overview and contact.
- [About](https://example.com/about): Team and credentials.
- [Pricing](https://example.com/pricing): Plans and onboarding.

## Contact
support@example.com
```

Pair with `Content-Signal: search=yes, ai-input=yes` in robots.txt and CDN `_headers` so agents may cite and use content at inference time.

### WAF / bot-management alignment (the #1 silent killer)
Audit finding seen constantly: robots.txt allows AI bots while the WAF/bot-fight-mode blocks them with 403s. Verify with real fetches per bot UA (a bot-access tester), and in Cloudflare: AI Crawl Control → per-crawler allow/block decisions; check Security Events for blocked AI UAs. Declared policy and enforced policy must match — scanners and bot operators both notice hypocrisy.

### Cloudflare AI Crawl Control (free, all plans)
Dashboard surface for: per-AI-crawler allow/block, crawler analytics (who fetches what, how often — your leading indicator of AI visibility), robots.txt violation tracking, Pay-Per-Crawl (private beta, HTTP 402), and the Markdown for Agents toggle. For any Cloudflare-hosted client this is step 1 of an engagement: read the analytics before changing anything.

### Web Bot Auth (RFC 9421 HTTP Message Signatures)
Cryptographic bot identity replacing spoofable user-agents; backed by Cloudflare + GoDaddy (with ANS). Site-owner side: mostly *consume* verification (Cloudflare Verified Bots). Publishing `/.well-known/http-message-signatures-directory` matters if you OPERATE a bot/agent (e.g., a scanner product should sign its own crawls — differentiator for an audit-tool vendor). For a normal SMB site: skip; rely on CDN verification.

---

## 2. LAYER 4 — DISCOVERY & AGENT INTERACTION

### Markdown for Agents (content negotiation)
Request with `Accept: text/markdown` → response `Content-Type: text/markdown` (+ optional `x-markdown-tokens`). Cuts agent token cost ~80%. On Cloudflare Pro/Business: one toggle in AI Crawl Control (edge converts HTML→MD on the fly, YAML frontmatter from meta tags + body markdown; cacheable). Self-hosted: middleware that converts or serves pre-rendered `.md` siblings (Cloudflare docs pattern: every page also at `<url>/index.md`). Test: `curl -sH "Accept: text/markdown" https://site/ -D- | grep -i content-type`. Note the Google dissent (Mueller: HTML is fine for bots; markdown strips schema) — recommendation: enable it for agent efficiency, keep HTML canonical and schema-complete; it's additive, not a replacement.

### Link headers (RFC 8288) — cheapest score win
Homepage response headers advertising agent resources:
```
Link: </.well-known/api-catalog>; rel="api-catalog", </llms.txt>; rel="llms-txt", </docs/api>; rel="service-doc"
```
On Cloudflare Pages: add to `_headers` file under `/`. Only advertise paths that exist.

### DNS-AID (DNS for AI Discovery, IETF draft)
SVCB/HTTPS (type 64/65) records at `_index._agents.<domain>`, `_mcp._agents.<domain>`, `_a2a._agents.<domain>` with alpn/endpoint params; DNSSEC-signed zone. Lets agents discover services before any HTTP request. Trivial to add in Cloudflare DNS once you HAVE an agent endpoint; meaningless without one. Verify via DoH: `https://cloudflare-dns.com/dns-query?name=_index._agents.example.com&type=SVCB` with `accept: application/dns-json`.

### API Catalog — RFC 9727
`/.well-known/api-catalog`, `Content-Type: application/linkset+json`:
```json
{"linkset":[{"anchor":"https://example.com/api","service-desc":[{"href":"https://example.com/openapi.json","type":"application/openapi+json"}],"service-doc":[{"href":"https://example.com/docs/api"}],"status":[{"href":"https://example.com/api/health"}]}]}
```
Ship only if a public API exists.

### OAuth/OIDC discovery (RFC 8414) + Protected Resource Metadata (RFC 9728) + auth.md
For sites with protected APIs agents should authenticate to: `/.well-known/oauth-authorization-server` (issuer, authorization_endpoint, token_endpoint, jwks_uri, grant_types_supported), `/.well-known/oauth-protected-resource` (resource, authorization_servers, scopes_supported), and human/agent-readable `/auth.md` (WorkOS convention) with registration instructions + `agent_auth` block (register_uri, identity/credential types). Required plumbing for any remote MCP server with auth; skip for brochure sites.

### MCP Server Card (SEP-1649 / PR 2127)
`/.well-known/mcp/server-card.json`: serverInfo (name, version), transport endpoint (streamable HTTP URL), capabilities (tools/resources/prompts). THE discovery hook for the MCP ecosystem. For SMBs the realistic path is Cloudflare **AI Search** (managed: index your site → instance exposes a built-in MCP endpoint + public search endpoint + embeddable UI snippets) — you get a legitimate MCP server for "search/ask this business" without writing one, then publish the card pointing at it. (AI Search instances after Apr 2026 include managed storage + web crawling of your site as a data source; also supports NLWeb.)

### Agent Skills index (Agent Skills Discovery RFC v0.2.0, Cloudflare)
`/.well-known/agent-skills/index.json` (legacy: `/.well-known/skills/index.json`): `$schema` + `skills` array, each {name, type, description, url, sha256 digest}. Publish downloadable skills teaching agents to use your service (e.g., "how to request a casting quote"). High-leverage for tool/SaaS vendors; optional for local SMBs.

### WebMCP (W3C Web Machine Learning CG / Chrome)
In-page JS: `navigator.modelContext.provideContext({tools:[{name, description, inputSchema, execute}]})` exposing site actions (request_quote, check_stock, book_slot) to browser-resident agents. Detected by scanners on page load. Early but cheap: a single quote-form tool is a real differentiator and converts agent visits into leads.

### Site search for agents — Cloudflare AI Search
Managed natural-language search over your content (Workers binding, REST, public endpoint, MCP). For agencies: deploy per-client instances ("ask this website anything") = instant layer-4 capability + the backing service for the MCP Server Card. NLWeb integration available.

---

## 3. LAYER 5 — AGENTIC COMMERCE (emerging; informational on most scanners, doesn't affect score yet)

- **Pay-Per-Crawl** (Cloudflare, private beta): respond 402 to AI crawlers; allow/charge/block per bot. The monetization counterpart to blocking.
- **x402** (Coinbase et al.): HTTP 402 payment flow middleware (@x402/express|hono|next + facilitator + wallet); agents pay per request autonomously.
- **MPP** (Machine Payment Protocol): `/openapi.json` with `x-payment-info` extensions per operation {intent: charge|session, method: tempo|stripe|lightning|card, amount, currency}; SDKs mppx/pympp.
- **UCP**: `/.well-known/ucp` profile (version, services, capabilities, endpoints).
- **ACP** (Agentic Commerce Protocol — OpenAI/Stripe lineage): `/.well-known/acp.json` {protocol:{name:"acp",version}, api_base_url, transports, capabilities.services}; lets ChatGPT-class agents discover checkout. **Watch this one for e-commerce clients** — when instant checkout via agents scales, early ACP adopters take the order flow.
- Strategy: layer 5 only after 1–4 are solid; for stores, ACP + Stripe is the pragmatic first move; x402/MPP for API products.

---

## 4. PRIORITY MATRIX (typical SMB/SME, e.g., a Thai factory site scoring "Level 1")

| Priority | Item | Effort | Score/impact |
|---|---|---|---|
| P0 | WAF/robots alignment — verify every major AI bot gets 200 | 1h | Unblocks everything |
| P0 | robots.txt: explicit AI rules + Content-Signal + Sitemap | 30m | Bot Access 2/2 |
| P0 | llms.txt (+ keep in sync) | 1h | Discoverability |
| P1 | Markdown for Agents toggle (Cloudflare) — review Content-Signal default | 15m | Content 1/1 |
| P1 | Link headers via `_headers` | 15m | Discoverability |
| P1 | Answer blocks + FAQ/LocalBusiness schema (layer 2 work) | days | Citations = revenue |
| P2 | Cloudflare AI Search instance → public ask endpoint + MCP Server Card | 0.5–1d | API/MCP from 0/7 → real capability |
| P2 | WebMCP quote/contact tool | 0.5d | Agent→lead conversion |
| P2 | DNS-AID records pointing at the MCP endpoint (DNSSEC on) | 30m | Discoverability 4/4 |
| P3 | Agent Skills index; auth.md/OAuth metadata if protected API exists | varies | Completeness |
| P3 | ACP/x402 if commerce | varies | Future order flow |

Expected movement on a 12-check agent-readiness rubric: Level 1 (~21) → Level 3+ (70+) with P0–P2 done.
