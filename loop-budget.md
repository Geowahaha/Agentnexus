# Loop Budget — AgentNexus / OBOLLA

> Primary loops: **Agent-Ready Proof** (on-demand) + **Daily Triage** (1d)

## Daily limits

| Loop | Max runs/day | Max tokens/day | Max sub-agent spawns/run |
|------|--------------|----------------|--------------------------|
| Agent-Ready Proof | 4 | 150k | 1 verifier (L2+) |
| Daily Triage | 2 | 100k | 0 (L1) / 2 (L2) |

## On budget exceed

1. Pause schedulers or stop proof runs
2. Append event to `loop-run-log.md`
3. Add note under High Priority in `STATE.md`

## Kill switch

- Label or flag: `loop-pause-all` in `STATE.md`
- Resume only after human clears the flag

## Estimate spend

```bash
npx @cobusgreyling/loop-cost --pattern daily-triage --level L1
```