# Premium Engine — GPT-4.1 + Grok 3 Mini

**Marketplace fee:** $5/run  
**LLM:** platform OpenAI + xAI keys (user credits cover token cost)

## Pipeline routing

| Step | Model | Role |
|------|-------|------|
| `plan` | `gpt-4.1` | Deep exploration + numbered edit plan |
| `implement` | `gpt-4.1` | Complete code, tests, verify commands |
| `review` | `grok-3-mini` | Senior critique — independent of implementer |
| `qa` | `grok-3-mini` | Strict checklist + READY / NEEDS_CORRECTION |

## Why this split

- **GPT-4.1** — strong multi-file planning and implementation; worth the Pro tier cost.
- **Grok 3 Mini** — fast, skeptical second opinion for review/QA (different provider = fewer shared blind spots).

## Fallback order (Pro only)

1. Primary from `crew_config`
2. `gpt-4.1` → `gpt-4o` → `gpt-4o-mini`
3. `grok-3-mini` for review/qa steps

Skipped when provider API key is not configured.

## Required platform keys

`OPENAI_API_KEY` and `XAI_API_KEY` must be set on the server.