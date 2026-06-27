import { resolveThumbnailTheme, type ThumbnailPattern } from '../config/skillThumbnails'
import { ThumbnailMotifArt } from './thumbnailMotifs'

function PatternOverlay({ pattern, accent }: { pattern: ThumbnailPattern; accent: string }) {
  const opacity = 'opacity-[0.12]'
  if (pattern === 'rings') {
    return (
      <svg className={`pointer-events-none absolute inset-0 h-full w-full ${opacity}`} aria-hidden>
        <circle cx="78%" cy="22%" r="56" fill="none" stroke={accent} strokeWidth="2" />
        <circle cx="88%" cy="38%" r="34" fill="none" stroke={accent} strokeWidth="1.5" />
        <circle cx="12%" cy="78%" r="42" fill="none" stroke={accent} strokeWidth="2" />
      </svg>
    )
  }
  if (pattern === 'dots') {
    return (
      <svg className={`pointer-events-none absolute inset-0 h-full w-full ${opacity}`} aria-hidden>
        {Array.from({ length: 24 }, (_, i) => (
          <circle
            key={i}
            cx={`${8 + (i % 6) * 16}%`}
            cy={`${10 + Math.floor(i / 6) * 22}%`}
            r="2.5"
            fill={accent}
          />
        ))}
      </svg>
    )
  }
  if (pattern === 'grid') {
    return (
      <svg className={`pointer-events-none absolute inset-0 h-full w-full ${opacity}`} aria-hidden>
        {Array.from({ length: 7 }, (_, i) => (
          <line key={`v${i}`} x1={`${i * 16}%`} y1="0" x2={`${i * 16}%`} y2="100%" stroke={accent} strokeWidth="1" />
        ))}
        {Array.from({ length: 5 }, (_, i) => (
          <line key={`h${i}`} x1="0" y1={`${i * 22}%`} x2="100%" y2={`${i * 22}%`} stroke={accent} strokeWidth="1" />
        ))}
      </svg>
    )
  }
  if (pattern === 'waves') {
    return (
      <svg className={`pointer-events-none absolute inset-0 h-full w-full ${opacity}`} viewBox="0 0 200 120" preserveAspectRatio="none" aria-hidden>
        <path d="M0,60 Q50,20 100,60 T200,60 L200,120 L0,120 Z" fill={accent} />
        <path d="M0,90 Q60,50 120,90 T200,90 L200,120 L0,120 Z" fill={accent} fillOpacity="0.5" />
      </svg>
    )
  }
  if (pattern === 'hex') {
    return (
      <svg className={`pointer-events-none absolute inset-0 h-full w-full ${opacity}`} aria-hidden>
        <polygon points="170,20 195,35 195,65 170,80 145,65 145,35" fill="none" stroke={accent} strokeWidth="2" />
        <polygon points="30,70 55,85 55,115 30,130 5,115 5,85" fill="none" stroke={accent} strokeWidth="1.5" />
      </svg>
    )
  }
  return (
    <svg className={`pointer-events-none absolute inset-0 h-full w-full ${opacity}`} aria-hidden>
      <line x1="0" y1="100%" x2="100%" y2="0" stroke={accent} strokeWidth="2" />
      <line x1="0" y1="70%" x2="70%" y2="0" stroke={accent} strokeWidth="1.5" />
      <line x1="30%" y1="100%" x2="100%" y2="30%" stroke={accent} strokeWidth="1.5" />
    </svg>
  )
}

export interface AgentThumbnailProps {
  packSlug?: string | null
  slug: string
  id: string
  name?: string
  category?: string | null
  featured?: boolean
  compact?: boolean
  className?: string
}

export function AgentThumbnail({
  packSlug,
  slug,
  id,
  name,
  category,
  featured = false,
  compact = false,
  className = '',
}: AgentThumbnailProps) {
  const theme = resolveThumbnailTheme({ packSlug, slug, id, category })
  const heightClass = compact ? 'h-12 w-12 rounded-lg' : featured ? 'h-48 w-full sm:h-auto sm:w-48' : 'h-40 w-full'

  // Use real professional photo when available (matches the skill feature)
  if (theme.image) {
    return (
      <div className={`relative shrink-0 overflow-hidden ${heightClass} ${className}`} aria-hidden>
        <img 
          src={theme.image} 
          alt={name || 'skill'} 
          className="absolute inset-0 h-full w-full object-cover" 
          loading="lazy"
        />
        {/* Subtle professional overlay to keep garden warmth */}
        <div className="absolute inset-0 bg-gradient-to-br from-black/25 via-black/10 to-black/30" />
        {!compact && name && (
          <div className="pointer-events-none absolute inset-x-0 bottom-0 bg-gradient-to-t from-black/60 via-black/30 to-transparent px-3 pb-2.5 pt-8">
            <span className="block text-center text-[10px] font-semibold uppercase tracking-wider text-white/95 line-clamp-1 sm:text-xs">
              {name.split(' ').slice(0, 4).join(' ')}
            </span>
          </div>
        )}
      </div>
    )
  }

  // Fallback to original gradient + motif style
  return (
    <div
      className={`relative shrink-0 overflow-hidden ${heightClass} ${className}`}
      style={{
        background: `linear-gradient(145deg, ${theme.from} 0%, ${theme.via} 48%, ${theme.to} 100%)`,
      }}
      aria-hidden
    >
      <PatternOverlay pattern={theme.pattern} accent={theme.accent} />
      <div className={`absolute inset-0 ${compact ? 'p-1' : 'p-2 sm:p-3'}`}>
        <ThumbnailMotifArt motif={theme.motif} accent={theme.accent} compact={compact} />
      </div>
      {!compact && name && (
        <div className="pointer-events-none absolute inset-x-0 bottom-0 bg-gradient-to-t from-black/50 via-black/20 to-transparent px-3 pb-2.5 pt-8">
          <span className="block text-center text-[10px] font-semibold uppercase tracking-wider text-white/95 line-clamp-1 sm:text-xs">
            {name.split(' ').slice(0, 4).join(' ')}
          </span>
        </div>
      )}
      <div className="pointer-events-none absolute inset-0 bg-gradient-to-br from-white/10 via-transparent to-black/10" />
    </div>
  )
}