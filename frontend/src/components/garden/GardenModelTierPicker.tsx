import type { GardenModelTier } from '../../types'

type Props = {
  tiers: GardenModelTier[]
  selectedId: string
  locale: 'th' | 'en'
  basePriceUsd: string
  disabled?: boolean
  onSelect: (tierId: string) => void
  labels: {
    title: string
    hint: string
    perRun: string
    base: string
    addon: string
    unavailable: string
  }
}

export function GardenModelTierPicker({
  tiers,
  selectedId,
  locale,
  basePriceUsd,
  disabled,
  onSelect,
  labels,
}: Props) {
  return (
    <div className="mt-6">
      <h4 className="text-lg font-semibold text-[var(--color-text)]">{labels.title}</h4>
      <p className="mt-1 text-sm font-medium text-readable-muted">{labels.hint}</p>
      <p className="mt-2 text-xs font-medium text-[var(--color-text-soft)]">
        {labels.base}: ${basePriceUsd} · {labels.addon}
      </p>
      <div className="mt-4 grid gap-3 sm:grid-cols-2">
        {tiers.map((tier) => {
          const selected = tier.id === selectedId
          const label = locale === 'th' ? tier.label_th : tier.label_en
          const engines = locale === 'th' ? tier.engines_th : tier.engines_en
          const hint = locale === 'th' ? tier.hint_th : tier.hint_en
          const unavailableReason =
            locale === 'th' ? tier.unavailable_reason_th : tier.unavailable_reason_en
          return (
            <button
              key={tier.id}
              type="button"
              disabled={disabled || !tier.available}
              onClick={() => onSelect(tier.id)}
              className={`rounded-xl border-2 p-4 text-left transition-colors ${
                selected
                  ? 'border-[var(--color-sage)] bg-[var(--color-surface-overlay)] shadow-sm'
                  : tier.available
                    ? 'border-[var(--color-border)] hover:border-[var(--color-sage)]/50'
                    : 'cursor-not-allowed border-[var(--color-border)] bg-[var(--color-surface)] opacity-60'
              }`}
            >
              <div className="flex items-start justify-between gap-2">
                <p className="text-base font-bold text-[var(--color-text)]">{label}</p>
                <span className="shrink-0 rounded-full bg-[var(--color-market)]/10 px-2.5 py-0.5 text-sm font-bold text-[var(--color-market-hover)]">
                  ${tier.suggested_price_usd}
                </span>
              </div>
              <p className="mt-1 text-sm font-medium text-readable-muted">{engines}</p>
              <p className="mt-2 text-xs text-[var(--color-text-soft)]">{hint}</p>
              {!tier.available && unavailableReason && (
                <p className="mt-2 text-xs font-medium text-amber-800">
                  {labels.unavailable}: {unavailableReason}
                </p>
              )}
              {tier.addon_usd !== '0.00' && (
                <p className="mt-2 text-xs font-medium text-[var(--color-muted)]">
                  +${tier.addon_usd} {labels.perRun}
                </p>
              )}
            </button>
          )
        })}
      </div>
    </div>
  )
}