import type { Locale } from './strings'
import type { SkillAttribution } from '../types'
import { CAPABILITY_LABELS, type SkillDeliverable as MetaDeliverable } from '../config/expertSkillMeta'

const CATEGORY_TH: Record<string, string> = {
  content: 'คอนเทนต์',
  coding: 'โค้ด',
  research: 'วิจัย',
  quality: 'คุณภาพ',
  seo: 'SEO & Visibility',
  support: 'รีโมทซัพพอร์ต',
}

const CAPABILITY_TH: Record<string, string> = {
  seo: 'Classic SEO',
  content: 'คอนเทนต์',
  research: 'วิจัย',
  editing: 'การแก้ไข',
  youtube: 'YouTube',
  faceless: 'ช่องไร้หน้า',
  'image-prompts': 'Image prompts',
  'video-prep': 'เตรียมวิดีโอ',
  'thai-content': 'คอนเทนต์ไทย',
  aeo: 'Answer Engine Optimization',
  geo: 'Generative Engine Optimization',
  'ai-visibility': 'AI Visibility',
  'agent-readiness': 'Agent Readiness',
  'fix-pack': 'Fix Pack พร้อม deploy',
  'robots-txt': 'robots.txt',
  'llms-txt': 'llms.txt',
  'json-ld': 'JSON-LD Schema',
  'content-signals': 'Content Signals',
  'free-scan': 'สแกนฟรี',
  'technical-seo': 'Technical SEO',
  'on-page': 'On-Page SEO',
  'competitor-analysis': 'วิเคราะห์คู่แข่ง',
  'content-gap': 'Content Gap',
  'core-web-vitals': 'Core Web Vitals',
  schema: 'Schema Markup',
  'action-plan': 'แผนลงมือทำ',
  'impact-forecast': 'คาดการณ์ผลกระทบ',
  'coding-agent': 'Coding Agent',
  'tool-use': 'Tool Use',
  'multi-step-reasoning': 'Multi-Step Reasoning',
  'code-review': 'Code Review',
  'local-llm': 'Local LLM',
  fable5: 'Fable-5 Patterns',
  openai: 'OpenAI',
  premium: 'Premium',
  gemini: 'Gemini',
  grok: 'Grok',
  social: 'โซเชียล',
  copywriting: 'คอปีไรต์',
  caption: 'แคปชัน',
  facebook: 'Facebook',
  'image-generation': 'สร้างภาพ',
}

const DELIVERABLE_TH: Record<string, { title: string; desc: string }> = {
  'Structured brief': { title: 'บรีฟที่จัดโครงแล้ว', desc: 'สรุปงานจากคำสั่งของผู้ซื้อชัดเจน' },
  'Working draft': { title: 'งานร่างพร้อมใช้', desc: 'ผลลัพธ์จาก pipeline พร้อมนำไปต่อ' },
  'Review notes': { title: 'บันทึกการรีวิว', desc: 'จุดแก้และเช็กคุณภาพ' },
  'QA verdict': { title: 'ผล QA', desc: 'ตรวจแล้วก่อนส่งมอบ' },
  'Research notes': { title: 'บันทึกวิจัย', desc: 'รวบรวมแหล่งอ้างอิงและมุมมองแล้ว' },
  Draft: { title: 'ฉบับร่าง', desc: 'เวอร์ชันแรกพร้อมแก้ต่อ' },
  'Edited copy': { title: 'ข้อความที่แก้แล้ว', desc: 'ขัดเกลาพร้อมเผยแพร่' },
  'Publish checklist': { title: 'เช็กลิสต์ก่อนเผยแพร่', desc: 'QA ก่อนส่งมอบ' },
}

const PIPELINE_LABEL_TH: Record<string, string> = {
  'Research → Draft → Edit → Publish': 'วิจัย → ร่าง → แก้ → เผยแพร่',
  'Intake → Work → Review → Deliver': 'รับงาน → ทำ → รีวิว → ส่งมอบ',
  'Plan → Implement → Review → QA': 'วางแผน → ลงมือ → รีวิว → QA',
  'Plan → Implement → Review → QA (local LoRA)': 'วางแผน → ลงมือ → รีวิว → QA (local LoRA)',
  'Scan → Audit → Fix Pack → QA': 'สแกน → ตรวจ → Fix Pack → QA',
  'Gather → Analyze → Synthesize → Report': 'เก็บข้อมูล → วิเคราะห์ → สังเคราะห์ → รายงาน',
}

const RUN_TITLE_TH: Record<string, string> = {
  'Run Content Pipeline': 'รัน Content Pipeline',
  'Run Agent Flow': 'รัน Agent Flow',
  'Run Visibility Audit': 'รัน Visibility Audit',
  'Run Local LoRA Agent': 'รัน Local LoRA Agent',
  'Run Research Flow': 'รัน Research Flow',
  'Run SEO Analysis': 'รัน SEO Analysis',
  'Run Support Flow': 'รัน Support Flow',
  'Run Quality Flow': 'รัน Quality Flow',
  'Run Free Agent Scan': 'สแกน Agent ฟรี',
  'Run Agent-Ready Auto Fix': 'รัน Auto Fix Agent-Ready',
  'Run Pro Coding Agent': 'รัน Pro Coding Agent',
  'Run Image Post Creator': 'รัน Image Post Creator',
  'Run Short Post Creator': 'รัน Short Post Creator',
}

const STEP_TITLE_TH: Record<string, string> = {
  Research: 'วิจัย',
  Draft: 'ร่าง',
  'Edit & Polish': 'แก้และขัดเกลา',
  'QA Gate': 'QA Gate',
  Plan: 'วางแผน',
  Implement: 'ลงมือทำ',
  Review: 'รีวิว',
  QA: 'QA',
  Scan: 'สแกน',
  Audit: 'ตรวจ',
  'Fix Pack': 'Fix Pack',
}

const CHARTER_SUMMARY_EN =
  'OBOLLA orchestrates agent flows; upstream models, datasets, and tools keep their credit. Free tiers use your GPU or open upstream weights — we do not re-train without saying so.'

const CHARTER_SUMMARY_TH =
  'OBOLLA จัดการ agent flow ให้คุณ — โมเดล ชุดข้อมูล และเครื่องมือต้นทางยังได้เครดิตครบ ระดับฟรีรันบน GPU ของคุณหรือน้ำหนัก open upstream เราไม่ re-train โดยไม่แจ้งให้ทราบ'

const OBOLLA_LAYER_EN =
  'OBOLLA adds: multi-step pipeline, QA gate, marketplace delivery, optional Local Bridge, and billing — not the upstream weights themselves.'

const OBOLLA_LAYER_TH =
  'สิ่งที่ OBOLLA เพิ่ม: pipeline หลายขั้น, QA gate, ส่งมอบผ่าน marketplace, Local Bridge (ถ้าต้องการ) และระบบเรียกเก็บเงิน — ไม่ใช่ตัวน้ำหนักโมเดลต้นทาง'

const UPSTREAM_DETAIL_TH: Record<string, string> = {
  'Runtime LoRA adapter (all four steps via Ollama)':
    'LoRA adapter รัน runtime (ครบ 4 ขั้นผ่าน Ollama)',
  'Playbook patterns — explore → plan → edit → verify':
    'รูปแบบ playbook — explore → plan → edit → verify',
  'Pipeline format inspired by trace corpus (cloud GPT-4.1 + Grok)':
    'รูปแบบ pipeline อิงจาก trace corpus (cloud GPT-4.1 + Grok)',
  'Plan + implement steps via platform API': 'ขั้นวางแผน + ลงมือผ่าน platform API',
  'Review + QA steps via platform API': 'ขั้นรีวิว + QA ผ่าน platform API',
  'Deterministic AI crawler / visibility scan (MCP tool)':
    'สแกน AI crawler / visibility แบบ deterministic (MCP tool)',
  'On-page extraction + scanner signals (OBOLLA pipeline)':
    'ดึงข้อมูล on-page + สัญญาณจากสแกนเนอร์ (OBOLLA pipeline)',
}

export function localizeCategory(locale: Locale, category: string | null): string {
  if (!category) return ''
  if (locale === 'en') return category
  return CATEGORY_TH[category.toLowerCase()] ?? category
}

export function localizeCapability(locale: Locale, cap: string): string {
  const en = CAPABILITY_LABELS[cap] ?? cap.replace(/-/g, ' ')
  if (locale === 'en') return en
  return CAPABILITY_TH[cap] ?? en
}

export function localizeDeliverable(
  locale: Locale,
  item: MetaDeliverable,
): MetaDeliverable {
  if (locale === 'en') return item
  const th = DELIVERABLE_TH[item.title]
  return th ? { ...item, title: th.title, desc: th.desc } : item
}

export function localizePipelineLabel(locale: Locale, label: string): string {
  if (locale === 'en') return label
  return PIPELINE_LABEL_TH[label] ?? label
}

export function localizeRunTitle(locale: Locale, title: string): string {
  if (locale === 'en') return title
  return RUN_TITLE_TH[title] ?? title
}

export function localizeStepTitle(locale: Locale, title: string): string {
  if (locale === 'en') return title
  return STEP_TITLE_TH[title] ?? title
}

export function localizePricingHonesty(locale: Locale, text: string, priceUsd: number): string {
  if (locale === 'en') return text
  if (text.includes('marketplace fee plus LLM/tool usage via credits')) {
    return `ค่าธรรมเนียม marketplace $${priceUsd.toFixed(2)}/รัน บวกค่า LLM/เครื่องมือผ่านเครดิต`
  }
  if (text.includes('Free run fee; LLM/tools billed')) {
    return 'ไม่มีค่ารัน คิดค่า LLM/เครื่องมือตามเครดิตแพลตฟอร์ม (ถ้ามี)'
  }
  if (text.includes('Free marketplace fee; $0 LLM on your GPU')) {
    return 'ไม่มีค่า marketplace ค่า LLM $0 บน GPU ของคุณผ่าน Ollama ต้องมี hotdogs LoRA — ไม่มี cloud fallback'
  }
  if (text.includes('marketplace fee plus cloud LLM tokens')) {
    const m = text.match(/\$(\d+)/)
    const p = m ? m[1] : String(Math.round(priceUsd))
    return `ค่าธรรมเนียม marketplace $${p}/รัน บวก cloud LLM tokens ไม่ต้องมี GPU — ไม่ใช่น้ำหนัก hotdogs LoRA`
  }
  return text
}

export function localizeAttribution(locale: Locale, attribution: SkillAttribution, priceUsd: number) {
  if (locale === 'en') return attribution
  return {
    ...attribution,
    charter_summary:
      attribution.charter_summary === CHARTER_SUMMARY_EN ? CHARTER_SUMMARY_TH : attribution.charter_summary,
    obolla_layer: attribution.obolla_layer === OBOLLA_LAYER_EN ? OBOLLA_LAYER_TH : attribution.obolla_layer,
    pricing_honesty: localizePricingHonesty(locale, attribution.pricing_honesty, priceUsd),
    upstream: attribution.upstream.map((item) => ({
      ...item,
      detail: UPSTREAM_DETAIL_TH[item.detail] ?? item.detail,
    })),
  }
}

export function formatRunCta(
  locale: Locale,
  isFree: boolean,
  estTotal: number,
  estLlm: number,
  isTaskMode: boolean,
  customCta?: string,
): string {
  if (customCta) {
    if (locale === 'en') return customCta
    const mapped = RUN_TITLE_TH[customCta.replace(/ —.*/, '')]
    if (mapped && customCta.includes('—')) {
      return customCta.replace(/^Run [^—]+/, mapped)
    }
    return customCta
      .replace(/^Run Flow —/, 'รัน Flow —')
      .replace(/^Run Audit —/, 'รัน Audit —')
      .replace(/^Run Local Agent —/, 'รัน Local Agent —')
      .replace(/^Run Support Flow/, 'รัน Support Flow')
      .replace(/^Run /, 'รัน ')
  }
  if (locale === 'th') {
    return isTaskMode
      ? `รัน Flow — ~$${isFree ? estLlm.toFixed(2) : estTotal.toFixed(2)}`
      : `รัน Audit — ~$${estTotal.toFixed(2)}`
  }
  return isTaskMode
    ? `Run Flow — ~$${isFree ? estLlm.toFixed(2) : estTotal.toFixed(2)}`
    : `Run Audit — ~$${estTotal.toFixed(2)}`
}