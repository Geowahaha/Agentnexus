/** OBOLLA DNA — community-first, not marketplace-first. */
export const OBOLLA_MANIFESTO_TH =
  'ไม่ใช่แค่ marketplace อีกแห่ง แต่ ชุมชนที่เอไอทำงานแทน เพื่อให้คนมีเวลาเป็นคน — ช่วยกันสร้างสวนสวยหน้าบ้าน แล้วมีเวลานั่งจิบกาแฟด้วยกัน'

export const OBOLLA_MANIFESTO_EN =
  'Not just another marketplace — a community where AI carries the heavy work so humans can be human again. We plant the front garden together, then make time to sit for coffee with the people we love.'

export const OBOLLA_GARDEN_STORY_TH = [
  'ในเยอรมนี สวนหน้าบ้านสวยเพราะผู้คนมีเวลาเหลือ — กลับบ้านตอนบ่าย มีแรงจับจอบ ปลูกดอกไม้ คุยกับลูกที่ระเบียงหน้าบ้าน',
  'ที่ไทยหลายครอบครัว ออกจากบ้านตอนเช้ามืด กลับมาตอนค่ำ หน้าบ้านแทบไม่มีเวลาดูแล แม้แต่ลูกก็ไม่มีเวลาคุยกัน',
  'เราไม่ได้มาแข่งกันว่าใครมีสวนสวยกว่า — เรามาช่วยกันสร้างสวนสวยหน้าบ้าน ด้วยเอไอที่ช่วยงานหนัก แล้วมีเวลานั่งจิบกาแฟด้วยกัน',
  'มาสร้างโลกที่เท่าเทียมกัน ใช้ประโยชน์จากเอไอร่วมกัน — ให้ agent ทำงานหนัก เพื่อให้คุณมีเวลาเป็นคน',
] as const

export const OBOLLA_GARDEN_STORY_EN = [
  'In Germany, front gardens bloom because people have time left — home by afternoon, energy to plant, talk with kids on the porch.',
  'In Thailand, many leave before dawn and return after dark. The front garden waits. Even children barely have time to talk.',
  'We are not competing over whose garden looks best — we build one together, with AI doing the heavy lifting, then sit for coffee.',
  'Let us build a fairer world with AI — agents carry the work so you have time to be human.',
] as const

export const OBOLLA_COMPANION_TH = 'ผมอยู่ข้างคุณในการสร้างมันครับ'

export const CREATOR_GARDEN_TITLE_TH = 'ห้องสร้างสรรค์ฟรี'
export const CREATOR_GARDEN_TITLE_EN = 'Free Creator Garden'

export const OBOLLA_DNA = [
  {
    th: 'เอไอทำงานหนัก — คนมีเวลาเป็นคน',
    en: 'AI carries the heavy work — humans have time to be human.',
  },
  {
    th: 'ช่วยกันสร้างสวนสวยหน้าบ้าน แล้วนั่งจิบกาแฟด้วยกัน',
    en: 'Build the front garden together — then sit for coffee with the people you love.',
  },
  {
    th: 'creator เป็นเจ้าของ flow — buyer ได้ผลลัพธ์จริง',
    en: 'Creators own flows; buyers get real outcomes.',
  },
  {
    th: 'ชุมชนอยู่ได้เมื่อ creator ได้รับรายได้อย่างซื่อสัตย์',
    en: 'Community thrives when creators earn honestly.',
  },
  {
    th: 'ให้เครดิต upstream ทุก model และ dataset',
    en: 'Credit every upstream model and dataset.',
  },
] as const

export const OBOLLA_CHARTER_RULES_EN = [
  'Credit every upstream model, dataset, and tool with name + link.',
  'Free when we have no inference cost; paid when we run cloud APIs.',
  'Never claim we trained a model we only orchestrate.',
  'Deliverables must be verifiable — QA gate before marketplace delivery.',
] as const

export const OBOLLA_CHARTER_RULES_TH = [
  'ให้เครดิตทุก model dataset และ tool พร้อมชื่อ + ลิงก์',
  'ฟรีเมื่อไม่มีค่า inference จ่ายเมื่อรันบนคลาวด์ API',
  'ไม่อ้างว่าเรา train model ที่เราแค่ orchestrate',
  'ผลลัพธ์ต้องตรวจสอบได้ — ผ่าน QA ก่อนส่งในตลาด',
] as const

/** @deprecated use OBOLLA_CHARTER_RULES_EN */
export const OBOLLA_CHARTER_RULES = OBOLLA_CHARTER_RULES_EN

export const GARDEN_STORAGE_KEY = 'obolla-creator-garden-draft'
export const GARDEN_STORY_KEY = 'obolla-creator-garden-story'