# OBOLLA Deploy Reference

## Edge (obolla.com)

```powershell
pwsh -NoProfile -File scripts/deploy-obolla.ps1
# or: npm run deploy:obolla
```

- Builds frontend → checks Worker token → OAuth fallback if scoped token fails → restores `.env` → smoke `/health`
- First OAuth: `npx wrangler login` (unset `CLOUDFLARE_API_TOKEN` in session first)

## Backend (VPS)

```powershell
pwsh -NoProfile -File scripts/deploy-vps-production.ps1
```

API + DB on `43.128.75.149` only. Never use Windows dev machine as production backend.

## Post-deploy (mandatory)

```powershell
Invoke-RestMethod https://obolla.com/health
```

Require `backend_reachable: true`.

If Agent-Ready files changed:

```powershell
Invoke-RestMethod -Uri https://obolla.com/api/v1/agent-ready/verify -Method POST -ContentType application/json -Body '{"url":"https://obolla.com","max_attempts":1}'
```

Record before/after in `loop-run-log.md`. Checker: `.grok/skills/loop-verifier`.