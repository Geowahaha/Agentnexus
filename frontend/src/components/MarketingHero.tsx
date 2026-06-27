import { Link } from 'react-router-dom'
import heroImage from '../assets/hero.png'
import { Fable5CreditsStrip } from './Fable5CreditsStrip'
import { FABLE5_LOCAL_SKILL_ID, FABLE5_PREMIUM_SKILL_ID } from '../config/featuredSkills'
import { FABLE5_LORA_HF_URL } from '../config/fable5Credits'

export function MarketingHero() {
  return (
    <section className="relative overflow-hidden rounded-2xl border border-[var(--color-border)] bg-gradient-to-br from-slate-900 via-[var(--color-surface-raised)] to-violet-950/40">
      <div className="grid gap-8 p-6 sm:p-10 lg:grid-cols-2 lg:items-center">
        <div>
          <h2 className="text-3xl font-bold tracking-tight text-white sm:text-4xl leading-tight">
            Fable-5 coding agents — local LoRA or cloud Pro
          </h2>
          <p className="mt-3 max-w-lg text-[var(--color-muted)]">
            <strong className="text-[var(--color-text-soft)]">Pro ($5):</strong> GPT-4.1 + Grok — no GPU.
            <br />
            <strong className="text-[var(--color-text-soft)]">Free:</strong>{' '}
            <a
              href={FABLE5_LORA_HF_URL}
              target="_blank"
              rel="noopener noreferrer"
              className="text-emerald-600 hover:text-emerald-700 underline underline-offset-2"
            >
              hotdogs/qwen3.6-27b-fable5-lora
            </a>{' '}
            on Ollama.
          </p>
          <div className="mt-3 max-w-lg">
            <Fable5CreditsStrip compact />
          </div>
          <div className="mt-6 flex flex-wrap gap-3">
            <Link
              to={`/expert-skills/${FABLE5_PREMIUM_SKILL_ID}`}
              className="rounded-lg bg-violet-500 px-5 py-3 text-sm font-bold text-slate-900 hover:bg-violet-400 shadow-lg shadow-violet-500/20"
            >
              Run Pro — $5
            </Link>
            <Link
              to={`/expert-skills/${FABLE5_LOCAL_SKILL_ID}`}
              className="rounded-lg border border-emerald-500/40 bg-emerald-500/10 px-5 py-3 text-sm font-semibold text-emerald-200 hover:bg-emerald-500/20"
            >
              Local LoRA — Free
            </Link>
          </div>
          <ul className="mt-5 flex flex-wrap gap-x-4 gap-y-1 text-xs text-[var(--color-muted)]">
            <li>✓ $5 free credits to start</li>
            <li>✓ Pro ≈ $5.18 total</li>
            <li>✓ Local tier $0 LLM</li>
          </ul>
        </div>
        <div className="relative hidden lg:block">
          <img
            src={heroImage}
            alt="OBOLLA agent flow marketplace preview"
            className="rounded-xl border border-white/10 shadow-2xl shadow-cyan-500/10"
          />
        </div>
      </div>
    </section>
  )
}