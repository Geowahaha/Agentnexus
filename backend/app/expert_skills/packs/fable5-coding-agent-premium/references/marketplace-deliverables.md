# Fable-5 Coding Agent Pro — Marketplace Deliverables

**Price:** $5/run marketplace fee. LLM tokens via user credits (GPT-4.1 + Grok 3 Mini).

## Step: Planner Agent (`plan`)

1. **Goal restatement** — one paragraph with success criteria
2. **Assumptions** — stack, repo layout, env limits
3. **Exploration notes** — files to Read/Grep and why (trace-style)
4. **Step plan** — numbered; each step has file targets + verify command
5. **Risks + mitigations**
6. **Out of scope**

## Step: Implementer Agent (`implement`)

1. **Changes summary** — files touched
2. **Code blocks** — complete files or unified diffs (no `...`)
3. **Test files** — included when applicable
4. **Commands** — install, run, test (copy-paste ready)
5. **Notes** — migrations, env vars, breaking changes

## Step: Code Reviewer (`review`)

1. **Review score** — /10 with rationale
2. **Issues** — P0/P1/P2 with file references
3. **Security & edge cases**
4. **Suggested patches** — for every P0/P1

## Step: QA Gate (`qa`)

1. **QA checklist** — PASS/FAIL/N/A (tests, types, lint, docs, no secrets)
2. **Verdict** — READY or NEEDS_CORRECTION
3. **Correction list** — exact fixes if NEEDS_CORRECTION