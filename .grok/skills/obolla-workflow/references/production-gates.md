# Production Gates

From `Agents.md`, `.production/PRODUCTION-RULES.md`, `docs/safety.md`.

## 24/7 rule

Anything blocking full feature use 24/7 must be fixed or moved to VPS — do not leave broken.

## DNSSEC / DNS-AID

- Fail because DNSSEC pending → reset Cloudflare DNSSEC **once** only
- Must re-enable immediately; then wait for parent DS publish
- Never leave DNSSEC `disabled`
- Helper: `node skills/isitagentready-one-stop/scripts/reset-cloudflare-dnssec-once.mjs --zone-id <id> --env-file <cf-env>`

## Denylist (human gate)

- `.env`, secrets, payment credentials
- `smart_scorecard.py`, `growth_scorecard.py` during L1 proof
- Auto-merge main
- Deploy without post-deploy health check

## MCP

- Public: `POST https://obolla.com/mcp` → `apply_agent_ready_fix`
- Deploy path needs customer `github_token` / `cf_api_token`