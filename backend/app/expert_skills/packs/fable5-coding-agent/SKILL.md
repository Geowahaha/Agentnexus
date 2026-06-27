---
name: fable5-coding-agent
description: Local Fable-5 LoRA coding playbook inspired by Fable-5 trace patterns. Use when the user has Ollama + hotdogs/qwen3.6-27b-fable5-lora configured. Multi-step plan → implement → review → QA on local GPU ($0 run + $0 LLM).
---

# Fable-5 Coding Agent — Local LoRA (Free)

Runs **[hotdogs/qwen3.6-27b-fable5-lora](https://huggingface.co/hotdogs/qwen3.6-27b-fable5-lora)** on your GPU via Ollama for all four pipeline steps. Playbook patterns are inspired by **[Glint-Research/Fable-5-traces](https://huggingface.co/datasets/Glint-Research/Fable-5-traces)**. Full attribution: `references/credits.md`.

**No cloud fallback.** If Ollama is not configured, use **Fable-5 Coding Agent Pro** ($5) instead.

## Credits

| Upstream | Link |
|----------|------|
| LoRA adapter (runtime model) | [hotdogs/qwen3.6-27b-fable5-lora](https://huggingface.co/hotdogs/qwen3.6-27b-fable5-lora) |
| Trace dataset (playbook inspiration) | [Glint-Research/Fable-5-traces](https://huggingface.co/datasets/Glint-Research/Fable-5-traces) |

## Engine (local only)

| Step | Model | Output |
|------|-------|--------|
| Plan | `qwen3.6-27b-fable5` | Exploration notes + numbered plan |
| Implement | `qwen3.6-27b-fable5` | Full code / diffs + verify commands |
| Review | `qwen3.6-27b-fable5` | Score, issues, patches |
| QA | `qwen3.6-27b-fable5` | Checklist + READY verdict |

Setup: `references/local-ollama-setup.md`

## Agent loop

1. **Understand** — restate goal, constraints, stack, success criteria.
2. **Explore** — name files you would Read/Grep before editing.
3. **Plan** — numbered steps; files, functions, verify commands.
4. **Execute** — concrete code; small diffs over prose.
5. **Verify** — tests, lint, manual checks per change.
6. **Review + QA** — challenge correctness before delivery.

## Tool-use mindset

With Local Bridge paired, prefer real Read/Grep/Bash. Without Bridge, simulate exploration in the plan step. See `references/tool-use-patterns.md`.

## Marketplace deliverables

**Run fee: $0. LLM: $0 on local GPU.** See `references/marketplace-deliverables.md`.

## Language

Match the user's language (Thai/English). Code identifiers stay English unless the stack requires otherwise.