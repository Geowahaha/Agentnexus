import type { ExpertSkill } from '../types'

export interface SkillDeliverable {
  icon: string
  title: string
  desc: string
}

export type SkillInputMode = 'url' | 'task'

export interface SkillMeta {
  pipelineLabel: string
  deliverables: SkillDeliverable[]
  runHint?: string
  inputMode?: SkillInputMode
  runTitle?: string
  runCta?: string
  requiresLocalOllama?: boolean
  upgradeSkillId?: string
}

const GARDEN_DELIVERABLES: SkillDeliverable[] = [
  { icon: '📋', title: 'Structured brief', desc: 'Clear intake from the buyer task' },
  { icon: '✍️', title: 'Working draft', desc: 'Pipeline output ready to use' },
  { icon: '🔍', title: 'Review notes', desc: 'Edits and quality checks' },
  { icon: '✅', title: 'QA verdict', desc: 'Verified before delivery' },
]

const CONTENT_DELIVERABLES: SkillDeliverable[] = [
  { icon: '🔎', title: 'Research notes', desc: 'Sources and angles gathered' },
  { icon: '✍️', title: 'Draft', desc: 'First version ready to edit' },
  { icon: '📝', title: 'Edited copy', desc: 'Polished for publish' },
  { icon: '✅', title: 'Publish checklist', desc: 'QA before handoff' },
]

const DEFAULT_META: SkillMeta = {
  inputMode: 'task',
  pipelineLabel: 'Intake → Work → Review → Deliver',
  runTitle: 'Run Agent Flow',
  deliverables: GARDEN_DELIVERABLES,
}

const SKILL_META: Record<string, SkillMeta> = {
  'fix-bot-ai-free': {
    inputMode: 'url',
    pipelineLabel: 'Scan → Audit → Fix Pack → QA',
    runTitle: 'Run Free Agent Scan',
    runCta: 'Scan & Prove — Free',
    runHint:
      'Free scan + public proof link. Live clients: successcasting.com & pinpointaccountingservice.com (88/100). Upgrade to Auto Fix Pro $9.99.',
    upgradeSkillId: '33333333-3333-4333-8333-333333333310',
    deliverables: [
      { icon: '🔍', title: 'Agent-ready scorecard', desc: 'isitagentready.com-style category scores' },
      { icon: '🏅', title: 'Public proof URL', desc: 'Shareable AIBotAuth badge — like our live clients' },
      { icon: '⚠️', title: 'Prioritized fixes', desc: 'P0/P1/P2 — robots, llms, Content-Signal first' },
      { icon: '🤖', title: 'Bot access report', desc: 'GPTBot, ClaudeBot, PerplexityBot status' },
      { icon: '📁', title: 'robots.txt + agents.txt', desc: 'AI crawler rules + machine-readable policy' },
      { icon: '📝', title: 'llms.txt + ai.txt', desc: 'Markdown links + consistent training opt-out' },
      { icon: '🔗', title: 'Header snippets', desc: 'Content-Signal for Cloudflare / Next.js' },
      { icon: '✅', title: 'QA + verify link', desc: 'Re-check at isitagentready.com' },
      { icon: '🆓', title: '$0 marketplace fee', desc: 'Free scan — upgrade to Auto Fix Pro $9.99' },
    ],
  },
  'agent-ready-auto-fix': {
    inputMode: 'url',
    pipelineLabel: 'Scan → Get real fixes → Apply with your AI (MCP) — Revenue tracked',
    runTitle: 'Run Agent-Ready Auto Fix Pro',
    runCta: 'Closed-Loop Auto Fix to Level 5 — $9.99',
    runHint:
      'SEO + AEO + AAIO improvements with real files. Apply securely via your AI (MCP). Revenue auto-tracked for creators.',
    deliverables: [
      { icon: '🏅', title: 'Live verifiable proof', desc: 'AIBotAuth signed badge — re-verifiable' },
      { icon: '📊', title: 'Actionable gap map', desc: 'P0/P1/P2 with exact file paths from isitagentready taxonomy' },
      { icon: '📁', title: 'Real deployable files', desc: 'robots.txt, llms.txt, agents.txt, headers — ready' },
      { icon: '🔗', title: 'MCP secure apply', desc: 'One clean flow: give MCP spec to your AI (Claude, Cursor, Grok) — no local software' },
      { icon: '📈', title: 'Before/After lift', desc: 'Improves SEO, AEO & agent visibility' },
      { icon: '🚀', title: 'Stack deploy plan', desc: 'Next.js, Cloudflare, static — exact files & commands' },
      { icon: '💰', title: 'Revenue auto-tracked', desc: 'Apply logs real BillingTransaction + CreatorEarning via moat' },
      { icon: '🏆', title: 'Closed loop moat', desc: 'Execution data powers better future recommendations' },
    ],
  },
  'ai-visibility-2026': {
    inputMode: 'url',
    pipelineLabel: 'Scan → Audit → Fix Pack → QA',
    runTitle: 'Run Visibility Audit',
    runCta: 'Audit + Proof — $2.50',
    runHint:
      '$2.50/run + proof badge. Verified on successcasting.com & pinpointaccountingservice.com (88/100).',
    deliverables: [
      { icon: '📊', title: 'Visibility scorecard', desc: '5-layer AI readability score (0–100)' },
      { icon: '🏅', title: 'Public proof URL', desc: 'Agent-Ready badge — share with clients' },
      { icon: '⚠️', title: 'Prioritized issues', desc: 'P0/P1/P2 findings with severity & impact' },
      { icon: '🤖', title: 'Bot status report', desc: 'Which AI crawlers can read your site today' },
      { icon: '📁', title: 'robots.txt', desc: 'AI crawler rules + Content-Signal directives' },
      { icon: '📝', title: 'llms.txt', desc: 'Complete Markdown link map for LLM agents' },
      { icon: '🔗', title: 'JSON-LD Schema', desc: 'Structured data matched to your site type' },
      { icon: '✅', title: 'QA-verified output', desc: 'Checked for accuracy before delivery' },
      { icon: '💡', title: 'Action plan', desc: '3–7 fixes you can deploy this week' },
    ],
  },
  'fable5-coding-agent': {
    pipelineLabel: 'Plan → Implement → Review → QA (local LoRA)',
    inputMode: 'task',
    runTitle: 'Run Local LoRA Agent',
    runCta: 'Run Local Agent — Free',
    runHint: 'Requires server Ollama + qwen3.6-27b-fable5. No GPU? Use Pro tier.',
    requiresLocalOllama: true,
    upgradeSkillId: '33333333-3333-4333-8333-333333333304',
    deliverables: [
      { icon: '🔗', title: 'hotdogs LoRA', desc: 'Runs huggingface.co/hotdogs/qwen3.6-27b-fable5-lora' },
      { icon: '🧭', title: 'Step plan', desc: 'Patterns from Glint-Research/Fable-5-traces' },
      { icon: '💻', title: 'Implementation', desc: 'Same adapter — plan + code on local GPU' },
      { icon: '🔍', title: 'Code review', desc: 'LoRA reviewer — P0/P1/P2 + patches' },
      { icon: '✅', title: 'QA verdict', desc: 'READY or NEEDS_CORRECTION checklist' },
      { icon: '🖥️', title: '$0 run + $0 LLM', desc: 'All 4 steps on Ollama when configured' },
    ],
  },
  'ai-lineart-facebook-reel-kemlife': {
    pipelineLabel: 'Hook → บทสั้น+เวลา → Prompt 9:16 → QA ปล่อย Reels',
    inputMode: 'task',
    runTitle: 'รันเทมเพลต Facebook Reels การ์ตูนลายเส้น',
    runCta: 'Run Reels Line-Art Kit — ~$1.11',
    runHint:
      'บอก niche หรือหัวข้อ Reel — ได้ hook + บท 30–90s + prompt ภาพ MS Paint 9:16',
    deliverables: [
      { icon: '⚡', title: 'Scroll-stop hooks', desc: '3–5 openers that pause the feed in 1 second' },
      { icon: '📝', title: 'Short script', desc: '30–90s voiceover with 1–3s timestamp density' },
      { icon: '🖍️', title: 'MS Paint 9:16', desc: 'Per-shot vertical prompts — intentionally ugly' },
      { icon: '💬', title: 'On-screen text', desc: 'Hook + keyword overlays for muted viewers' },
      { icon: '📱', title: 'Reels caption', desc: 'Facebook caption + hashtags copy-paste ready' },
      { icon: '✅', title: 'Publish QA', desc: 'CapCut vertical checklist + READY verdict' },
    ],
  },
  'ai-lineart-youtube-kemlife': {
    pipelineLabel: 'หาเรื่อง → บท+เวลา → Prompt ภาพ → QA ปล่อยคลิป',
    inputMode: 'task',
    runTitle: 'รันเทมเพลตช่องการ์ตูนลายเส้น',
    runCta: 'Run Line-Art Channel Kit — ~$1.14',
    runHint:
      'บอก niche หรือหัวข้อคลิป — ได้บท timestamp + ตาราง prompt ภาพ MS Paint 16:9',
    deliverables: [
      { icon: '🎯', title: 'Topic hooks', desc: '3–5 titles that force the click' },
      { icon: '📝', title: 'Timestamped script', desc: '8–13 min voiceover with dense timecodes' },
      { icon: '🖍️', title: 'MS Paint prompts', desc: 'Per-shot 16:9 prompts — intentionally ugly' },
      { icon: '📁', title: 'Filename map', desc: '0-00, 0-03… ready for CapCut timeline' },
      { icon: '✂️', title: 'Edit checklist', desc: 'CapCut/DaVinci sync + music/caption tips' },
      { icon: '✅', title: 'Publish QA', desc: 'Title, thumbnail, READY verdict' },
    ],
  },
  'fable5-coding-agent-premium': {
    pipelineLabel: 'Plan → Implement → Review → QA (cloud Pro)',
    inputMode: 'task',
    runTitle: 'Run Pro Coding Agent',
    runCta: 'Run Pro Agent — $5',
    runHint: 'No Ollama/GPU needed. GPT-4.1 + Grok 3 Mini in the cloud.',
    deliverables: [
      { icon: '🧭', title: 'Deep plan', desc: 'GPT-4.1 exploration map + numbered steps' },
      { icon: '💻', title: 'Production code', desc: 'Complete files, tests, verify commands' },
      { icon: '🔍', title: 'Senior review', desc: 'Grok 3 Mini — strict P0/P1/P2 + patches' },
      { icon: '✅', title: 'QA verdict', desc: 'READY gate — Pro quality bar' },
      { icon: '☁️', title: 'Cloud only', desc: 'OpenAI + Grok — no local setup' },
      { icon: '⚡', title: '$5/run', desc: 'For buyers without a GPU machine' },
    ],
  },
  'image-post-creator': {
    pipelineLabel: 'มุมโพสต์ → แคปชัน → Prompt → Gen รูป → QA',
    inputMode: 'task',
    runTitle: 'รัน Image Post Creator',
    runCta: 'Run Image Post — ~$1.16',
    runHint:
      'บอกหัวข้อ (เช่น ข่าว AI / เทรนด์โลก) + แพลตฟอร์ม — ได้เรื่องเล่า 1 ตอน ภาษาไทยธรรมชาติ + รูป Grok Imagine',
    deliverables: [
      { icon: '🎯', title: 'Post angles', desc: '3–5 episode angles with visual scenes' },
      { icon: '📖', title: 'เรื่องเล่า 1 ตอน', desc: 'ภาษาไทยคนเล่า — ผูกกับภาพ ไม่ใช่แคปชั่นแปล' },
      { icon: '#️⃣', title: 'Hashtags', desc: 'Platform-appropriate tag set' },
      { icon: '🖼️', title: 'Generated image', desc: 'Grok Imagine — real image URL (~$0.05)' },
      { icon: '✅', title: 'Publish QA', desc: 'READY verdict before you post' },
    ],
  },
  'short-post-creator': {
    pipelineLabel: 'มุมโพสต์ → ร่าง 3 แบบ → ขัดเกลา → QA ปล่อย',
    inputMode: 'task',
    runTitle: 'รัน Short Post Creator',
    runCta: 'Run Short Post — ~$0.61',
    runHint:
      'บอกหัวข้อ + แพลตฟอร์ม (X/Threads/LinkedIn/FB) — ได้โพสต์สั้นพร้อมโพสต์',
    deliverables: [
      { icon: '🔎', title: 'Platform research', desc: 'Angles + char limits for your platform' },
      { icon: '📝', title: '3 variants', desc: 'Different hooks with character counts' },
      { icon: '✨', title: 'Polished primary', desc: 'Best post + backup copy-paste ready' },
      { icon: '🧵', title: 'Thread split', desc: 'Numbered 1/N if you asked for a thread' },
      { icon: '✅', title: 'Publish QA', desc: 'Length + hook check + READY verdict' },
    ],
  },
  'seo-expert-analysis': {
    inputMode: 'url',
    pipelineLabel: 'Scan → Research → Analyze → Audit → Optimize → Report',
    runTitle: 'Run SEO Analysis',
    runHint: 'Keywords are auto-discovered from your site — paste the URL',
    deliverables: [
      { icon: '📊', title: 'SEO scorecard', desc: 'Overall score /100 + 5 sub-scores' },
      { icon: '🏁', title: 'Competitor analysis', desc: '3–5 competitors with strengths & gaps' },
      { icon: '📝', title: 'Content gap report', desc: 'Topics and pages you should add' },
      { icon: '🔧', title: 'Technical SEO audit', desc: 'Crawl, index, on-page, schema findings' },
      { icon: '⚡', title: 'Core Web Vitals', desc: 'LCP, INP, CLS with impact forecasts' },
      { icon: '🎯', title: 'Action plan', desc: 'Quick wins + long-term roadmap' },
      { icon: '📈', title: 'Impact forecasts', desc: 'Predicted outcomes per fix (conservative)' },
      { icon: '📄', title: 'Professional report', desc: 'Client-ready markdown download' },
    ],
  },
}

const CATEGORY_META: Record<string, Partial<SkillMeta>> = {
  content: {
    inputMode: 'task',
    pipelineLabel: 'Research → Draft → Edit → Publish',
    runTitle: 'Run Content Pipeline',
    deliverables: CONTENT_DELIVERABLES,
  },
  coding: {
    inputMode: 'task',
    pipelineLabel: 'Plan → Implement → Review → QA',
    runTitle: 'Run Agent Flow',
  },
  research: {
    inputMode: 'task',
    pipelineLabel: 'Gather → Analyze → Synthesize → Report',
    runTitle: 'Run Research Flow',
  },
  seo: {
    inputMode: 'url',
    pipelineLabel: 'Scan → Audit → Fix Pack → QA',
    runTitle: 'Run Visibility Audit',
  },
}

export const CAPABILITY_LABELS: Record<string, string> = {
  seo: 'Classic SEO',
  content: 'Content',
  research: 'Research',
  editing: 'Editing',
  youtube: 'YouTube',
  faceless: 'Faceless channel',
  'image-prompts': 'Image prompts',
  'video-prep': 'Video prep',
  'thai-content': 'Thai content',
  aeo: 'Answer Engine Optimization',
  geo: 'Generative Engine Optimization',
  'ai-visibility': 'AI Visibility',
  'agent-readiness': 'Agent Readiness',
  'fix-pack': 'Deployable Fix Pack',
  'robots-txt': 'robots.txt',
  'llms-txt': 'llms.txt',
  'json-ld': 'JSON-LD Schema',
  'content-signals': 'Content Signals',
  'free-scan': 'Free Scan',
  'technical-seo': 'Technical SEO',
  'on-page': 'On-Page SEO',
  'competitor-analysis': 'Competitor Analysis',
  'content-gap': 'Content Gap',
  'core-web-vitals': 'Core Web Vitals',
  schema: 'Schema Markup',
  'action-plan': 'Action Plan',
  'impact-forecast': 'Impact Forecast',
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
  social: 'Social media',
  copywriting: 'Copywriting',
  caption: 'Caption',
  facebook: 'Facebook',
  'image-generation': 'Image generation',
}

function crewString(skill: ExpertSkill, key: string): string | undefined {
  const value = skill.crew_config?.[key]
  return typeof value === 'string' && value.trim() ? value : undefined
}

function inferInputMode(skill: ExpertSkill): SkillInputMode {
  const fromCrew = crewString(skill, 'input_mode')
  if (fromCrew === 'url' || fromCrew === 'task') return fromCrew
  if (skill.pack_slug === 'custom') return 'task'
  if (skill.category && CATEGORY_META[skill.category]?.inputMode) {
    return CATEGORY_META[skill.category].inputMode!
  }
  const urlCaps = ['seo', 'ai-visibility', 'technical-seo', 'fix-pack']
  if (skill.capabilities.some((c) => urlCaps.includes(c))) return 'url'
  return 'task'
}

export function resolveSkillMeta(skill: Pick<ExpertSkill, 'slug' | 'category' | 'pack_slug' | 'crew_config' | 'capabilities' | 'name'>): SkillMeta {
  const hardcoded = SKILL_META[skill.slug]
  if (hardcoded) return hardcoded

  const categoryPartial = skill.category ? CATEGORY_META[skill.category] : undefined
  const inputMode = inferInputMode(skill as ExpertSkill)

  return {
    ...DEFAULT_META,
    ...categoryPartial,
    inputMode,
    pipelineLabel: crewString(skill as ExpertSkill, 'pipeline_label') ?? categoryPartial?.pipelineLabel ?? DEFAULT_META.pipelineLabel,
    runTitle: crewString(skill as ExpertSkill, 'run_title') ?? categoryPartial?.runTitle ?? DEFAULT_META.runTitle,
    runHint: crewString(skill as ExpertSkill, 'run_hint') ?? categoryPartial?.runHint,
    runCta: crewString(skill as ExpertSkill, 'run_cta'),
    deliverables: categoryPartial?.deliverables ?? DEFAULT_META.deliverables,
  }
}

const FABLE5_STEP_LABELS: Record<string, string> = {
  plan: 'Planner Agent',
  implement: 'Implementer Agent',
  review: 'Code Reviewer',
  qa: 'QA Gate',
  planner_agent: 'Planner Agent',
  implementer_agent: 'Implementer Agent',
  code_reviewer: 'Code Reviewer',
  qa_gate: 'QA Gate',
}

export function getExpertStepLabel(slug: string, stepId: string): string {
  if (slug === 'fable5-coding-agent' || slug === 'fable5-coding-agent-premium') {
    return FABLE5_STEP_LABELS[stepId] ?? stepId.replace(/_/g, ' ')
  }
  return stepId.replace(/_/g, ' ')
}

/** @deprecated use resolveSkillMeta(skill) */
export function getSkillMeta(slug: string): SkillMeta {
  return SKILL_META[slug] ?? DEFAULT_META
}