# Local Ollama + Qwen3.6-27B Fable-5 LoRA

Run the upstream [hotdogs/qwen3.6-27b-fable5-lora](https://huggingface.co/hotdogs/qwen3.6-27b-fable5-lora) adapter on your machine for **$0 inference** in OBOLLA. See `credits.md` for full attribution (trace dataset: [Glint-Research/Fable-5-traces](https://huggingface.co/datasets/Glint-Research/Fable-5-traces)).

## Requirements

- NVIDIA GPU ~24GB VRAM (RTX 4090 class), or CPU/GGUF via llama.cpp (slower)
- [Ollama](https://ollama.com) installed
- Hugging Face account (accept model terms to download LoRA)

## Option A — GGUF + llama.cpp (from model card)

```bash
# Base model (example — use your preferred Qwen3.6-27B quant)
wget -O base.gguf <your-qwen3.6-27b-q4_k_m.gguf>
wget -O lora.gguf https://huggingface.co/hotdogs/qwen3.6-27b-fable5-lora/resolve/main/GGUF/qwen36-fable5-lora.gguf
./llama-server -m base.gguf --lora lora.gguf --port 8080
```

Point AgentNexus at an OpenAI-compatible endpoint if you expose llama-server that way, or use Ollama import below.

## Option B — Ollama (recommended for AgentNexus)

1. Pull or import a Qwen3.6-27B base into Ollama (community GGUF).
2. Create `Modelfile`:

```
FROM qwen3.6-27b
ADAPTER ./qwen36-fable5-lora.gguf
PARAMETER temperature 0.7
PARAMETER top_p 0.9
```

3. Build:

```bash
ollama create qwen3.6-27b-fable5 -f Modelfile
ollama run qwen3.6-27b-fable5 "Say hello"
```

4. Backend `.env`:

```
OLLAMA_ENABLED=true
OLLAMA_BASE_URL=http://127.0.0.1:11434
```

5. Restart FastAPI — Fable-5 skill steps using `qwen3.6-27b-fable5` hit your local GPU.

## Fallback

If Ollama is down, AgentNexus falls back to Gemini/Grok (cloud API keys required).