# Phase 2 — Auto Deploy

## API (OBOLLA backend)

| Endpoint | Purpose |
|----------|---------|
| `POST /api/v1/agent-ready/analyze` | Stack fingerprint + isitagentready + deploy plan |
| `POST /api/v1/agent-ready/verify` | Re-scan loop (optional CF purge between attempts) |
| `POST /api/v1/agent-ready/cloudflare/purge` | Purge agent paths on Cloudflare |

## CLI

```bash
node scripts/agent-ready-auto-deploy.mjs https://yoursite.com
node scripts/agent-ready-auto-deploy.mjs https://yoursite.com --verify-only
```

Output: `.agent-ready-out/<host>/` with fix files + analyze.json + verify.json

## Server env (VPS)

```
CLOUDFLARE_API_TOKEN=...   # Cache Purge + Zone Read
CLOUDFLARE_ZONE_ID=...     # optional — auto-resolved from URL
```

## Honest automation boundary

| Automated | Buyer / ops step |
|-----------|------------------|
| Stack detect | Paste files into repo / hosting |
| Fix pack generate | `npm run build` + restart |
| isitagentready verify loop | DNS-AID in DNS panel |
| CF cache purge (when token set) | x402 wallet, OAuth secrets |

Target: deploy fix pack → `--verify-only` until 95%+ (or 100% with commerce).