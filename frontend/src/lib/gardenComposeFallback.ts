import type { CreatorGardenCoachResponse } from '../types'
import type { Locale } from '../i18n/strings'

const VALID_CATEGORIES = new Set(['seo', 'coding', 'content', 'support', 'research', 'quality'])

function pickCategory(identity: string, audience: string, problem: string): string {
  const text = `${identity} ${audience} ${problem}`.toLowerCase()
  if (/seo|google|visibility|website|เว็บ|ค้นหา/.test(text)) return 'seo'
  if (/code|dev|api|python|โค้ด|พัฒนา/.test(text)) return 'coding'
  if (
    /write|content|blog|เขียน|บทความ|youtube|ยูทูบ|facebook|reel|เฟซบุ๊ก|การ์ตูน|ลายเส้น|faceless|capcut|kemlife|ช่อง/.test(
      text,
    )
  ) {
    return 'content'
  }
  if (/support|customer|ช่วยเหลือ|ลูกค้า/.test(text)) return 'support'
  if (/research|วิจัย|ข้อมูล|analyze/.test(text)) return 'research'
  return 'quality'
}

function workflowIdeas(
  identity: string,
  audience: string,
  problem: string,
): { name: string; pitch: string; steps: string }[] {
  const category = pickCategory(identity, audience, problem)
  const audienceShort = audience.trim().slice(0, 60) || 'คนที่คุณอยากช่วย'
  const problemShort = problem.trim().slice(0, 80) || 'งานที่ทำซ้ำจนเหนื่อย'

  const templates: Record<string, { name: string; pitch: string; steps: string }[]> = {
    seo: [
      {
        name: `AI visibility audit สำหรับ ${audienceShort}`,
        pitch: `สแกน → ตรวจ → แพ็กแก้ไขสำหรับ ${problemShort}`,
        steps: 'Scan → Auditor → Fix pack → QA',
      },
    ],
    coding: [
      {
        name: `Coding agent สำหรับ ${audienceShort}`,
        pitch: `วางแผน → ทำ → รีวิว → QA สำหรับ ${problemShort}`,
        steps: 'Planner → Implementer → Review → QA',
      },
    ],
    content: [
      {
        name: `Content pipeline สำหรับ ${audienceShort}`,
        pitch: `ค้นคว้า → ร่าง → ตัดต่อ → เช็กลิสต์ก่อนโพสต์สำหรับ ${problemShort}`,
        steps: 'Research → Draft → Edit → QA',
      },
    ],
    support: [
      {
        name: `Support playbook — ${audienceShort}`,
        pitch: 'แปลง FAQ เป็นคำตอบทีละขั้นพร้อมกฎ escalation',
        steps: 'FAQ → Draft → Review → Handoff',
      },
    ],
    research: [
      {
        name: `Research brief — ${audienceShort}`,
        pitch: `รวบรวมข้อมูล → สรุป → แนะนำขั้นต่อไปสำหรับ ${problemShort}`,
        steps: 'Gather → Summarize → Recommend',
      },
    ],
    quality: [
      {
        name: `Quality check flow — ${audienceShort}`,
        pitch: `ตรวจงานก่อนส่งมอบสำหรับ ${problemShort}`,
        steps: 'Checklist → Run → Review → Verdict',
      },
    ],
  }

  return templates[category] ?? templates.quality
}

function capabilitiesForCategory(category: string): string[] {
  const mapping: Record<string, string[]> = {
    seo: ['seo', 'audit', 'research'],
    coding: ['coding', 'review', 'qa'],
    content: ['content', 'writing', 'qa'],
    support: ['support', 'faq', 'handoff'],
    research: ['research', 'summarize'],
    quality: ['agent-flow', 'qa'],
  }
  return mapping[category] ?? ['agent-flow', 'qa']
}

export function composeGardenStoryFallback(
  rawStory: string,
  locale: Locale,
  modelTierId = 'standard',
): CreatorGardenCoachResponse {
  const story = rawStory.trim()
  const lines = story.split(/\r?\n/).map((line) => line.trim()).filter(Boolean)
  const identity = (lines[0] ?? story).slice(0, 400)
  const audience = (lines[1] ?? '').slice(0, 200)
  const problem = (lines[2] ?? (story.length > 200 ? story.slice(200, 500) : story)).slice(0, 300)
  const category = pickCategory(identity, audience, problem || story)
  const ideas = workflowIdeas(identity, audience, problem || story)
  const idea = ideas[0] ?? { name: 'Custom agent flow', pitch: story.slice(0, 200), steps: 'Draft → Run → QA' }
  const audienceFallback = locale === 'th' ? 'คนที่คุณอยากช่วย' : 'people you want to help'

  return {
    message_th:
      'เซิร์ฟเวอร์ช้าชั่วคราว — เราจัดร่างเบื้องต้นให้แล้ว ข้อความของคุณยังอยู่ครบ แก้ด้านล่างแล้วกดสร้างได้เลย (ไม่ต้อง login)',
    message_en:
      'Server briefly slow — we shaped a local draft. Your story is safe. Edit below and create when ready (no login needed).',
    workflow_ideas: ideas,
    suggested_draft: {
      identity,
      audience: audience || audienceFallback,
      problem: problem || story.slice(0, 300),
      name: idea.name,
      description: idea.pitch,
      category: VALID_CATEGORIES.has(category) ? category : 'quality',
      capabilities: capabilitiesForCategory(category),
      model_tier_id: modelTierId,
      suggested_price_usd: '0.99',
      input_mode: 'task',
      pipeline_label: idea.steps,
      run_title: idea.name,
    },
    companion_th: 'ผมอยู่ข้างคุณในการสร้างมันครับ',
    composed: true,
    used_llm: false,
  }
}