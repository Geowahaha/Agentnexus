/** Attribution for the free local LoRA tier — links to upstream HuggingFace artifacts. */

export const FABLE5_LORA_HF_URL =
  'https://huggingface.co/hotdogs/qwen3.6-27b-fable5-lora'

export const FABLE5_TRACES_HF_URL =
  'https://huggingface.co/datasets/Glint-Research/Fable-5-traces'

export interface Fable5CreditLink {
  label: string
  href: string
  detail: string
}

export const FABLE5_LOCAL_CREDITS: Fable5CreditLink[] = [
  {
    label: 'hotdogs/qwen3.6-27b-fable5-lora',
    href: FABLE5_LORA_HF_URL,
    detail: 'GGUF LoRA adapter — what this free tier runs via Ollama',
  },
  {
    label: 'Glint-Research/Fable-5-traces',
    href: FABLE5_TRACES_HF_URL,
    detail: 'Agent trace dataset — playbook patterns are inspired by this corpus',
  },
]

export const FABLE5_LOCAL_CREDIT_LINE =
  'Free tier runs the hotdogs Fable-5 LoRA on your GPU (not a re-trained model). Playbook inspired by Glint Fable-5 traces.'