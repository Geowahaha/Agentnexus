# Loop Safety — AgentNexus / OBOLLA

## Denylist (human gate required)

- `.env`, secrets, API tokens, `wrangler` secrets
- Payment / Stripe / x402 production credentials
- DNSSEC reset (max once; must re-enable — see `Agents.md`)
- Changes to `smart_scorecard.py`, `growth_scorecard.py` during L1 proof
- Auto-merge to `main`
- Production deploy without `backend_reachable: true` check after

## Allowlist (L2+ with verifier)

- Agent-ready discovery files in `public/` or Worker routes
- Fix-pack markdown generators (no deploy)
- Docs: `STATE.md`, `loop-run-log.md`, `LOOP.md`

## MCP scopes

- `https://obolla.com/mcp`: read + `apply_agent_ready_fix` pack generation
- Write/deploy connectors: customer-supplied tokens only

## Verifier requirements

- Re-run `https://obolla.com/health`
- Re-run `POST /api/v1/agent-ready/verify` for protocol claims
- Implementer session ≠ verifier session

## Auto-merge policy

**Never** auto-merge. All production changes via human-reviewed deploy scripts.