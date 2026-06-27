# Fable-5 Tool-Use Patterns

Patterns distilled from Fable-5 traces (82.9% tool_use sessions).

## Exploration first

Before editing, an agent should:

```
1. Glob relevant paths (e.g. **/*.py, src/components/**)
2. Read top 2–3 files that own the behavior
3. Grep for symbols, routes, or error strings
```

Output in plan step: "I would Read `path/to/file` because …"

## Edit discipline

- One logical change per file when possible
- Preserve existing style (imports, naming, formatter)
- Never invent APIs — if unsure, note "verify in codebase"

## Bash verification

End every implement step with concrete commands:

```bash
cd backend && python -m pytest scripts/test_expert_skill_prompts.py -q
npm run build
```

## CoT blocks (internal)

Reason briefly, then act. Marketplace output should **not** dump raw chain-of-thought — only decisions and artifacts.

## Multi-step tasks

Split into: data model → API → UI → tests. Do not skip tests for "speed" unless user explicitly opts out.