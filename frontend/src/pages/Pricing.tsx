import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../api/client'
import { Fable5CreditsStrip } from '../components/Fable5CreditsStrip'
import { useLocale } from '../context/LocaleContext'
import {
  AI_VISIBILITY_SKILL_ID,
  FABLE5_LOCAL_SKILL_ID,
  FABLE5_PREMIUM_SKILL_ID,
  FIX_BOT_AI_SKILL_ID,
} from '../config/featuredSkills'
import type { BillingConfig } from '../types'
import type { Locale } from '../i18n/strings'

type IncludeItem = { label: string; detail: string }

const FABLE5_PRO_INCLUDES_EN: IncludeItem[] = [
  { label: 'Deep plan', detail: 'GPT-4.1 exploration map + numbered steps + tests' },
  { label: 'Production code', detail: 'Complete files/diffs + verify commands' },
  { label: 'Senior review', detail: 'Grok 3 Mini — P0/P1/P2 + patch blocks' },
  { label: 'Strict QA', detail: 'READY only if paste-and-run quality' },
]

const FABLE5_PRO_INCLUDES_TH: IncludeItem[] = [
  { label: 'แผนลึก', detail: 'GPT-4.1 สำรวจโค้ด + ขั้นตอนเลข + ชุดทดสอบ' },
  { label: 'โค้ดพร้อมใช้', detail: 'ไฟล์/diff ครบ + คำสั่ง verify' },
  { label: 'รีวิวระดับ senior', detail: 'Grok 3 Mini — P0/P1/P2 + patch blocks' },
  { label: 'QA เข้ม', detail: 'READY เมื่อคุณภาพ paste-and-run ผ่านจริง' },
]

const FABLE5_LOCAL_INCLUDES_EN: IncludeItem[] = [
  {
    label: 'Upstream LoRA',
    detail: 'hotdogs/qwen3.6-27b-fable5-lora — same weights as HuggingFace GGUF',
  },
  { label: '4-step pipeline', detail: 'Plan → implement → review → QA on GPU' },
  { label: '$0 LLM', detail: 'No cloud tokens when Ollama is configured' },
  {
    label: 'Trace playbook',
    detail: 'Step format inspired by Glint-Research/Fable-5-traces',
  },
]

const FABLE5_LOCAL_INCLUDES_TH: IncludeItem[] = [
  {
    label: 'Upstream LoRA',
    detail: 'hotdogs/qwen3.6-27b-fable5-lora — น้ำหนักเดียวกับ HuggingFace GGUF',
  },
  { label: 'Pipeline 4 ขั้น', detail: 'Plan → implement → review → QA บน GPU' },
  { label: '$0 LLM', detail: 'ไม่มี cloud tokens เมื่อตั้ง Ollama แล้ว' },
  {
    label: 'Trace playbook',
    detail: 'รูปแบบขั้นตอนอิง Glint-Research/Fable-5-traces',
  },
]

const ONE_RUN_INCLUDES_EN: IncludeItem[] = [
  { label: 'Visibility scorecard', detail: '5-layer score so you know where you stand' },
  { label: 'Public proof URL', detail: 'Shareable AIBotAuth badge (live: SuccessCasting & Pinpoint)' },
  { label: 'Audit report', detail: 'Plain priorities: fix this first, then that' },
  { label: 'Fix files', detail: 'robots.txt, llms.txt, JSON-LD snippets to paste' },
  { label: 'QA review', detail: 'Second AI pass catches weak recommendations' },
]

const ONE_RUN_INCLUDES_TH: IncludeItem[] = [
  { label: 'Visibility scorecard', detail: 'คะแนน 5 ชั้น — รู้ว่าตอนนี้อยู่ตรงไหน' },
  { label: 'ลิงก์ proof สาธารณะ', detail: 'Badge AIBotAuth แชร์ได้ (ลูกค้าจริง SuccessCasting & Pinpoint)' },
  { label: 'รายงาน audit', detail: 'ลำดับความสำคัญชัด — แก้อันไหนก่อน' },
  { label: 'ไฟล์แก้', detail: 'robots.txt, llms.txt, JSON-LD snippet พร้อมวาง' },
  { label: 'รีวิว QA', detail: 'AI รอบสองจับคำแนะนำที่อ่อน' },
]

const AGENT_FREE_INCLUDES_EN: IncludeItem[] = [
  { label: 'Free Agent-Ready scan', detail: 'isitagentready.com-style category scores' },
  { label: 'Public proof link', detail: '88/100 on file for live OBOLLA clients' },
  { label: 'Paste-ready fixes', detail: 'robots.txt, llms.txt, agents.txt, Content-Signal' },
  { label: 'Upgrade path', detail: 'Auto Fix Pro $9.99 · Growth Monitor ฿490/mo' },
]

const AGENT_FREE_INCLUDES_TH: IncludeItem[] = [
  { label: 'สแกน Agent-Ready ฟรี', detail: 'คะแนนรายหมวดแบบ isitagentready.com' },
  { label: 'ลิงก์ proof สาธารณะ', detail: 'ลูกค้า OBOLLA จริง proof 88/100' },
  { label: 'ไฟล์แก้พร้อมวาง', detail: 'robots.txt, llms.txt, agents.txt, Content-Signal' },
  { label: 'ทางอัปเกรด', detail: 'Auto Fix Pro $9.99 · Growth Monitor ฿490/เดือน' },
]

const AGENT_PRO_INCLUDES_EN: IncludeItem[] = [
  { label: 'Level 5 fix pack', detail: 'Protocol + commerce stubs + deploy guide' },
  { label: 'Proof badge', detail: 'Public URL every run' },
  { label: 'Gap map', detail: 'P0/P1/P2 tied to files and deploy paths' },
  { label: 'Re-verify checklist', detail: 'Post-deploy isitagentready scan steps' },
]

const AGENT_PRO_INCLUDES_TH: IncludeItem[] = [
  { label: 'แพ็ก Level 5', detail: 'Protocol + commerce stubs + คู่มือ deploy' },
  { label: 'Proof badge', detail: 'ลิงก์สาธารณะทุก run' },
  { label: 'แผนที่ช่องว่าง', detail: 'P0/P1/P2 ผูกกับไฟล์และ path deploy' },
  { label: 'เช็กลิสต์ verify', detail: 'ขั้นตอนสแกนซ้ำหลัง deploy' },
]

function pickIncludes(locale: Locale, en: IncludeItem[], th: IncludeItem[]) {
  return locale === 'th' ? th : en
}

export function Pricing() {
  const { locale, tr, trf } = useLocale()
  const [config, setConfig] = useState<BillingConfig | null>(null)

  useEffect(() => {
    api.getBillingConfig().then(setConfig).catch(() => setConfig(null))
  }, [])

  const signupCredits = config?.signup_credits_usd ?? 5
  const proIncludes = pickIncludes(locale, FABLE5_PRO_INCLUDES_EN, FABLE5_PRO_INCLUDES_TH)
  const localIncludes = pickIncludes(locale, FABLE5_LOCAL_INCLUDES_EN, FABLE5_LOCAL_INCLUDES_TH)
  const auditIncludes = pickIncludes(locale, ONE_RUN_INCLUDES_EN, ONE_RUN_INCLUDES_TH)
  const agentFreeIncludes = pickIncludes(locale, AGENT_FREE_INCLUDES_EN, AGENT_FREE_INCLUDES_TH)
  const agentProIncludes = pickIncludes(locale, AGENT_PRO_INCLUDES_EN, AGENT_PRO_INCLUDES_TH)

  return (
    <div className="mx-auto max-w-3xl px-4 py-10 sm:px-6">
      <Link to="/" className="text-sm font-medium text-readable-muted hover:text-[var(--color-text)]">
        {tr('skillBackMarketplace')}
      </Link>

      <h1 className="mt-6 text-3xl font-bold text-[var(--color-text)]">{tr('pricingTitle')}</h1>
      <p className="mt-2 font-medium text-readable-muted">{tr('pricingSubtitle')}</p>
      <p className="mt-2 max-w-2xl text-sm font-medium text-[var(--color-market-hover)]">
        {locale === 'th'
          ? 'Agent-Ready Certification — ลูกค้าจริง successcasting.com & pinpointaccountingservice.com (proof 88/100)'
          : 'Agent-Ready Certification — live clients successcasting.com & pinpointaccountingservice.com (88/100 proof)'}
      </p>

      <div className="mt-8 rounded-2xl border-2 border-emerald-300 bg-emerald-50/90 p-6 sm:p-8">
        <p className="text-sm font-semibold text-emerald-950">Fix Bot AI — Free Agent Scan</p>
        <div className="mt-2 flex flex-wrap items-end gap-3">
          <p className="text-4xl font-bold text-[var(--color-text)]">$0</p>
          <p className="pb-1 text-sm font-medium text-readable-muted">
            {locale === 'th' ? 'สแกน + ลิงก์ proof สาธารณะ' : 'scan + public proof link'}
          </p>
        </div>
        <ul className="mt-4 space-y-3">
          {agentFreeIncludes.map((item) => (
            <li
              key={item.label}
              className="flex gap-3 rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)] px-4 py-3"
            >
              <span className="shrink-0 text-emerald-400">✓</span>
              <div>
                <p className="font-medium text-[var(--color-text)]">{item.label}</p>
                <p className="text-sm text-[var(--color-muted)]">{item.detail}</p>
              </div>
            </li>
          ))}
        </ul>
        <Link
          to={`/expert-skills/${FIX_BOT_AI_SKILL_ID}`}
          className="mt-6 inline-block rounded-lg bg-emerald-600 px-6 py-3 text-sm font-bold text-white hover:bg-emerald-500"
        >
          {locale === 'th' ? 'สแกนฟรี + Proof' : 'Free Scan + Proof'}
        </Link>
      </div>

      <div className="mt-6 rounded-2xl border-2 border-amber-200 bg-amber-50/90 p-6 sm:p-8">
        <p className="text-sm font-semibold text-amber-950">Agent-Ready Auto Fix Pro</p>
        <div className="mt-2 flex flex-wrap items-end gap-3">
          <p className="text-4xl font-bold text-[var(--color-text)]">$9.99</p>
          <p className="pb-1 text-sm font-medium text-readable-muted">
            {locale === 'th' ? 'ต่อรัน + LLM ผ่านเครดิต' : 'per run + LLM via credits'}
          </p>
        </div>
        <ul className="mt-4 space-y-3">
          {agentProIncludes.map((item) => (
            <li
              key={item.label}
              className="flex gap-3 rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)] px-4 py-3"
            >
              <span className="shrink-0 text-emerald-400">✓</span>
              <div>
                <p className="font-medium text-[var(--color-text)]">{item.label}</p>
                <p className="text-sm text-[var(--color-muted)]">{item.detail}</p>
              </div>
            </li>
          ))}
        </ul>
        <Link
          to="/agent-ready"
          className="mt-6 inline-block rounded-lg bg-amber-500 px-6 py-3 text-sm font-bold text-slate-900 hover:bg-amber-400"
        >
          {locale === 'th' ? 'แก้ถึง Level 5 — $9.99' : 'Fix to Level 5 — $9.99'}
        </Link>
      </div>

      <div className="mt-8 rounded-2xl border-2 border-violet-200 bg-violet-50/90 p-6 sm:p-8">
        <p className="text-sm font-semibold text-violet-950">Fable-5 Coding Agent Pro</p>
        <div className="mt-2 flex flex-wrap items-end gap-3">
          <p className="text-4xl font-bold text-[var(--color-text)]">$5</p>
          <p className="pb-1 text-sm font-medium text-readable-muted">{trf('pricingPerRunLlm', { amount: '0.18' })}</p>
        </div>
        <p className="mt-1 text-lg font-medium text-violet-900">
          GPT-4.1 + Grok 3 Mini · {locale === 'th' ? 'ไม่ต้องมี GPU · 3–6 นาที' : 'no GPU · 3–6 minutes'}
        </p>

        <h2 className="mt-6 text-sm font-semibold uppercase tracking-wide text-[var(--color-muted)]">
          {tr('pricingOneRunIncludes')}
        </h2>
        <ul className="mt-4 space-y-3">
          {proIncludes.map((item) => (
            <li
              key={item.label}
              className="flex gap-3 rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)] px-4 py-3"
            >
              <span className="text-emerald-400 shrink-0">✓</span>
              <div>
                <p className="font-medium text-[var(--color-text)]">{item.label}</p>
                <p className="text-sm text-[var(--color-muted)]">{item.detail}</p>
              </div>
            </li>
          ))}
        </ul>

        <Link
          to={`/expert-skills/${FABLE5_PREMIUM_SKILL_ID}`}
          className="mt-6 inline-block rounded-lg bg-violet-500 px-6 py-3 text-sm font-bold text-slate-900 hover:bg-violet-400"
        >
          {tr('pricingRunPro')}
        </Link>
      </div>

      <div className="mt-6 rounded-2xl border-2 border-emerald-200 bg-emerald-50/80 p-6 sm:p-8">
        <p className="text-sm font-semibold text-emerald-950">Fable-5 Local LoRA (Free)</p>
        <div className="mt-2 flex flex-wrap items-end gap-3">
          <p className="text-4xl font-bold text-[var(--color-text)]">$0</p>
          <p className="pb-1 text-sm font-medium text-readable-muted">{tr('pricingRunFeeGpu')}</p>
        </div>
        <p className="mt-1 text-sm font-medium text-amber-900">{tr('pricingOllamaNote')}</p>

        <ul className="mt-4 space-y-3">
          {localIncludes.map((item) => (
            <li
              key={item.label}
              className="flex gap-3 rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)] px-4 py-3"
            >
              <span className="text-emerald-400 shrink-0">✓</span>
              <div>
                <p className="font-medium text-[var(--color-text)]">{item.label}</p>
                <p className="text-sm text-[var(--color-muted)]">{item.detail}</p>
              </div>
            </li>
          ))}
        </ul>

        <div className="mt-5">
          <Fable5CreditsStrip compact />
        </div>

        <Link
          to={`/expert-skills/${FABLE5_LOCAL_SKILL_ID}`}
          className="mt-6 inline-block rounded-lg bg-emerald-500 px-6 py-3 text-sm font-bold text-slate-900 hover:bg-emerald-400"
        >
          {tr('pricingRunLocal')}
        </Link>
      </div>

      <div className="mt-6 rounded-2xl border-2 border-[var(--color-sage)]/40 bg-[var(--color-surface-overlay)]/60 p-6 sm:p-8">
        <p className="text-sm font-semibold text-[var(--color-text)]">AI Visibility Audit</p>
        <div className="mt-2 flex flex-wrap items-end gap-3">
          <p className="text-4xl font-bold text-[var(--color-text)]">$2.50</p>
          <p className="pb-1 text-sm font-medium text-readable-muted">{trf('pricingPerRunAi', { amount: '0.12' })}</p>
        </div>
        <p className="mt-1 text-lg font-medium text-[var(--color-market-hover)]">
          {trf('pricingTotalReady', { amount: '2.62' })}
        </p>

        <ul className="mt-4 space-y-3">
          {auditIncludes.map((item) => (
            <li
              key={item.label}
              className="flex gap-3 rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)] px-4 py-3"
            >
              <span className="text-emerald-400 shrink-0">✓</span>
              <div>
                <p className="font-medium text-[var(--color-text)]">{item.label}</p>
                <p className="text-sm text-[var(--color-muted)]">{item.detail}</p>
              </div>
            </li>
          ))}
        </ul>

        <Link
          to={`/expert-skills/${AI_VISIBILITY_SKILL_ID}`}
          className="mt-6 inline-block rounded-lg bg-cyan-500 px-6 py-3 text-sm font-bold text-slate-900 hover:bg-cyan-400"
        >
          {tr('pricingRunAudit')}
        </Link>
      </div>

      <div className="mt-6 rounded-2xl border border-[var(--color-border)] bg-white/95 p-6">
        <h2 className="font-semibold text-[var(--color-text)]">{tr('pricingNewHere')}</h2>
        <p className="mt-2 text-3xl font-bold text-[var(--color-text)]">
          ${signupCredits.toFixed(0)} {tr('pricingFreeCredits')}
        </p>
        <p className="text-sm text-[var(--color-muted)]">{tr('pricingEnoughPro')}</p>
        <Link
          to="/register"
          state={{ from: { pathname: `/expert-skills/${FABLE5_PREMIUM_SKILL_ID}` } }}
          className="mt-4 inline-block rounded-lg bg-cyan-500 px-4 py-2 text-sm font-semibold text-slate-900 hover:bg-cyan-400"
        >
          {tr('pricingCreateAccount')}
        </Link>
      </div>
    </div>
  )
}