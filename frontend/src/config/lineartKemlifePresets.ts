/** Topic + edit-style presets for line-art YouTube / Facebook Reels agent flows. */

export type LineartFormat = 'reel' | 'youtube'

export type LineartTopicPreset = {
  id: string
  label_th: string
  label_en: string
  brief_th: string
  brief_en: string
}

export type LineartEditStylePreset = {
  id: string
  formats: LineartFormat[]
  label_th: string
  label_en: string
  notes_th: string
  notes_en: string
}

export const LINEART_KEMLIFE_SLUGS = [
  'ai-lineart-youtube-kemlife',
  'ai-lineart-facebook-reel-kemlife',
] as const

export type LineartKemlifeSlug = (typeof LINEART_KEMLIFE_SLUGS)[number]

export function isLineartKemlifeSlug(slug: string | undefined): slug is LineartKemlifeSlug {
  return LINEART_KEMLIFE_SLUGS.includes(slug as LineartKemlifeSlug)
}

export function lineartFormatFromSlug(slug: string | undefined): LineartFormat {
  return slug === 'ai-lineart-facebook-reel-kemlife' ? 'reel' : 'youtube'
}

export const LINEART_TOPIC_PRESETS: LineartTopicPreset[] = [
  {
    id: 'body-secrets',
    label_th: 'ความลับของร่างกาย',
    label_en: 'Body secrets',
    brief_th: 'สิ่งที่ร่างกายทำโดยไม่บอก — คำถามเดียวที่ต้องรู้คำตอบ',
    brief_en: 'What your body does without telling you — one-answer curiosity hooks',
  },
  {
    id: 'psychology',
    label_th: 'จิตวิทยาที่ซ่อนอยู่',
    label_en: 'Hidden psychology',
    brief_th: 'ทำไมคุณถึง… — พฤติกรรมที่คนสงสัยแต่ไม่กล้าถาม',
    brief_en: 'Why you… — behaviors people wonder about but rarely ask',
  },
  {
    id: 'history-wtf',
    label_th: 'ประวัติศาสตร์ WTF',
    label_en: 'History WTF',
    brief_th: 'เรื่องจริงในอดีตที่ฟังแล้วไม่เชื่อ — มุม Zenn-style',
    brief_en: 'Real past events that sound fake — Zenn-style curiosity',
  },
  {
    id: 'life-backfire',
    label_th: 'ไลฟ์แฮ็กที่แพ้',
    label_en: 'Life hacks that backfire',
    brief_th: 'เคล็ดลับที่ดูฉลาดแต่ทำร้ายคุณ — twist ท้ายคลิป',
    brief_en: 'Tips that look smart but hurt you — twist ending',
  },
  {
    id: 'custom',
    label_th: 'กำหนดเอง',
    label_en: 'Custom topic',
    brief_th: 'พิมพ์มุมหรือหัวข้อเฉพาะในช่องด้านล่าง',
    brief_en: 'Type your specific angle in the notes field below',
  },
]

export const LINEART_EDIT_STYLE_PRESETS: LineartEditStylePreset[] = [
  {
    id: 'reel-fast-cut',
    formats: ['reel'],
    label_th: 'ตัดเร็ว',
    label_en: 'Fast cut',
    notes_th: 'เปลี่ยนภาพทุก 1–2 วิ, hook ข้อความใหญ่วินาทีแรก, เพลงเบา',
    notes_en: 'Image every 1–2s, bold hook text in second one, light music',
  },
  {
    id: 'reel-punch-zoom',
    formats: ['reel'],
    label_th: 'ซูมช็อต + hook',
    label_en: 'Punch zoom hooks',
    notes_th: 'ซูมเข้า stick figure ตอนคำสำคัญ, ข้อความบนจอสั้นๆ',
    notes_en: 'Zoom on stick figures at keywords, short on-screen text',
  },
  {
    id: 'reel-text-heavy',
    formats: ['reel'],
    label_th: 'เน้นข้อความ (ปิดเสียง)',
    label_en: 'Text-heavy (muted)',
    notes_th: 'ข้อความบนจอทุก beat สำหรับคนดูแบบไม่เปิดเสียง',
    notes_en: 'On-screen text every beat for muted scrollers',
  },
  {
    id: 'reel-meme-hold',
    formats: ['reel'],
    label_th: 'ค้างเฟรมตลก',
    label_en: 'Meme hold beat',
    notes_th: 'ค้างภาพ MS Paint แปลกๆ 1 วิ เป็นจังหวะตลกก่อนตัดต่อ',
    notes_en: 'Hold one ugly MS Paint frame ~1s as a comedy beat',
  },
  {
    id: 'yt-dense-cut',
    formats: ['youtube'],
    label_th: 'ตัดถี่มาตรฐาน',
    label_en: 'Dense cuts (default)',
    notes_th: 'เปลี่ยนภาพทุก 3–5 วิ, sync กับบทพากย์, caption เบาๆ',
    notes_en: 'Image every 3–5s, synced voiceover, light captions',
  },
  {
    id: 'yt-chapter',
    formats: ['youtube'],
    label_th: 'แบ่ง part + title',
    label_en: 'Chapter beats',
    notes_th: 'แบ่ง 3–4 part มี title card MS Paint สั้นๆ ระหว่างทาง',
    notes_en: '3–4 parts with short MS Paint title cards between sections',
  },
  {
    id: 'yt-meme-hold',
    formats: ['youtube'],
    label_th: 'ค้างเฟรมตลก',
    label_en: 'Meme hold beat',
    notes_th: 'ค้างเฟรมตลก 1–2 วิ เป็นจังหวะพักก่อน re-hook',
    notes_en: 'Hold comedy frame 1–2s as a pause before re-hooks',
  },
  {
    id: 'yt-slow-burn',
    formats: ['youtube'],
    label_th: 'ช้าลึก (5–7 วิ)',
    label_en: 'Slow-burn holds',
    notes_th: 'ถือภาพนานขึ้น 5–7 วิ สำหรับเรื่องลึก — ยังต้อง MS Paint ห้ามสวย',
    notes_en: 'Longer 5–7s holds for deep stories — still ugly MS Paint',
  },
]

export function defaultEditStyleId(format: LineartFormat): string {
  return format === 'reel' ? 'reel-fast-cut' : 'yt-dense-cut'
}

export function editStylesForFormat(format: LineartFormat): LineartEditStylePreset[] {
  return LINEART_EDIT_STYLE_PRESETS.filter((s) => s.formats.includes(format))
}

export function findTopic(id: string): LineartTopicPreset | undefined {
  return LINEART_TOPIC_PRESETS.find((t) => t.id === id)
}

export function findEditStyle(id: string): LineartEditStylePreset | undefined {
  return LINEART_EDIT_STYLE_PRESETS.find((s) => s.id === id)
}

export type LineartPresetSelection = {
  format: LineartFormat
  topicId: string
  editStyleId: string
  customTopic?: string
  language: 'th' | 'en'
}

const PRESET_BLOCK_RE = /\[OBOLLA_PRESETS\][\s\S]*?\[\/OBOLLA_PRESETS\]\s*/g

export function buildLineartPresetBlock(sel: LineartPresetSelection): string {
  const topic = findTopic(sel.topicId)
  const style = findEditStyle(sel.editStyleId)
  const topicLabel = sel.language === 'th' ? topic?.label_th : topic?.label_en
  const styleLabel = sel.language === 'th' ? style?.label_th : style?.label_en
  const styleNotes = sel.language === 'th' ? style?.notes_th : style?.notes_en
  const topicBrief = sel.language === 'th' ? topic?.brief_th : topic?.brief_en
  const langLabel = sel.language === 'th' ? 'ไทย' : 'English'
  const custom = sel.customTopic?.trim()

  const lines =
    sel.language === 'th'
      ? [
          '[OBOLLA_PRESETS]',
          `หัวข้อ: ${topicLabel ?? sel.topicId}`,
          topicBrief ? `มุมเนื้อหา: ${topicBrief}` : '',
          custom ? `หัวข้อย่อย: ${custom}` : '',
          `สไตล์ตัดต่อ: ${styleLabel ?? sel.editStyleId}`,
          styleNotes ? `แนวตัดต่อ: ${styleNotes}` : '',
          `ภาษาบท: ${langLabel}`,
          `ฟอร์แมต: ${sel.format === 'reel' ? 'Facebook Reels 9:16' : 'YouTube 16:9'}`,
          '[/OBOLLA_PRESETS]',
        ]
      : [
          '[OBOLLA_PRESETS]',
          `Topic: ${topicLabel ?? sel.topicId}`,
          topicBrief ? `Angle: ${topicBrief}` : '',
          custom ? `Sub-topic: ${custom}` : '',
          `Edit style: ${styleLabel ?? sel.editStyleId}`,
          styleNotes ? `Edit notes: ${styleNotes}` : '',
          `Script language: ${langLabel}`,
          `Format: ${sel.format === 'reel' ? 'Facebook Reels 9:16' : 'YouTube 16:9'}`,
          '[/OBOLLA_PRESETS]',
        ]

  return `${lines.filter(Boolean).join('\n')}\n\n`
}

export function stripLineartPresetBlock(text: string): string {
  return text.replace(PRESET_BLOCK_RE, '').trim()
}

export function mergeLineartPresetsIntoText(text: string, sel: LineartPresetSelection): string {
  const body = stripLineartPresetBlock(text)
  const block = buildLineartPresetBlock(sel)
  return body ? `${block}${body}` : block.trimEnd()
}

export function validateLineartPresets(sel: LineartPresetSelection, freeText: string): string | null {
  if (!findTopic(sel.topicId)) return 'Please pick a topic.'
  if (!findEditStyle(sel.editStyleId)) return 'Please pick an edit style.'
  if (sel.topicId === 'custom' && !sel.customTopic?.trim() && !freeText.trim()) {
    return sel.language === 'th'
      ? 'กรุณาระบุหัวข้อเพิ่มเติม หรืออธิบายในช่องงาน'
      : 'Add a custom topic or describe your task below.'
  }
  return null
}