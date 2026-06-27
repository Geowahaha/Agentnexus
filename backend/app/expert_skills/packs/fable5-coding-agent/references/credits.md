# Credits — Free Local LoRA Tier

OBOLLA’s free Fable-5 agent flow runs the **upstream HuggingFace adapter** on your GPU via Ollama. We did not re-train this model; we orchestrate it with a marketplace playbook.

## Model adapter

- **[hotdogs/qwen3.6-27b-fable5-lora](https://huggingface.co/hotdogs/qwen3.6-27b-fable5-lora)** — Qwen3.6-27B + Fable-5 LoRA (GGUF for Ollama). All four pipeline steps use `qwen3.6-27b-fable5` when this tier is configured.

## Training / trace corpus

- **[Glint-Research/Fable-5-traces](https://huggingface.co/datasets/Glint-Research/Fable-5-traces)** — agent trace dataset. Our step prompts and deliverable format are **inspired by** patterns in this corpus (explore → plan → edit → verify).

## OBOLLA layer

- Marketplace playbook (plan → implement → review → QA)
- $0 run fee; $0 LLM when Ollama is enabled locally
- Optional Local Bridge for real Read/Grep/Bash on a paired machine

For cloud inference without a GPU, use **Fable-5 Coding Agent Pro** ($5) — GPT-4.1 + Grok 3 Mini; not the hotdogs LoRA weights.