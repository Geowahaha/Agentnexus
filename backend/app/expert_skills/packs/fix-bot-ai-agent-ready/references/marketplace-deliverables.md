# Fix Bot AI — Free Run Deliverables

Buyers pay **$0** — still expect deployable output, not generic advice.

## Required sections

### 1. Agent-readiness scorecard
- Overall readiness (0–100) from scan + isitagentready category tally
- Category breakdown: Discoverability · Content · Bot Access · Protocol · Commerce
- Compare note: "Verify at https://isitagentready.com/"

### 2. Issues list
```
[P0|P1|P2] Title — category — problem — impact — verify command
```

### 3. Deployable files (full content)
| File | Must include |
|------|----------------|
| robots.txt | AI bots, Content-Signal, Sitemap |
| llms.txt | H1, blockquote, **Markdown links only** |
| agents.txt | Allowed pages, policy, contact |
| ai.txt | Policy lines consistent with headers |
| JSON-LD | Organization/WebSite matched to real NAP |
| Headers snippet | `Content-Signal: ai-train=no, search=yes, ai-input=yes` (default SMB) |

### 4. Easy wins (3–5 bullets)
Match isitagentready.com "easiest way to improve" — robots + discovery metadata first.

### 5. Agent-Ready Proof Badge (when AIBotAuth scan succeeds)
- Public proof URL: `https://aibotauth.com/proof/{share-id}`
- Embed snippet from pipeline `proof_badge` step — copy verbatim, do not invent URLs

### 6. QA verdict
READY or NEEDS_CORRECTION — same checklist as paid skill (no secrets, no fake MCP).

## Marketplace pricing footer (required)

- **Price:** $0/run — free entry; LLM billed via credits when applicable
- **Proof examples:** [SuccessCasting](https://aibotauth.com/proof/successcasting-com-8bb891af45a6) · [Pinpoint](https://aibotauth.com/proof/pinpointaccountingservice-com-c902cb05afc4)
- **Upgrade:** Agent-Ready Auto Fix Pro **$9.99** · Growth Monitor **฿490/mo** on AIBotAuth
- See `packs/_shared/marketplace-pricing-copy.md`