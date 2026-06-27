import type { ShowcaseBeforeAfter } from '../types'
import { useLocale } from '../context/LocaleContext'

function statusColor(status: string): string {
  const lower = status.toLowerCase()
  if (lower.includes('can read') || lower.includes('full') || lower.includes('ready')) {
    return 'text-emerald-800'
  }
  if (lower.includes('blocked') || lower.includes('401') || lower.includes('522')) {
    return 'text-red-800'
  }
  if (lower.includes('served') || lower.includes('limited') || lower.includes('sketch')) {
    return 'text-amber-900'
  }
  return 'text-[var(--color-text)]'
}

export function BeforeAfterSection({
  data,
  compact = false,
}: {
  data: ShowcaseBeforeAfter
  compact?: boolean
}) {
  const { tr } = useLocale()
  const bots = data.bots ?? []
  const fixes = data.fixes_applied ?? []
  const hasBots = bots.length > 0
  const hasScores = data.score_before || data.score_after
  const hasFixes = fixes.length > 0

  if (!hasBots && !hasScores && !hasFixes) return null

  return (
    <div
      className={
        compact
          ? 'rounded-xl border border-[var(--color-border)] bg-white p-4'
          : 'garden-card p-4 sm:p-6'
      }
    >
      <h2
        className={
          compact
            ? 'text-sm font-bold text-[var(--color-text)]'
            : 'text-lg font-bold text-[var(--color-text)]'
        }
      >
        {tr('skillBeforeAfterTitle')}
      </h2>
      {!compact && (
        <p className="mt-1 text-sm font-medium text-readable-muted">{tr('skillBeforeAfterDesc')}</p>
      )}

      {hasScores && (
        <div className={`flex flex-wrap gap-3 ${compact ? 'mt-3' : 'mt-5'}`}>
          {data.score_before && (
            <div className="min-w-[140px] rounded-xl border border-red-200 bg-red-50 px-4 py-3">
              <p className="text-[10px] font-bold uppercase tracking-wide text-red-800/80">{tr('skillBeforeLabel')}</p>
              <p className="mt-1 font-mono text-base font-semibold leading-snug text-red-950">
                {data.score_before}
              </p>
            </div>
          )}
          {data.score_after && (
            <div className="min-w-[140px] rounded-xl border border-emerald-200 bg-emerald-50 px-4 py-3">
              <p className="text-[10px] font-bold uppercase tracking-wide text-emerald-800/80">{tr('skillAfterLabel')}</p>
              <p className="mt-1 font-mono text-base font-semibold leading-snug text-emerald-950">
                {data.score_after}
              </p>
            </div>
          )}
        </div>
      )}

      {hasBots && (
        <div className={compact ? 'mt-3 overflow-x-auto' : 'mt-5 overflow-x-auto'}>
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-[var(--color-border)] text-left text-xs font-bold uppercase tracking-wide text-[var(--color-text-soft)]">
                <th className="pb-2 pr-4">{tr('skillAiBot')}</th>
                <th className="pb-2 pr-4">{tr('skillBeforeLabel')}</th>
                <th className="pb-2">{tr('skillAfterLabel')}</th>
              </tr>
            </thead>
            <tbody>
              {bots.map((bot) => (
                <tr key={bot.name} className="border-b border-[var(--color-border)]/60">
                  <td className="py-2.5 pr-4 font-semibold text-[var(--color-text)]">{bot.name}</td>
                  <td className={`py-2.5 pr-4 font-medium ${statusColor(bot.before)}`}>{bot.before}</td>
                  <td className={`py-2.5 font-medium ${statusColor(bot.after)}`}>{bot.after}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {hasFixes && (
        <div className={compact ? 'mt-3' : 'mt-5'}>
          <p className="text-xs font-bold uppercase tracking-wide text-[var(--color-text-soft)]">
            {tr('skillFixesApplied')}
          </p>
          <ul className="mt-2 space-y-2 text-sm font-medium text-[var(--color-text)]">
            {fixes.map((fix) => (
              <li key={fix} className="flex gap-2 leading-snug">
                <span className="shrink-0 font-bold text-[var(--color-market-hover)]">→</span>
                <span>{fix}</span>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  )
}