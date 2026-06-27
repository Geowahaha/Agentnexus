export type ThumbnailPattern = 'rings' | 'dots' | 'grid' | 'waves' | 'diagonal' | 'hex'

/** Inline SVG motif id — all artwork is original, no external assets or emoji. */
export type ThumbnailMotif =
  | 'bot-scan'
  | 'auto-fix'
  | 'visibility'
  | 'terminal'
  | 'seo-chart'
  | 'greenhouse'
  | 'smart-sensors'
  | 'youtube'
  | 'reel'
  | 'image-post'
  | 'short-post'
  | 'cloud-premium'
  | 'network'
  | 'database'
  | 'workflow'
  | 'shield'
  | 'compass'
  | 'layers'
  | 'nodes'
  | 'pulse'
  | 'beacon'
  | 'radar'
  | 'circuit'
  | 'flow'
  | 'archive'
  | 'link'
  | 'scope'
  | 'matrix'
  | 'bridge'
  | 'orbit'
  | 'signal'
  | 'prism'

export interface ThumbnailTheme {
  from: string
  via: string
  to: string
  motif: ThumbnailMotif
  pattern: ThumbnailPattern
  accent: string
  image?: string   // real professional photo URL (Unsplash etc.)
}

const PACK_THEMES: Record<string, ThumbnailTheme> = {
  'fix-bot-ai-free': {
    from: '#0c4a6e',
    via: '#0284c7',
    to: '#bae6fd',
    motif: 'bot-scan',
    pattern: 'grid',
    accent: '#0369a1',
    image: 'https://images.unsplash.com/photo-1555066931-4365d14bab8c?w=600&q=80', // clean code / web audit feel
  },
  'agent-ready-auto-fix': {
    from: '#14532d',
    via: '#16a34a',
    to: '#bbf7d0',
    motif: 'auto-fix',
    pattern: 'diagonal',
    accent: '#15803d',
    image: 'https://images.unsplash.com/photo-1497366216548-37526070297c?w=600&q=80', // professional modern workspace with light
  },
  'ai-visibility-2026': {
    from: '#4c1d95',
    via: '#7c3aed',
    to: '#ddd6fe',
    motif: 'visibility',
    pattern: 'rings',
    accent: '#5b21b6',
    image: 'https://images.unsplash.com/photo-1432888622747-4eb9a8efeb07?w=600&q=80', // clean professional modern site feel
  },
  'fable5-coding-agent': {
    from: '#1e293b',
    via: '#334155',
    to: '#fdba74',
    motif: 'terminal',
    pattern: 'hex',
    accent: '#ea580c',
    image: 'https://images.unsplash.com/photo-1517694712202-14dd9538aa97?w=600&q=80', // real laptop on wooden desk with plants
  },
  'seo-expert-analysis': {
    from: '#78350f',
    via: '#d97706',
    to: '#fde68a',
    motif: 'seo-chart',
    pattern: 'waves',
    accent: '#b45309',
    image: 'https://images.unsplash.com/photo-1551288049-bebda4e38f71?w=600&q=80', // professional laptop analytics natural light
  },
  'japanese-melon-dataset': {
    from: '#365314',
    via: '#65a30d',
    to: '#ecfccb',
    motif: 'greenhouse',
    pattern: 'dots',
    accent: '#4d7c0f',
    image: 'https://images.unsplash.com/photo-1581092918056-0c4c3acd85ca?w=600&q=80', // real greenhouse plants
  },
  'quality-check-smart-farm': {
    from: '#134e4a',
    via: '#0d9488',
    to: '#ccfbf1',
    motif: 'smart-sensors',
    pattern: 'grid',
    accent: '#0f766e',
  },
  'ai-lineart-youtube-kemlife': {
    from: '#7f1d1d',
    via: '#dc2626',
    to: '#fecaca',
    motif: 'youtube',
    pattern: 'diagonal',
    accent: '#b91c1c',
    image: 'https://images.unsplash.com/photo-1516321497677-de7c7f2f4b9f?w=600&q=80', // creative desk setup
  },
  'ai-lineart-facebook-reel-kemlife': {
    from: '#831843',
    via: '#db2777',
    to: '#fbcfe8',
    motif: 'reel',
    pattern: 'rings',
    accent: '#be185d',
  },
  'image-post-creator': {
    from: '#881337',
    via: '#e11d48',
    to: '#ffe4e6',
    motif: 'image-post',
    pattern: 'dots',
    accent: '#be123c',
    image: 'https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=600&q=80', // creative content creation desk
  },
  'short-post-creator': {
    from: '#0c4a6e',
    via: '#2563eb',
    to: '#dbeafe',
    motif: 'short-post',
    pattern: 'waves',
    accent: '#1d4ed8',
    image: 'https://images.unsplash.com/photo-1485988412941-77a35537dae4?w=600&q=80', // writing desk with natural elements
  },
}

const SLUG_THEMES: Record<string, ThumbnailTheme> = {
  'fable5-coding-agent-premium': {
    from: '#312e81',
    via: '#6366f1',
    to: '#fde68a',
    motif: 'cloud-premium',
    pattern: 'hex',
    accent: '#4338ca',
  },
  'japanese-melon-dataset-pack': PACK_THEMES['japanese-melon-dataset'],
  'quality-check-flow-smart-famers': PACK_THEMES['quality-check-smart-farm'],
}

const CREATOR_PALETTE: ThumbnailTheme[] = [
  { from: '#422006', via: '#ea580c', to: '#fed7aa', motif: 'network', pattern: 'diagonal', accent: '#c2410c' },
  { from: '#134e4a', via: '#14b8a6', to: '#99f6e4', motif: 'database', pattern: 'waves', accent: '#0d9488' },
  { from: '#3b0764', via: '#a855f7', to: '#e9d5ff', motif: 'workflow', pattern: 'rings', accent: '#9333ea' },
  { from: '#1c1917', via: '#78716c', to: '#e7e5e4', motif: 'shield', pattern: 'grid', accent: '#57534e' },
  { from: '#052e16', via: '#22c55e', to: '#bbf7d0', motif: 'compass', pattern: 'dots', accent: '#16a34a' },
  { from: '#450a0a', via: '#ef4444', to: '#fecaca', motif: 'layers', pattern: 'hex', accent: '#dc2626' },
  { from: '#172554', via: '#3b82f6', to: '#bfdbfe', motif: 'nodes', pattern: 'diagonal', accent: '#2563eb' },
  { from: '#4a044e', via: '#d946ef', to: '#f5d0fe', motif: 'pulse', pattern: 'waves', accent: '#c026d3' },
  { from: '#292524', via: '#f59e0b', to: '#fde68a', motif: 'beacon', pattern: 'grid', accent: '#d97706' },
  { from: '#164e63', via: '#06b6d4', to: '#cffafe', motif: 'radar', pattern: 'rings', accent: '#0891b2' },
  { from: '#365314', via: '#84cc16', to: '#ecfccb', motif: 'circuit', pattern: 'dots', accent: '#65a30d' },
  { from: '#500724', via: '#f43f5e', to: '#ffe4e6', motif: 'flow', pattern: 'hex', accent: '#e11d48' },
  { from: '#1e1b4b', via: '#818cf8', to: '#e0e7ff', motif: 'archive', pattern: 'diagonal', accent: '#6366f1' },
  { from: '#042f2e', via: '#2dd4bf', to: '#ccfbf1', motif: 'link', pattern: 'waves', accent: '#14b8a6' },
  { from: '#431407', via: '#fb923c', to: '#ffedd5', motif: 'scope', pattern: 'grid', accent: '#ea580c' },
  { from: '#27272a', via: '#a1a1aa', to: '#f4f4f5', motif: 'matrix', pattern: 'hex', accent: '#71717a' },
  { from: '#14532d', via: '#4ade80', to: '#dcfce7', motif: 'bridge', pattern: 'rings', accent: '#22c55e' },
  { from: '#581c87', via: '#c084fc', to: '#f3e8ff', motif: 'orbit', pattern: 'dots', accent: '#a855f7' },
  { from: '#0f172a', via: '#64748b', to: '#e2e8f0', motif: 'signal', pattern: 'diagonal', accent: '#475569' },
  { from: '#7c2d12', via: '#f97316', to: '#ffedd5', motif: 'prism', pattern: 'waves', accent: '#ea580c' },
]

function hashString(value: string): number {
  let hash = 0
  for (let i = 0; i < value.length; i += 1) {
    hash = (hash * 31 + value.charCodeAt(i)) >>> 0
  }
  return hash
}

export function resolveThumbnailTheme(input: {
  packSlug?: string | null
  slug: string
  id: string
  category?: string | null
}): ThumbnailTheme {
  const slugTheme = SLUG_THEMES[input.slug]
  if (slugTheme) return slugTheme

  const pack = input.packSlug?.trim()
  if (pack && pack !== 'custom' && PACK_THEMES[pack]) {
    return PACK_THEMES[pack]
  }

  const idx = hashString(`${input.slug}:${input.id}`) % CREATOR_PALETTE.length
  return CREATOR_PALETTE[idx]
}