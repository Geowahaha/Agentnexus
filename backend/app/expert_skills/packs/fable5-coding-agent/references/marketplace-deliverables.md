# Fable-5 Coding Agent — Marketplace Deliverables

**Price:** $0/run marketplace fee. **LLM:** $0 on local GPU (`qwen3.6-27b-fable5` via Ollama). No cloud fallback. For cloud GPT-4.1 + Grok, use Pro tier ($5).

## Step: Planner Agent (`plan`)

Deliver:

1. **Goal restatement** — one paragraph
2. **Assumptions** — stack, repo layout, env limits
3. **Step plan** — numbered, each with file targets and verify command
4. **Risks** — what could fail + mitigation
5. **Out of scope** — explicit boundaries

## Step: Implementer Agent (`implement`)

Deliver:

1. **Changes summary** — bullet list of files touched
2. **Code blocks** — full file contents or unified diffs (no `...` omissions)
3. **Commands** — install, run, test (copy-paste ready)
4. **Notes** — breaking changes, migrations, env vars

## Step: Code Reviewer (`review`)

Deliver:

1. **Review score** — /10 with rationale
2. **Issues** — severity P0/P1/P2, file:line reference
3. **Security & edge cases** — short checklist
4. **Suggested patches** — for each P0/P1

## Step: QA Gate (`qa`)

Deliver:

1. **QA checklist** — PASS/FAIL/N/A per item (tests, types, lint, docs, no secrets)
2. **Verdict** — READY or NEEDS_CORRECTION
3. **Correction list** — if NEEDS_CORRECTION, exact fixes only

## Final report assembly

The platform concatenates all steps. QA verdict must appear in the last section.