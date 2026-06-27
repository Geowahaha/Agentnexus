# Grok Skills — AgentNexus / OBOLLA

9arm-style buckets for this repo.

## framework

- **[obolla-workflow](obolla-workflow/SKILL.md)** — master OS for every task (9arm + loop + OBOLLA rules)

## engineering

- [loop-verifier](loop-verifier/SKILL.md) — checker; live verify after changes
- [loop-triage](loop-triage/SKILL.md) — daily triage → STATE.md
- [agent-ready-proof](agent-ready-proof/SKILL.md) — L1 proof on live URL
- [loop-budget](loop-budget/SKILL.md) — token caps

## domain (repo `skills/`)

- [isitagentready-one-stop](../../skills/isitagentready-one-stop/SKILL.md) — protocol Level 5

## Usage

```text
/obolla-workflow          # classify task + read STATE.md
/debug-mantra             # via obolla-workflow references
/agent-ready-proof        # L1 scan obolla.com
```

New skills: follow skill-creator pattern (`evals/evals.json`, `references/`, pushy description).