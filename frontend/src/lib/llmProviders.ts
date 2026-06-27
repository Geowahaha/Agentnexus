export type LlmProvider = 'gemini' | 'claude' | 'grok' | 'openai' | 'ollama'

export const LLM_PROVIDERS: Record<
  LlmProvider,
  { label: string; models: { id: string; label: string }[] }
> = {
  gemini: {
    label: 'Gemini',
    models: [
      { id: 'gemini-2.5-flash', label: 'Gemini 2.5 Flash (recommended)' },
      { id: 'gemini-2.5-flash-lite', label: 'Gemini 2.5 Flash Lite (fastest)' },
      { id: 'gemini-2.0-flash', label: 'Gemini 2.0 Flash (may need paid tier)' },
    ],
  },
  claude: {
    label: 'Claude',
    models: [
      { id: 'claude-haiku-4-5-20251001', label: 'Claude Haiku 4.5 (fast)' },
      { id: 'claude-sonnet-4-5-20250929', label: 'Claude Sonnet 4.5' },
      { id: 'claude-sonnet-4-6', label: 'Claude Sonnet 4.6' },
      { id: 'claude-opus-4-20250514', label: 'Claude Opus 4' },
    ],
  },
  grok: {
    label: 'Grok',
    models: [
      { id: 'grok-3-mini', label: 'Grok 3 Mini (fast)' },
      { id: 'grok-4.3', label: 'Grok 4.3' },
      { id: 'grok-4', label: 'Grok 4' },
    ],
  },
  openai: {
    label: 'OpenAI',
    models: [
      { id: 'gpt-4o-mini', label: 'GPT-4o Mini (fast)' },
      { id: 'gpt-4o', label: 'GPT-4o' },
      { id: 'gpt-4.1', label: 'GPT-4.1' },
      { id: 'gpt-5', label: 'GPT-5' },
    ],
  },
  ollama: {
    label: 'Local (Ollama)',
    models: [
      {
        id: 'qwen3.6-27b-fable5',
        label: 'hotdogs/qwen3.6-27b-fable5-lora (HF, local GPU)',
      },
    ],
  },
}

export function resolveProvider(model: string): LlmProvider {
  const normalized = model.toLowerCase()
  if (normalized.startsWith('ollama:') || normalized.startsWith('qwen3.6')) return 'ollama'
  if (normalized.startsWith('claude')) return 'claude'
  if (normalized.startsWith('gemini')) return 'gemini'
  if (normalized.startsWith('grok')) return 'grok'
  return 'openai'
}

export function providerForModel(model: string): LlmProvider {
  return resolveProvider(model)
}