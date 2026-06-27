# Scrutinize (9arm — adapted for OBOLLA)

Outsider review. Run in order.

## 1. Intent

- Goal in one sentence. If unclear → stop, say underspecified.
- **Mandatory:** Is there a simpler way? (do nothing, reuse existing, smaller change, different layer)
- Name the better alternative before line-by-line review if one exists.

## 2. Trace

- Follow entry → calls → branches → state → exit through **real code**, not just the diff.
- OBOLLA seams to watch: Worker proxy vs VPS API, analyze vs verify orchestrator, scorecard vs protocol scan.

## 3. Verify claims

For each claim: traced path holds? Edge cases? Silent behavior changes? Tests exercise the path?

## 4. Report

Per finding: **Finding** | **Why it matters** | **Evidence** | **Suggested change**

Close with one-line verdict: **ship / fix-then-ship / rework / reject** + biggest reason.

No rubber-stamps. Cite `file:line` or API response fields.