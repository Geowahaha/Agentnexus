/** Geometric botanical illustration mark — exhibition garden style. */
export function ObollaIcon({ size = 44, className = '' }: { size?: number; className?: string }) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 48 48"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      className={className}
      aria-hidden
    >
      <rect x="1" y="1" width="46" height="46" rx="11" fill="#FAF7F2" stroke="#8B9A7B" strokeWidth="1.5" />
      <rect x="22" y="30" width="4" height="12" rx="1" fill="#B85C38" />
      <polygon points="24,10 38,30 10,30" fill="#6B7F6A" />
      <polygon points="24,16 33,27 15,27" fill="#8B9A7B" />
      <polygon points="24,20 29,25 19,25" fill="#A8B5A0" />
      <circle cx="35" cy="13" r="4.5" fill="#C67B5C" opacity="0.9" />
      <ellipse cx="14" cy="36" rx="6" ry="3" fill="#C9A9A6" opacity="0.55" />
      <path d="M6 40 H42" stroke="#D4C9B8" strokeWidth="1" strokeLinecap="round" />
    </svg>
  )
}

type ObollaMarkProps = {
  showWordmark?: boolean
  showTagline?: boolean
  tagline?: string
  size?: 'sm' | 'md' | 'lg'
}

const SIZES = {
  sm: { icon: 36, word: 'text-lg', tag: 'text-[10px]' },
  md: { icon: 44, word: 'text-xl sm:text-2xl', tag: 'text-[11px]' },
  lg: { icon: 52, word: 'text-2xl sm:text-3xl', tag: 'text-xs' },
} as const

export function ObollaMark({
  showWordmark = true,
  showTagline = false,
  tagline,
  size = 'md',
}: ObollaMarkProps) {
  const s = SIZES[size]

  return (
    <span className="inline-flex items-center gap-3">
      <ObollaIcon size={s.icon} />
      {showWordmark && (
        <span className="flex flex-col leading-none">
          <span
            className={`text-display font-bold tracking-[0.14em] text-[var(--color-text)] ${s.word}`}
          >
            OBOLLA
          </span>
          {showTagline && tagline && (
            <span
              className={`mt-1 font-semibold uppercase tracking-[0.22em] text-[var(--color-sage)] ${s.tag}`}
            >
              {tagline}
            </span>
          )}
        </span>
      )}
    </span>
  )
}