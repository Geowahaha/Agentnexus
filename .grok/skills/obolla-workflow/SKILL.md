---
name: obolla-workflow
description: >
  Master working framework for AgentNexus / OBOLLA. Use this skill for EVERY
  engineering task in this repo — bug fixes, deploys, Agent-Ready scans, MCP,
  feature work, reviews, and long multi-step sessions. Combines 9arm-skills
  discipline (debug-mantra, scrutinize, stay-on-track) with loop-engineering
  (STATE.md, verifier, L1→L3) and OBOLLA production rules. Trigger on
  /obolla-workflow, when the user says work is not going well, asks for a
  better process, starts any OBOLLA task, deploy, agent-ready, or debug session.
metadata:
  author: obolla
  bucket: framework
  user-invocable: "true"
compatibility: Grok Build; requires shell, network, and AgentNexus repo access.
---

# OBOLLA Workflow — Master Framework

You are working in **AgentNexus / OBOLLA**. This skill is the **default operating system** for every session. Read `Agents.md`, `LOOP.md`, and `STATE.md` at session start when the task touches production or Agent-Ready.

## Session open (every task)

1. Read `STATE.md` — know the frozen baseline and open items.
2. Classify the task:

| Type | Sub-skill / reference |
|------|----------------------|
| Bug / error / broken | `references/debug-mantra.md` — recite mantra, 4 steps |
| Review plan / PR / change | `references/scrutinize.md` |
| Agent-Ready / obolla.com scan | `.grok/skills/agent-ready-proof` |
| Post-fix documentation | `references/post-mortem.md` |
| Deploy edge or VPS | `references/deploy.md` |
| Long session / stuck / repeating | **Stay on track** (below) |

3. State the **one-sentence goal** and **phase** (L1 report / L2 fix+verify / L3 unattended).

## Stay on track (from 9arm qwenchance)

Before **each step**, check:

| Check | Trigger | Action |
|-------|---------|--------|
| Looping? | Re-read unchanged file, re-run same command, revisit dropped hypothesis | Stop — ask one sharp question or try a different action |
| Over-thinking? | >1000 words reasoning without acting | Act on best decision or ask user one question |
| Context tight? | 20+ turns, 5+ files read, 3+ steps left | Finish current step, update `STATE.md` + `loop-run-log.md`, hand off |

**Retry cap:** same failing command max **2** attempts (3rd → stop, escalate).  
**Edit rule:** read enough → one edit → verify before next edit.

## Execute — OBOLLA non-negotiables

From `Agents.md` — always:

1. **Run commands yourself** — never tell the user to run without trying first.
2. **Workaround before giving up** — OAuth vs scoped token, `deploy-obolla.ps1`, etc.
3. **Production split** — Edge = Cloudflare Worker (`obolla.com`); API/DB = VPS `43.128.75.149` only.
4. **Close with evidence** — `https://obolla.com/health` → `backend_reachable: true` after deploy.
5. **Permanent fixes → `scripts/`** — repeatable workarounds become scripts.

## Loop engineering (every meaningful run)

```
Read STATE.md → Act (maker) → Verify live (checker) → Append loop-run-log.md → Update STATE.md
```

| Phase | Allowed | Forbidden |
|-------|---------|-----------|
| **L1** | scan, analyze, fix-pack preview, MCP pack-only | deploy, score formula edits |
| **L2** | one scoped fix + deploy + `loop-verifier` | auto-merge, batch risky changes |
| **L3** | unattended with scoped tokens + `docs/safety.md` denylist | DNSSEC abuse, secrets in chat |

**Checker rule:** implementer cannot mark work done. Re-run health + verify before claiming improvement.

**Score freeze:** do not edit `smart_scorecard.py` / `growth_scorecard.py` until L2 proves a live delta on `STATE.md` baseline.

## Task workflows

### A. Agent-Ready / customer site

1. L1: run `.grok/skills/agent-ready-proof` steps on live URL.
2. Record evidence in `loop-run-log.md` (JSON block).
3. Human gate: deploy, DNSSEC reset-once, paid AIBotAuth JSON.
4. L2: apply **one** P0 fix → `scripts/deploy-obolla.ps1` or VPS script → `.grok/skills/loop-verifier`.
5. Compare before/after vs `STATE.md` — do not conflate protocol % with smart/growth %.

Protocol skill: `skills/isitagentready-one-stop/SKILL.md`

### B. Bug fix

1. Load `references/debug-mantra.md` — recite mantra verbatim in first response.
2. Repro → fail path → falsify hypothesis → breadcrumb ledger.
3. Fix only after reliable repro exists.
4. Deploy if production-affecting; verify with health check.
5. Offer `references/post-mortem.md` if non-trivial.

### C. Code / plan review

1. Load `references/scrutinize.md`.
2. Intent (simpler alternative?) → trace end-to-end → verify claims → report with verdict.
3. Verdict: ship / fix-then-ship / rework / reject.

### D. Deploy

1. Load `references/deploy.md`.
2. Edge: `pwsh -NoProfile -File scripts/deploy-obolla.ps1`
3. Backend: `pwsh -NoProfile -File scripts/deploy-vps-production.ps1`
4. Smoke: `GET https://obolla.com/health`
5. Agent-Ready deploy: re-run verify if discovery files changed.

## Human gates (always escalate)

- DNSSEC / DNS-AID registrar (reset once only; keep enabled)
- Production deploy without approval
- Customer GitHub / Cloudflare tokens
- Score formula or weight changes
- Auto-merge to main

## Session close (every task)

Update durable artifacts:

- `STATE.md` — last run time, high priority, baseline deltas
- `loop-run-log.md` — append JSON run entry
- If fix landed: offer post-mortem draft

## Slash commands

| Command | Action |
|---------|--------|
| `/obolla-workflow` | Open framework; classify task; read STATE |
| `/debug-mantra` | Bug path — mantra + 4 steps |
| `/scrutinize` | Review path |
| `/agent-ready-proof` | L1 proof on obolla.com or given URL |

## Skill bucket map (9arm-style)

| Bucket | Skills in this repo |
|--------|---------------------|
| **framework** | `obolla-workflow` (this) |
| **engineering** | `loop-verifier`, `loop-triage`, `agent-ready-proof` |
| **domain** | `skills/isitagentready-one-stop` |
| **loop** | `loop-budget`, loop-engineering files |

When creating new skills, load **`skills/skill-creator/SKILL.md`** (Anthropic official). Validate with `python skills/skill-creator/scripts/quick_validate.py <skill-dir>`. Template: `skills/template-SKILL.md`. Spec: `skills/AGENT-SKILLS-SPEC.md`.