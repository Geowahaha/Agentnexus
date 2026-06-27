import type { SkillAttribution } from '../types'
import { useLocale } from '../context/LocaleContext'

export function AttributionCredits({
  attribution,
  compact = false,
}: {
  attribution: SkillAttribution
  compact?: boolean
}) {
  const { tr } = useLocale()

  if (compact) {
    return (
      <p className="text-xs text-[var(--color-muted)]">
        {attribution.pricing_honesty}{' '}
        {attribution.upstream.map((item, index) => (
          <span key={item.href}>
            {index > 0 ? ' · ' : ''}
            <a
              href={item.href}
              target="_blank"
              rel="noopener noreferrer"
              className="text-emerald-600 hover:text-emerald-700 underline underline-offset-2"
            >
              {item.label}
            </a>
          </span>
        ))}
      </p>
    )
  }

  return (
    <div className="rounded-2xl border border-emerald-200 bg-emerald-50/80 p-5">
      <p className="text-xs font-bold uppercase tracking-widest text-emerald-800">{tr('attrCharterTitle')}</p>
      <p className="mt-2 text-sm font-medium text-[var(--color-text-soft)] leading-relaxed">{attribution.charter_summary}</p>
      <p className="mt-3 text-sm text-[var(--color-muted)]">{attribution.pricing_honesty}</p>

      {attribution.upstream.length > 0 && (
        <>
          <p className="mt-4 text-sm font-semibold text-emerald-900">{tr('attrUpstreamCredits')}</p>
          <ul className="mt-3 space-y-3">
            {attribution.upstream.map((item) => (
              <li key={item.href}>
                <a
                  href={item.href}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-sm font-medium text-[var(--color-market-hover)] hover:underline underline-offset-2"
                >
                  {item.label}
                </a>
                <p className="mt-0.5 text-xs font-medium text-readable-muted">{item.detail}</p>
              </li>
            ))}
          </ul>
        </>
      )}

      <p className="mt-4 text-xs font-medium text-readable-muted">
        <span className="font-semibold text-[var(--color-text-soft)]">{tr('attrObolLayerLabel')}:</span>{' '}
        {attribution.obolla_layer}
      </p>
    </div>
  )
}