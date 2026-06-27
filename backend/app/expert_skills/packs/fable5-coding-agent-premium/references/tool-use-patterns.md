# Fable-5 Tool-Use Patterns (Pro)

Patterns inspired by Fable-5 traces (82.9% tool_use sessions).

## Exploration first

```
1. Glob relevant paths (e.g. **/*.py, src/components/**)
2. Read top 2–3 files that own the behavior
3. Grep for symbols, routes, or error strings
```

Pro plan step must name concrete paths — not vague "check the codebase".

## Edit discipline

- One logical change per file when possible
- Preserve existing style
- Never invent APIs — note "verify in codebase" when unsure
- **Include tests** in implement unless user opts out

## Bash verification

End every implement step with concrete commands:

```bash
cd backend && python -m pytest tests/test_health.py -q
npm run build && npm test
```

## Pro quality gate

Implement step fails QA if: partial diffs with `...`, missing tests for new logic, or invented file paths.