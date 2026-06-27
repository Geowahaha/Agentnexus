# Agent-Ready Auto Fix Pro — Deliverables

Paid run ($9.99) — buyer expects **deployable** output toward Level 5.

## Required sections

### 1. Before / After scorecard
- isitagentready category scores (from scan)
- Target: 100% per category after deploy
- Reference: successcasting.com 25% → 100%

### 2. Gap → file map
For each failing check: `check_id → file(s) → deploy path`

### 3. Full fix pack (complete contents)
| Layer | Files |
|-------|-------|
| Discoverability | robots.txt, sitemap note, Link header snippet, DNS-AID record spec |
| Content | Markdown negotiation route or CF toggle steps |
| Bot Access | Content-Signal in robots + `_headers` / `next.config` |
| Protocol | api-catalog JSON, oauth-*, auth.md, mcp/server-card, agent-skills/index, WebMCP hints |
| Commerce | ucp, acp.json, openapi.json, x402 /api/v1 route (if commerce signals) |

### 4. Stack deploy guide
Detect or ask: Next.js App Router · Cloudflare Pages · WordPress · static
- Exact paste paths per stack
- `purge cache` / `npm run build` / DNS steps

### 5. Re-verify commands
```bash
curl -sI https://SITE/api/v1   # x402: expect 402 + Payment-Required
node scripts/agent-ready-fix-generator.mjs https://SITE
POST https://isitagentready.com/api/scan
```

### 6. QA verdict
READY when: no placeholders, policies consistent, no fake endpoints, P0 gaps addressed in fix pack.

## Marketplace pricing footer (required)

- **Price:** $9.99/run + LLM via credits
- **Live clients:** successcasting.com (Level 5 reference) · pinpointaccountingservice.com ([proof 88/100](https://aibotauth.com/proof/pinpointaccountingservice-com-c902cb05afc4))
- **Upsell:** Growth Monitor ฿490/mo — unbranded proof + score-drop alerts
- See `packs/_shared/marketplace-pricing-copy.md`