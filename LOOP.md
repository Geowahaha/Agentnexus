# LOOP.md — AgentNexus / OBOLLA

This repo runs **loop engineering** ([cobusgreyling/loop-engineering](https://github.com/cobusgreyling/loop-engineering)) alongside OBOLLA Agent-Ready tooling.

**Core shift:** stop one-shot prompting; design loops that scan → act → verify → record until the goal is met or a human gate fires.

## Active Loops

| Pattern | Cadence | Phase | Goal |
|---------|---------|-------|------|
| **Agent-Ready Proof** (obolla.com) | on-demand / 1d | **L1 report-only** | Prove what MCP + API tools can measure/fix before any score-formula changes |
| Daily Triage | 1d | L1 report-only | CI, deploy health, open gaps from `STATE.md` |

### Agent-Ready Proof Loop (primary — week 1)

**Single goal:** Document what `https://obolla.com` Agent-Ready tools can *prove* with live evidence.

**Non-goals (locked until proof complete):**
- Do **not** change smart/growth score weights or formulas
- Do **not** auto-deploy without human approval or scoped tokens
- Do **not** claim 100% while DNS-AID waits on registrar DS propagation

**Cycle (L1):**
1. Read `STATE.md` + prior `loop-run-log.md`
2. Run live checks (shell/API, not guesses):
   - `GET https://obolla.com/health` → `backend_reachable: true`
   - `POST /api/v1/agent-ready/verify` → isitagentready pass/fail + gaps
   - `POST /api/v1/agent-ready/analyze` → stack + layered scores (read-only)
   - `POST /api/v1/agent-ready/fix-pack` → files generated (no deploy)
   - `POST https://obolla.com/mcp` → `apply_agent_ready_fix` (pack only if no tokens)
3. Append evidence to `loop-run-log.md`; update `STATE.md`
4. Escalate to human if deploy, DNSSEC reset, or paid AIBotAuth scan needed

**Cycle (L2 — after L1 proof):**
1. Maker: apply fix pack in worktree or via MCP with customer tokens
2. Deploy: `scripts/deploy-obolla.ps1` / `scripts/deploy-vps-production.ps1`
3. Checker (`loop-verifier`): re-run verify + health; compare delta to `STATE.md` baseline
4. Log revenue moat if apply succeeded

**Cycle (L3 — later):** unattended apply + deploy + verify with scoped tokens and denylist gates.

## Human Gates

- DNSSEC / DNS-AID registrar steps (reset-once only; see `Agents.md`)
- Production deploy (edge + VPS)
- GitHub / Cloudflare tokens and customer credentials
- Any change to scoring logic (`smart_scorecard.py`, `growth_scorecard.py`)
- Auto-merge: **never** on main

## Maker / Checker

- **Maker:** implementer agent or `apply_agent_ready_fix` MCP
- **Checker:** `loop-verifier` skill — must re-run live verify/health; implementer cannot mark done alone

## Connectors (MCP)

- `https://obolla.com/mcp` — `apply_agent_ready_fix` (public JSON-RPC)
- Cloudflare MCP (optional) — DNS-AID / purge when tokens available
- GitHub MCP (optional) — PR apply path

## Worktrees

- Unattended code experiments: one git worktree per fix attempt; discard on verifier REJECT

## Budget & Observability

- Caps: `loop-budget.md`
- History: `loop-run-log.md`
- Estimate: `npx @cobusgreyling/loop-cost --pattern daily-triage --level L1`
- Kill switch: `loop-pause-all` in `STATE.md` or issue label

## Skills

| Skill | Role |
|-------|------|
| **`.grok/skills/obolla-workflow`** | **Master framework — เริ่มที่นี่ทุก session** |
| `skills/isitagentready-one-stop` | Protocol Level 5 / discovery files |
| `.grok/skills/loop-triage` | Daily engineering triage |
| `.grok/skills/agent-ready-proof` | OBOLLA proof-loop steps |
| `.grok/skills/loop-verifier` | Post-change live verification |
| `.grok/skills/loop-budget` | Token cap checks |

## Commands (Grok)

```text
/loop 1d Run agent-ready-proof for https://obolla.com. L1 only: verify + analyze + fix-pack preview. Update STATE.md and loop-run-log.md. No score formula edits. No deploy without human gate.
```

## Links

- [loop-design-checklist](https://github.com/cobusgreyling/loop-engineering/blob/main/docs/loop-design-checklist.md)
- [daily-triage pattern](https://github.com/cobusgreyling/loop-engineering/blob/main/patterns/daily-triage.md)
- OBOLLA deploy: `scripts/deploy-obolla.ps1`, `scripts/deploy-vps-production.ps1`