import { useId, type ReactNode } from 'react'
import type { ThumbnailMotif } from '../config/skillThumbnails'

type MotifProps = { accent: string; shadowId: string; gradientId: string }

function ShadowDef({ id }: { id: string }) {
  return (
    <filter id={id} x="-10%" y="-10%" width="120%" height="130%">
      <feDropShadow dx="0" dy="4" stdDeviation="4" floodOpacity="0.25" />
    </filter>
  )
}

function CardShell({ children, accent, shadowId }: { children: ReactNode; accent: string; shadowId: string }) {
  return (
    <g filter={`url(#${shadowId})`}>
      <rect x="28" y="22" width="144" height="96" rx="8" fill="#f8fafc" stroke={accent} strokeWidth="1.2" strokeOpacity="0.35" />
      {children}
    </g>
  )
}

function BrowserChrome({ y = 22 }: { y?: number }) {
  return (
    <>
      <rect x="28" y={y} width="144" height="18" rx="8" fill="#e2e8f0" />
      <rect x="28" y={y + 10} width="144" height="10" fill="#e2e8f0" />
      <circle cx="40" cy={y + 9} r="3" fill="#f87171" />
      <circle cx="50" cy={y + 9} r="3" fill="#fbbf24" />
      <circle cx="60" cy={y + 9} r="3" fill="#4ade80" />
    </>
  )
}

function MotifBotScan({ accent, shadowId }: MotifProps) {
  return (
    <svg viewBox="0 0 200 120" className="h-full w-full" aria-hidden>
      <defs><ShadowDef id={shadowId} /></defs>
      <BrowserChrome />
      <CardShell accent={accent} shadowId={shadowId}>
        <rect x="36" y="48" width="56" height="8" rx="2" fill={accent} fillOpacity="0.2" />
        <rect x="36" y="62" width="88" height="6" rx="2" fill="#cbd5e1" />
        <rect x="36" y="74" width="72" height="6" rx="2" fill="#cbd5e1" />
        <rect x="36" y="86" width="40" height="14" rx="4" fill={accent} fillOpacity="0.85" />
        <circle cx="148" cy="72" r="22" fill="none" stroke={accent} strokeWidth="2.5" />
        <path d="M148 58v28M134 72h28" stroke={accent} strokeWidth="2" strokeLinecap="round" />
        <circle cx="148" cy="72" r="8" fill={accent} fillOpacity="0.3" />
      </CardShell>
    </svg>
  )
}

function MotifAutoFix({ accent, shadowId }: MotifProps) {
  return (
    <svg viewBox="0 0 200 120" className="h-full w-full" aria-hidden>
      <defs><ShadowDef id={shadowId} /></defs>
      <CardShell accent={accent} shadowId={shadowId}>
        <rect x="36" y="32" width="128" height="72" rx="4" fill="#0f172a" />
        <rect x="42" y="40" width="48" height="4" rx="1" fill="#4ade80" />
        <rect x="42" y="50" width="72" height="3" rx="1" fill="#64748b" />
        <rect x="42" y="58" width="64" height="3" rx="1" fill="#64748b" />
        <rect x="42" y="66" width="80" height="3" rx="1" fill="#64748b" />
        <path d="M130 78l12-12 8 8 16-20" stroke="#4ade80" strokeWidth="2.5" fill="none" strokeLinecap="round" strokeLinejoin="round" />
        <circle cx="158" cy="48" r="14" fill={accent} fillOpacity="0.9" />
        <path d="M152 48h12M158 42v12" stroke="#fff" strokeWidth="2" strokeLinecap="round" />
      </CardShell>
    </svg>
  )
}

function MotifVisibility({ accent, shadowId }: MotifProps) {
  return (
    <svg viewBox="0 0 200 120" className="h-full w-full" aria-hidden>
      <defs><ShadowDef id={shadowId} /></defs>
      <CardShell accent={accent} shadowId={shadowId}>
        <path d="M48 88 L68 52 L88 72 L108 44 L128 68 L148 38" stroke={accent} strokeWidth="2.5" fill="none" strokeLinecap="round" strokeLinejoin="round" />
        <circle cx="148" cy="38" r="4" fill={accent} />
        <rect x="44" y="92" width="16" height="18" rx="2" fill={accent} fillOpacity="0.5" />
        <rect x="66" y="84" width="16" height="26" rx="2" fill={accent} fillOpacity="0.65" />
        <rect x="88" y="76" width="16" height="34" rx="2" fill={accent} fillOpacity="0.8" />
        <rect x="110" y="68" width="16" height="42" rx="2" fill={accent} />
        <ellipse cx="100" cy="58" rx="28" ry="12" fill="none" stroke={accent} strokeWidth="1.5" strokeOpacity="0.5" />
        <circle cx="100" cy="58" r="6" fill={accent} fillOpacity="0.4" />
      </CardShell>
    </svg>
  )
}

function MotifTerminal({ accent, shadowId }: MotifProps) {
  return (
    <svg viewBox="0 0 200 120" className="h-full w-full" aria-hidden>
      <defs><ShadowDef id={shadowId} /></defs>
      <rect x="24" y="18" width="152" height="104" rx="10" fill="#0f172a" stroke={accent} strokeWidth="1" strokeOpacity="0.4" filter={`url(#${shadowId})`} />
      <rect x="24" y="18" width="152" height="22" rx="10" fill="#1e293b" />
      <circle cx="38" cy="29" r="4" fill="#ef4444" />
      <circle cx="52" cy="29" r="4" fill="#eab308" />
      <circle cx="66" cy="29" r="4" fill="#22c55e" />
      <text x="36" y="58" fill="#4ade80" fontSize="9" fontFamily="ui-monospace, monospace">{'>'} implement</text>
      <text x="36" y="72" fill="#94a3b8" fontSize="8" fontFamily="ui-monospace, monospace">  plan · review</text>
      <text x="36" y="86" fill={accent} fontSize="8" fontFamily="ui-monospace, monospace">  QA: READY</text>
      <rect x="36" y="94" width="8" height="12" fill="#4ade80" opacity="0.8">
        <animate attributeName="opacity" values="0.8;0.2;0.8" dur="1.2s" repeatCount="indefinite" />
      </rect>
    </svg>
  )
}

function MotifSeoChart({ accent, shadowId, gradientId }: MotifProps) {
  return (
    <svg viewBox="0 0 200 120" className="h-full w-full" aria-hidden>
      <defs>
        <ShadowDef id={shadowId} />
        <linearGradient id={gradientId} x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor={accent} stopOpacity="0.5" />
          <stop offset="100%" stopColor={accent} stopOpacity="0.05" />
        </linearGradient>
      </defs>
      <CardShell accent={accent} shadowId={shadowId}>
        <path d="M44 92 L44 72 L64 68 L84 58 L104 62 L124 42 L144 48 L156 32 L156 92 Z" fill={`url(#${gradientId})`} />
        <path d="M44 72 L64 68 L84 58 L104 62 L124 42 L144 48 L156 32" stroke={accent} strokeWidth="2.5" fill="none" strokeLinecap="round" strokeLinejoin="round" />
        <text x="44" y="38" fill={accent} fontSize="14" fontWeight="700" fontFamily="system-ui">88</text>
        <text x="68" y="38" fill="#64748b" fontSize="8" fontFamily="system-ui">/ 100</text>
      </CardShell>
    </svg>
  )
}

function MotifGreenhouse({ accent, shadowId }: MotifProps) {
  return (
    <svg viewBox="0 0 200 120" className="h-full w-full" aria-hidden>
      <defs><ShadowDef id={shadowId} /></defs>
      <path d="M40 92 L40 52 L100 28 L160 52 L160 92 Z" fill="#ecfccb" stroke={accent} strokeWidth="1.5" filter={`url(#${shadowId})`} />
      <path d="M40 52 L100 28 L160 52" fill="none" stroke={accent} strokeWidth="1.5" />
      <line x1="70" y1="44" x2="70" y2="92" stroke={accent} strokeWidth="1" strokeOpacity="0.4" />
      <line x1="100" y1="36" x2="100" y2="92" stroke={accent} strokeWidth="1" strokeOpacity="0.4" />
      <line x1="130" y1="44" x2="130" y2="92" stroke={accent} strokeWidth="1" strokeOpacity="0.4" />
      <ellipse cx="100" cy="78" rx="22" ry="14" fill="#84cc16" fillOpacity="0.7" stroke={accent} strokeWidth="1" />
      <path d="M88 78 Q100 62 112 78" fill="#65a30d" />
      <rect x="148" y="64" width="28" height="20" rx="3" fill="#f8fafc" stroke={accent} strokeWidth="1" />
      <text x="154" y="78" fill={accent} fontSize="7" fontFamily="system-ui">28C</text>
    </svg>
  )
}

function MotifSmartSensors({ accent, shadowId }: MotifProps) {
  return (
    <svg viewBox="0 0 200 120" className="h-full w-full" aria-hidden>
      <defs><ShadowDef id={shadowId} /></defs>
      <rect x="32" y="70" width="136" height="28" rx="4" fill="#a7f3d0" fillOpacity="0.5" />
      <rect x="48" y="48" width="24" height="36" rx="3" fill="#f8fafc" stroke={accent} strokeWidth="1.2" filter={`url(#${shadowId})`} />
      <rect x="88" y="40" width="24" height="44" rx="3" fill="#f8fafc" stroke={accent} strokeWidth="1.2" filter={`url(#${shadowId})`} />
      <rect x="128" y="52" width="24" height="32" rx="3" fill="#f8fafc" stroke={accent} strokeWidth="1.2" filter={`url(#${shadowId})`} />
      <circle cx="60" cy="58" r="6" fill={accent} fillOpacity="0.3" />
      <path d="M56 68h8" stroke={accent} strokeWidth="1.5" strokeLinecap="round" />
      <circle cx="100" cy="52" r="6" fill={accent} fillOpacity="0.3" />
      <path d="M96 68h8" stroke={accent} strokeWidth="1.5" strokeLinecap="round" />
      <circle cx="140" cy="62" r="6" fill={accent} fillOpacity="0.3" />
      <path d="M44 84h112" stroke={accent} strokeWidth="1" strokeDasharray="4 3" strokeOpacity="0.6" />
    </svg>
  )
}

function MotifYoutube({ accent, shadowId }: MotifProps) {
  return (
    <svg viewBox="0 0 200 120" className="h-full w-full" aria-hidden>
      <defs><ShadowDef id={shadowId} /></defs>
      <rect x="32" y="28" width="136" height="76" rx="8" fill="#0f172a" filter={`url(#${shadowId})`} />
      <rect x="40" y="36" width="120" height="52" rx="4" fill="#1e293b" />
      <polygon points="88,48 88,76 112,62" fill={accent} />
      <rect x="40" y="92" width="80" height="6" rx="2" fill="#94a3b8" fillOpacity="0.5" />
      <rect x="40" y="102" width="56" height="4" rx="2" fill="#64748b" fillOpacity="0.4" />
    </svg>
  )
}

function MotifReel({ accent, shadowId }: MotifProps) {
  return (
    <svg viewBox="0 0 200 120" className="h-full w-full" aria-hidden>
      <defs><ShadowDef id={shadowId} /></defs>
      <rect x="72" y="14" width="56" height="96" rx="10" fill="#0f172a" stroke={accent} strokeWidth="1.5" filter={`url(#${shadowId})`} />
      <rect x="78" y="22" width="44" height="72" rx="4" fill="#1e293b" />
      <polygon points="92,42 92,74 110,58" fill={accent} />
      <rect x="82" y="98" width="36" height="4" rx="2" fill="#64748b" />
    </svg>
  )
}

function MotifImagePost({ accent, shadowId }: MotifProps) {
  return (
    <svg viewBox="0 0 200 120" className="h-full w-full" aria-hidden>
      <defs><ShadowDef id={shadowId} /></defs>
      <CardShell accent={accent} shadowId={shadowId}>
        <rect x="40" y="34" width="72" height="56" rx="4" fill="#e2e8f0" />
        <circle cx="58" cy="50" r="8" fill="#fbbf24" fillOpacity="0.8" />
        <path d="M40 78 L60 58 L76 70 L92 48 L112 78 Z" fill={accent} fillOpacity="0.45" />
        <rect x="118" y="40" width="44" height="4" rx="2" fill="#cbd5e1" />
        <rect x="118" y="50" width="36" height="3" rx="1" fill="#e2e8f0" />
        <rect x="118" y="58" width="40" height="3" rx="1" fill="#e2e8f0" />
      </CardShell>
    </svg>
  )
}

function MotifShortPost({ accent, shadowId }: MotifProps) {
  return (
    <svg viewBox="0 0 200 120" className="h-full w-full" aria-hidden>
      <defs><ShadowDef id={shadowId} /></defs>
      <CardShell accent={accent} shadowId={shadowId}>
        <rect x="44" y="36" width="112" height="8" rx="2" fill={accent} fillOpacity="0.35" />
        <rect x="44" y="52" width="96" height="5" rx="2" fill="#cbd5e1" />
        <rect x="44" y="62" width="104" height="5" rx="2" fill="#cbd5e1" />
        <rect x="44" y="72" width="80" height="5" rx="2" fill="#cbd5e1" />
        <rect x="44" y="82" width="88" height="5" rx="2" fill="#cbd5e1" />
        <line x1="52" y1="96" x2="120" y2="96" stroke={accent} strokeWidth="2" strokeLinecap="round" />
      </CardShell>
    </svg>
  )
}

function MotifCloudPremium({ accent, shadowId }: MotifProps) {
  return (
    <svg viewBox="0 0 200 120" className="h-full w-full" aria-hidden>
      <defs><ShadowDef id={shadowId} /></defs>
      <path d="M60 72 Q60 52 80 52 Q88 36 108 40 Q128 36 132 56 Q152 56 152 72 Q152 88 132 88 L72 88 Q60 88 60 72 Z" fill="#f8fafc" stroke={accent} strokeWidth="1.5" filter={`url(#${shadowId})`} />
      <rect x="88" y="58" width="40" height="28" rx="4" fill="#312e81" />
      <rect x="94" y="66" width="28" height="3" rx="1" fill="#818cf8" />
      <rect x="94" y="74" width="20" height="3" rx="1" fill="#6366f1" />
      <polygon points="100,48 108,56 116,48 108,40" fill={accent} />
    </svg>
  )
}

function MotifAbstract({ accent, shadowId, variant }: MotifProps & { variant: number }) {
  const shapes = [
    () => (
      <>
        <circle cx="70" cy="60" r="18" fill="none" stroke={accent} strokeWidth="2" />
        <circle cx="130" cy="60" r="18" fill="none" stroke={accent} strokeWidth="2" />
        <line x1="88" y1="60" x2="112" y2="60" stroke={accent} strokeWidth="2" />
      </>
    ),
    () => (
      <>
        <rect x="52" y="44" width="96" height="48" rx="6" fill="#f8fafc" stroke={accent} strokeWidth="1.5" />
        <rect x="60" y="54" width="32" height="28" rx="3" fill={accent} fillOpacity="0.25" />
        <rect x="100" y="54" width="40" height="6" rx="2" fill="#cbd5e1" />
        <rect x="100" y="66" width="32" height="6" rx="2" fill="#cbd5e1" />
      </>
    ),
    () => <path d="M50 88 L80 40 L110 70 L140 36 L170 88 Z" fill={accent} fillOpacity="0.2" stroke={accent} strokeWidth="1.5" />,
    () => (
      <>
        <circle cx="100" cy="60" r="32" fill="none" stroke={accent} strokeWidth="1.5" strokeOpacity="0.4" />
        <circle cx="100" cy="60" r="20" fill="none" stroke={accent} strokeWidth="2" />
        <circle cx="100" cy="60" r="6" fill={accent} />
      </>
    ),
    () => (
      <>
        {[0, 1, 2, 3].map((i) => (
          <rect key={i} x={56 + i * 22} y={48 + (i % 2) * 12} width="16" height="36" rx="3" fill={accent} fillOpacity={0.25 + i * 0.15} />
        ))}
      </>
    ),
  ]
  const Shape = shapes[variant % shapes.length]
  return (
    <svg viewBox="0 0 200 120" className="h-full w-full" aria-hidden>
      <defs><ShadowDef id={shadowId} /></defs>
      <g filter={`url(#${shadowId})`}>
        <Shape />
      </g>
    </svg>
  )
}

const ABSTRACT_MOTIFS: ThumbnailMotif[] = [
  'network', 'database', 'workflow', 'shield', 'compass', 'layers', 'nodes', 'pulse',
  'beacon', 'radar', 'circuit', 'flow', 'archive', 'link', 'scope', 'matrix', 'bridge', 'orbit', 'signal', 'prism',
]

function abstractVariant(motif: ThumbnailMotif): number {
  const idx = ABSTRACT_MOTIFS.indexOf(motif)
  return idx >= 0 ? idx : 0
}

export function ThumbnailMotifArt({ motif, accent }: { motif: ThumbnailMotif; accent: string; compact?: boolean }) {
  const uid = useId().replace(/:/g, '')
  const shadowId = `ts-${uid}`
  const gradientId = `tg-${uid}`
  const props: MotifProps = { accent, shadowId, gradientId }

  switch (motif) {
    case 'bot-scan': return <MotifBotScan {...props} />
    case 'auto-fix': return <MotifAutoFix {...props} />
    case 'visibility': return <MotifVisibility {...props} />
    case 'terminal': return <MotifTerminal {...props} />
    case 'seo-chart': return <MotifSeoChart {...props} />
    case 'greenhouse': return <MotifGreenhouse {...props} />
    case 'smart-sensors': return <MotifSmartSensors {...props} />
    case 'youtube': return <MotifYoutube {...props} />
    case 'reel': return <MotifReel {...props} />
    case 'image-post': return <MotifImagePost {...props} />
    case 'short-post': return <MotifShortPost {...props} />
    case 'cloud-premium': return <MotifCloudPremium {...props} />
    default:
      return <MotifAbstract {...props} variant={abstractVariant(motif)} />
  }
}