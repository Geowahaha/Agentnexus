---
name: agent-ready-proof
description: >
  L1 proof loop for OBOLLA Agent-Ready tools on a live URL (default obolla.com).
  Runs verify, analyze, fix-pack, and MCP apply (pack-only) without changing
  score formulas. Updates STATE.md and loop-run-log.md with evidence.
metadata:
  author: obolla
  bucket: engineering
  user-invocable: "true"
---

# Agent-Ready Proof Loop (L1)

Prove what OBOLLA tools can measure and deliver **before** tuning scores.

## Inputs

- Target URL (default: `https://obolla.com`)
- `STATE.md` baseline
- Optional: paid AIBotAuth JSON path for smart-scan

## Steps (execute in order; run commands yourself)

1. **Health** — `GET {url}/health`
2. **Verify** — `POST {url}/api/v1/agent-ready/verify` body `{"url":"...","max_attempts":1,"purge_between":false}`
3. **Analyze** — `POST {url}/api/v1/agent-ready/analyze` body `{"url":"..."}`
4. **Fix-pack** — `POST {url}/api/v1/agent-ready/fix-pack` body `{"url":"..."}` — record file list, do not deploy
5. **MCP** (optional) — `POST {url}/mcp` JSON-RPC `tools/call` for `apply_agent_ready_fix` without deploy tokens
6. **Smart-scan** (optional) — `POST /api/v1/agent-ready/smart-scan` with reference JSON if provided

## Output to STATE.md

Update `Last run` timestamp and proof table. Add High Priority items only for real blockers.

## Output to loop-run-log.md

Append JSON entry with `evidence` object from API responses.

## Hard rules

- **No** edits to `smart_scorecard.py`, `growth_scorecard.py`, or score weights
- **No** deploy unless human explicitly approved in the same session
- **No** claiming 100% protocol while `dnsAid` DNSSEC gap remains external
- Escalate paid scans, DNS registrar, and production deploy to human