---
name: fable5-coding-agent-premium
description: Premium cloud Fable-5-style coding agent ($5/run). Plan → implement → review → QA using OpenAI GPT-4.1 and Grok 3 Mini. For users without Ollama/GPU. Inspired by Fable-5 trace patterns — production-grade deliverables.
---

# Fable-5 Coding Agent Pro — Cloud Premium

For buyers **without a local GPU** or Ollama setup. A four-step pipeline inspired by [Fable-5 trace patterns](https://huggingface.co/datasets/Glint-Research/Fable-5-traces), tuned for **depth and copy-paste-ready output**.

## Engine (cloud)

| Step | Model | Output |
|------|-------|--------|
| Plan | GPT-4.1 | Deep exploration + executable plan |
| Implement | GPT-4.1 | Complete files/diffs + tests + verify commands |
| Review | Grok 3 Mini | Senior review — score, P0/P1/P2, patches |
| QA | Grok 3 Mini | Strict checklist + READY / NEEDS_CORRECTION |

Details: `references/premium-engine.md`

## Quality bar (Pro)

- **No `...` omissions** in code — full file contents or unified diffs.
- **Tests required** unless user explicitly opts out.
- **Verify commands** must be copy-paste ready from repo root.
- Review must cite file paths; QA must reject partial or invented code.

## Agent loop

Same as local tier: understand → explore → plan → execute → verify → review → QA. See `references/tool-use-patterns.md`.

## vs Free local tier

| | Free (Local LoRA) | Pro (Cloud) |
|--|-------------------|-------------|
| Model | qwen3.6-27b-fable5 | GPT-4.1 + Grok 3 Mini |
| GPU | Required | Not required |
| Run fee | $0 | $5 |
| Best for | Matching HF LoRA behavior | No-machine buyers |

## Marketplace deliverables

**Run fee: $5.** LLM tokens billed via platform credits. See `references/marketplace-deliverables.md`.