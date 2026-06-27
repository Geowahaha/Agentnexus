# AgentNexus Marketplace Run — Deliverables & QA (AI Visibility Audit 2026)

Use this reference for every paid marketplace run. Buyers pay $2.50 per run and expect **measurable, deployable output** — not generic SEO advice.

## Buyer deliverables (all runs)

Every completed run must include these sections in the final output:

### 1. Visibility scorecard
- Overall score (0–100) from the deterministic AIBotAuth scan
- Layer breakdown: Discovery · Access · Structure · Trust · Agent-ready (each /20)
- One-line interpretation (e.g., "Strong baseline" / "Access blockers cap citation potential")

### 2. Issues list with severity
Format each finding as:
```
[P0|P1|P2] Short title — Layer N — What is wrong — Why it matters for AI bots — How to verify
```
- **P0** = blocks AI crawlers or returns errors (WAF/robots mismatch, HTTP 401/403/522, missing llms.txt when agents expect it)
- **P1** = hurts citation/agent discovery (bare URLs in llms.txt, missing JSON-LD, wrong Content-Signal, LCP/render-delay hiding hero content from scanners)
- **P2** = polish (Link headers, well-known endpoints, freshness signals)

### 3. Deployable fix files (paste-ready)
Ship complete file contents, not placeholders:

| File | Location | Must include |
|---|---|---|
| `robots.txt` | site root | Explicit AI bot rules (GPTBot, ClaudeBot, PerplexityBot, OAI-SearchBot, Google-Extended), `Content-Signal`, Sitemap |
| `llms.txt` | `/llms.txt` | H1 site name, blockquote summary, sections with **Markdown links** `[Title](url): description` — never bare URLs only |
| JSON-LD | homepage `<script type="application/ld+json">` | Organization + WebSite (or LocalBusiness/ProfessionalService for service sites) matched to actual NAP |
| `_headers` | Cloudflare Pages root (if applicable) | `Content-Signal: search=yes, ai-input=yes` (+ `ai-train=no` if client withholds training), security headers |

### 4. Actionable recommendations
3–7 bullets the buyer can do this week without a developer (GSC/Bing verification, update dates, answer-block content, CF AI Crawl Control check).

### 5. Agent-Ready Proof Badge (required when scan succeeds)
Every run that completes an AIBotAuth scan must surface the public proof artifact:

- **Public proof URL** — `https://aibotauth.com/proof/{share-id}` (shareable, no login)
- **Score line** — overall /100 + grade from the deterministic scan (must match scan output)
- **Embed snippet** — paste-ready `<script src="https://aibotauth.com/embed/badge.js" data-proof="…">` block

If the pipeline attached `proof_badge` in prior steps, copy it verbatim into the final report. Do not invent proof URLs.

Strategy reference: AIBotAuth co-founder roadmap (`COFOUNDER_ROADMAP.md` in visibility-engine) — wedge = Proof + Monitoring, not generic SEO advice.

## Marketplace pricing footer (required on every paid run)

Copy from `packs/_shared/marketplace-pricing-copy.md` or:

- **Price:** $2.50/run + ~$0.12 LLM (~$2.62 total)
- **Live proof on file:** [SuccessCasting 88/100](https://aibotauth.com/proof/successcasting-com-8bb891af45a6) · [Pinpoint 88/100](https://aibotauth.com/proof/pinpointaccountingservice-com-c902cb05afc4)
- **Upsell:** Growth Monitor ฿490/mo at [aibotauth.com/dashboard.html](https://aibotauth.com/dashboard.html)
- **Honest scope:** No ranking, citation, or revenue guarantees.

### 6. Before → After projection
When fixes are applied, show expected bot status changes:

| Bot | Before (from scan) | After (expected) |
|---|---|---|
| GPTBot | blocked / served / can read | can read |
| ClaudeBot | … | … |
| PerplexityBot | … | … |
| OAI-SearchBot | … | … |

Use scan data for "Before"; infer "After" only for fixes you actually shipped in the fix pack.

## QA checklist (Grok QA step — must verify before delivery)

Mark each item PASS / FAIL / N/A:

1. **Scan integrity** — Scores cited match scan output; no invented layer numbers
2. **Access honesty** — If HTTP 401/403/522, banner says "limited audit" and P0 focuses on access
3. **robots.txt** — Valid syntax; explicit AI UAs; Content-Signal present; matches WAF intent
4. **llms.txt** — Uses Markdown link syntax; no `ai-input=no` unless buyer explicitly wants it; syncs with real pages
5. **JSON-LD** — Valid JSON; entity matches site name/URL; no fake addresses or phone numbers
6. **No overclaims** — No MCP Server Card / API Catalog unless site has those endpoints
7. **No secrets** — No API tokens, CF tokens, SSH keys, or env values in output
8. **Localization** — `.th` / Thai content sites: recommendations mention Thai market context where relevant

If any P0-related item FAILs, QA must list corrections the Fix Pack Generator should apply.

## Common 2026 fixes (from production audits)

These patterns recur in real client work — check every site:

### llms.txt: bare URLs → Markdown links
**Bad:** `https://example.com/about — About us`
**Good:** `[About Us](https://example.com/about): Company background and team.`

Scanners and agents parse Markdown links reliably; bare URL lines score lower on Structure layer.

### Content-Signal alignment
robots.txt and CDN `_headers` must agree:
```
Content-Signal: search=yes, ai-input=yes, ai-train=no
```
`ai-input=yes` lets agents use site content at inference (RAG/citations). Mismatch between robots.txt and edge headers is a P0 trust failure.

### WAF vs robots.txt hypocrisy
robots.txt `Allow: /` for GPTBot but Cloudflare Bot Fight Mode returning 403 = silent P0. Recommend CF AI Crawl Control per-bot allow + Security Events check.

### Render-delay / LCP hiding content
Scroll-reveal animations on hero copy cause scanners to see empty `<p>` tags — hurts Structure and Trust. Fix: exclude above-fold hero from reveal scripts; move heavy JSON-LD to end of `<body>`.

### JSON-LD placement
Large inline JSON-LD in `<head>` blocks first paint. Prefer end of `<body>` or single compact graph; keep HTML canonical.

### www / apex consistency
HTTP 522 on www while apex works = P0 access failure. Fix: add www as hosting custom domain or 301 redirect at CDN.

## Partial-scan runs (WAF-blocked sites)

When scan returns 401/403:
- Still deliver template robots.txt, llms.txt, JSON-LD based on public signals (site name from URL, industry guess from title if fetchable)
- Lead with honest "Scan access limited" banner
- P0 = unblock scanner UAs in WAF
- Do not fabricate layer scores — say "scores unavailable; estimated fixes below"