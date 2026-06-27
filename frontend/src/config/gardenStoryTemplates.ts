/** One-click story starters for Creator Garden compose mode. */

export type GardenStoryTemplate = {
  id: string
  skillId: string
  label_th: string
  label_en: string
  story_th: string
  story_en: string
}

export const LINEART_YOUTUBE_KEMLIFE_SKILL_ID = '33333333-3333-4333-8333-333333333305'
export const LINEART_FACEBOOK_REEL_KEMLIFE_SKILL_ID = '33333333-3333-4333-8333-333333333306'

export const GARDEN_STORY_TEMPLATES: GardenStoryTemplate[] = [
  {
    id: 'lineart-facebook-reel-kemlife',
    skillId: LINEART_FACEBOOK_REEL_KEMLIFE_SKILL_ID,
    label_th: 'Facebook Reels การ์ตูนลายเส้น AI',
    label_en: 'AI line-art Facebook Reels',
    story_th: `ผมอยากทำ Facebook Reels แบบไม่ต้องออกหน้า (faceless)
ใช้ภาพการ์ตูนลายเส้นบ้านๆ สไตล์ MS Paint เส้นเบี้ยว หัวกลม ห้ามวาดสวย — แนวตั้ง 9:16
เล่าเรื่องสั้น 30–90 วินาที ประวัติศาสตร์ จิตวิทยา ความลับของร่างกาย
hook วินาทีแรกต้องหยุด scroll ในวินาทีแรก

งานหนักที่อยากให้ AI ช่วย:
1) หา hook ที่หยุด scroll ในวินาทีแรก
2) เขียนบทพากย์สั้นพร้อม timestamp ถี่ๆ (1–3 วิ = หนึ่งภาพ)
3) แตก prompt ภาพ 9:16 ทุกช็อต — MS Paint style + ข้อความบนจอ
4) caption/hashtag Facebook + checklist ตัดต่อ CapCut แนวตั้ง

ผมจะใช้ Higgsfield วาดภาพเอง แต่อยากได้บทกับ prompt จาก agent`,
    story_en: `I want faceless Facebook Reels with ugly MS Paint line-art cartoons —
9:16 vertical, thick wobbly lines, round stick heads, deliberately not pretty.
Short 30–90s curiosity stories; the first second must stop the scroll.

Heavy work I want AI to carry:
1) Scroll-stop hooks for second one
2) Short voiceover with dense timestamps (1–3s = one image)
3) Per-shot 9:16 image prompts + on-screen text cues
4) Facebook caption/hashtags + vertical CapCut checklist

I'll render images in Higgsfield myself — need script + prompt pack from the agent.`,
  },
  {
    id: 'lineart-youtube-kemlife',
    skillId: LINEART_YOUTUBE_KEMLIFE_SKILL_ID,
    label_th: 'ช่อง YouTube การ์ตูนลายเส้น AI',
    label_en: 'AI line-art YouTube channel',
    story_th: `ผมอยากทำช่อง YouTube แบบไม่ต้องออกหน้า (faceless)
ใช้ภาพการ์ตูนลายเส้นบ้านๆ สไตล์ MS Paint เส้นเบี้ยว หัวกลม ห้ามวาดสวย
เล่าเรื่องประวัติศาสตร์ จิตวิทยา ความลับของร่างกาย แบบช่อง Zenn ที่คนดูเพราะอยากรู้คำตอบ

งานหนักที่อยากให้ AI ช่วย:
1) หาหัวข้อที่ title จิก
2) เขียนบทพากย์พร้อม timestamp ถี่ๆ (หนึ่งเวลา = หนึ่งภาพ)
3) แตก prompt ภาพ 16:9 ทุกช็อต — MS Paint style
4) checklist ตัดต่อ CapCut + QA ก่อนอัป

ผมจะใช้ Higgsfield / GPT Image วาดภาพเอง แต่อยากได้บทกับ prompt จาก agent`,
    story_en: `I want a faceless YouTube channel with ugly MS Paint line-art cartoons —
thick wobbly lines, round stick heads, deliberately not pretty (Zenn-style curiosity niche).

Heavy work I want AI to carry:
1) Topic hooks people must click
2) Voiceover script with dense timestamps (one timecode = one image)
3) Per-shot 16:9 image prompts in MS Paint style
4) CapCut edit checklist + publish QA

I'll render images in Higgsfield myself — need script + prompt pack from the agent.`,
  },
]