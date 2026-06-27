# "If I build a new website TODAY" — Day-One Blueprint (2026)

Use this when a user starts a new site (or relaunches) and wants it born AI-visible. Output a concrete build plan with the actual files. Order matters: foundation → access → citation content → agent layer.

## Phase 0 — Decisions before code
1. **One canonical host** (pick `www` or apex, 301 the other; the redirect chain in scan results costs trust and crawl budget).
2. **Entity identity locked:** exact business name, address, phone, hours, geo — written once, reused EVERYWHERE (site footer, schema, Google Business Profile, Facebook, LINE OA, directories). NAP inconsistency is a hard E-E-A-T penalty.
3. **Stack:** static-first (Astro/Eleventy/plain HTML on Cloudflare Pages or equivalent CDN). Server-rendered HTML — AI crawlers don't reliably execute JS; content must exist in the initial HTML response. Real text, never text-in-images (product specs as images are invisible to every layer).
4. **Language:** primary market language first-class (e.g., Thai), English as secondary with hreflang — AI engines answer in the asker's language from same-language sources.

## Phase 1 — Foundation (classic SEO, day 1)
- HTTPS + HSTS; mobile viewport; <2.5s LCP (compress images to WebP/AVIF, minimal JS).
- Per page: unique `<title>` ≤60 chars, meta description 140–160, exactly one H1, logical H2/H3 (phrased as buyer questions where natural), canonical tag, descriptive alt text on every image.
- `sitemap.xml` referenced from robots.txt; submit to Google Search Console + Bing Webmaster (Bing feeds ChatGPT/Copilot — do not skip Bing).
- JSON-LD in every page head: `LocalBusiness`/`Organization` (full NAP, geo, openingHours, `sameAs` to all profiles), plus `FAQPage` on pages with answer blocks, `Product`/`Service` with real specs, `Article` with author + dates.

## Phase 2 — Access files (day 1, copy-paste from agent-readiness.md §1)
- robots.txt with explicit AI-bot rules + `Content-Signal` + Sitemap line.
- `/llms.txt` curated map; plan `/llms-full.txt` when content volume justifies.
- Verify WAF/bot settings allow the AI roster (test fetch per UA).
- `_headers` (or server config): security headers + `Link:` rel="llms-txt" (add api-catalog later if/when an API exists).
- Enable Markdown for Agents if on Cloudflare (review Content-Signal default).

## Phase 3 — Citation content (weeks 1–4, the revenue layer)
- Every commercial page: 3–7 answer blocks (formula in ai-overviews-geo.md) targeting real buyer questions in the buyer's words.
- One **proof asset** per service: original photos, real numbers (capacity, tolerances, lead times, prices/ranges), named people. First-hand specificity is the moat — commodity text gets filtered.
- Author/About pages with credentials; visible "Updated" dates with a real update cadence (refresh top pages quarterly — <3-month-old content cites ~3× more).
- 5–10 citation-probe questions written down on launch day = your baseline scoreboard.

## Phase 4 — Agent layer (month 2)
- Cloudflare AI Search instance over the site → public ask endpoint → publish MCP Server Card at `/.well-known/mcp/server-card.json`.
- WebMCP tool for the #1 conversion action (quote request / booking).
- DNS-AID SVCB records (`_index._agents`, `_mcp._agents`) pointing at the live endpoint; enable DNSSEC.
- Optional: Agent Skills index; ACP discovery if e-commerce.

## Launch-day verification checklist (the proof)
```
curl -s https://site/robots.txt            # AI rules + Content-Signal + Sitemap present
curl -s https://site/llms.txt              # 200, valid markdown map
curl -sI https://site/ | grep -i link      # Link headers
curl -sH "Accept: text/markdown" https://site/ -D- | grep -i content-type   # text/markdown
curl -sA "GPTBot" -o /dev/null -w "%{http_code}" https://site/              # 200 not 403 (repeat per bot UA)
```
Then: run an agent-readiness scan (target Level 3+), Rich Results test for schema, PSI mobile ≥85, and the citation-probe baseline.

## Anti-patterns (refuse to build these)
- JS-only rendering of core content; specs as images; PDF-only product data.
- Doorway/AI-spun page farms; fake authors; schema describing content that isn't visibly on the page.
- Discovery files pointing at dead endpoints (worse than absent).
- Blocking all AI bots "for safety" on a business that lives on being found.
