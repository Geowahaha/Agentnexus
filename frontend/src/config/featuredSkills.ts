/** Obolla flagship agent flows — used for hero CTAs and featured sorting. */

export const FABLE5_LOCAL_SKILL_ID = '33333333-3333-4333-8333-333333333303'
export const FABLE5_LOCAL_SLUG = 'fable5-coding-agent'

export const FABLE5_PREMIUM_SKILL_ID = '33333333-3333-4333-8333-333333333304'
export const FABLE5_PREMIUM_SLUG = 'fable5-coding-agent-premium'

/** @deprecated use FABLE5_LOCAL_SKILL_ID */
export const FABLE5_SKILL_ID = FABLE5_LOCAL_SKILL_ID
/** @deprecated use FABLE5_LOCAL_SLUG */
export const FABLE5_SKILL_SLUG = FABLE5_LOCAL_SLUG

export const AI_VISIBILITY_SKILL_ID = '33333333-3333-4333-8333-333333333301'

export const LINEART_YOUTUBE_SKILL_ID = '33333333-3333-4333-8333-333333333305'
export const LINEART_YOUTUBE_SLUG = 'ai-lineart-youtube-kemlife'

export const LINEART_FACEBOOK_REEL_SKILL_ID = '33333333-3333-4333-8333-333333333306'
export const LINEART_FACEBOOK_REEL_SLUG = 'ai-lineart-facebook-reel-kemlife'

export const IMAGE_POST_SKILL_ID = '33333333-3333-4333-8333-333333333307'
export const IMAGE_POST_SLUG = 'image-post-creator'

export const SHORT_POST_SKILL_ID = '33333333-3333-4333-8333-333333333308'
export const SHORT_POST_SLUG = 'short-post-creator'

export const FIX_BOT_AI_SKILL_ID = '33333333-3333-4333-8333-333333333309'
export const FIX_BOT_AI_SLUG = 'fix-bot-ai-free'

export const AGENT_READY_AUTO_FIX_SKILL_ID = '33333333-3333-4333-8333-333333333310'
export const AGENT_READY_AUTO_FIX_SLUG = 'agent-ready-auto-fix'

/** Slugs pinned to the top of marketplace featured rows (Pro first for cloud buyers). */
export const PINNED_FEATURED_SLUGS = [
  AGENT_READY_AUTO_FIX_SLUG,
  FIX_BOT_AI_SLUG,
  FABLE5_PREMIUM_SLUG,
  FABLE5_LOCAL_SLUG,
] as const

export function sortFeaturedSkills<T extends { slug: string }>(skills: T[]): T[] {
  return [...skills].sort((a, b) => {
    const aIdx = PINNED_FEATURED_SLUGS.indexOf(a.slug as (typeof PINNED_FEATURED_SLUGS)[number])
    const bIdx = PINNED_FEATURED_SLUGS.indexOf(b.slug as (typeof PINNED_FEATURED_SLUGS)[number])
    const aRank = aIdx === -1 ? PINNED_FEATURED_SLUGS.length : aIdx
    const bRank = bIdx === -1 ? PINNED_FEATURED_SLUGS.length : bIdx
    return aRank - bRank
  })
}