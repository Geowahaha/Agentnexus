import { Link } from 'react-router-dom'
import { useLocale } from '../../context/LocaleContext'

function initials(name: string): string {
  return name
    .split(/\s+/)
    .slice(0, 2)
    .map((p) => p[0]?.toUpperCase() ?? '')
    .join('')
}

export function CreatorAttribution({
  ownerId,
  ownerName,
  size = 'md',
}: {
  ownerId: string
  ownerName: string
  size?: 'sm' | 'md'
}) {
  const compact = size === 'sm'
  const { tr } = useLocale()

  return (
    <Link
      to={`/creators/${ownerId}`}
      className={`inline-flex items-center gap-2 rounded-full border border-[var(--color-border)] bg-[var(--color-surface)] transition-colors hover:border-slate-500 hover:bg-[var(--color-surface-overlay)] ${
        compact ? 'px-2 py-1' : 'px-3 py-1.5'
      }`}
    >
      <span
        className={`flex shrink-0 items-center justify-center rounded-full bg-gradient-to-br from-[var(--color-market)] to-[var(--color-accent)] font-bold text-black ${
          compact ? 'h-6 w-6 text-[10px]' : 'h-8 w-8 text-xs'
        }`}
      >
        {initials(ownerName)}
      </span>
      <span className={compact ? 'text-xs text-[var(--color-text-soft)]' : 'text-sm text-[var(--color-text-soft)]'}>
        <span className="text-[var(--color-muted)]">{tr('skillBy')} </span>
        <span className="font-medium text-[var(--color-text)]">{ownerName}</span>
      </span>
    </Link>
  )
}