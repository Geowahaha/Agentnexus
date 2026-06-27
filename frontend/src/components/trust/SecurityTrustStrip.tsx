import { Link } from 'react-router-dom'
import { useLocale } from '../../context/LocaleContext'

export function SecurityTrustStrip({ compact = false }: { compact?: boolean }) {
  const { tr } = useLocale()

  const items = [
    { icon: '🔐', titleKey: 'trustConsentTitle' as const, descKey: 'trustConsentDesc' as const },
    { icon: '🛡️', titleKey: 'trustCreatorTitle' as const, descKey: 'trustCreatorDesc' as const },
    { icon: '⚖️', titleKey: 'trustClientTitle' as const, descKey: 'trustClientDesc' as const },
  ]

  if (compact) {
    return (
      <div className="flex flex-wrap items-center gap-x-4 gap-y-1 text-xs text-[var(--color-muted)]">
        <span className="font-medium text-emerald-700">{tr('trustSecureRemote')}</span>
        <Link to="/terms" className="hover:text-emerald-800">
          {tr('trustCreatorTos')}
        </Link>
        <Link to="/security" className="hover:text-emerald-800">
          {tr('trustSafetyRisk')}
        </Link>
      </div>
    )
  }

  return (
    <section className="garden-card p-6">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <p className="text-xs font-semibold uppercase tracking-widest text-emerald-700">{tr('trustTitle')}</p>
          <h2 className="mt-1 text-xl font-bold text-[var(--color-text)]">{tr('trustHeading')}</h2>
        </div>
        <Link
          to="/security"
          className="text-sm font-medium text-[var(--color-text-soft)] underline decoration-emerald-400 underline-offset-4 hover:text-emerald-800"
        >
          {tr('trustReadPolicy')}
        </Link>
      </div>
      <div className="mt-5 grid gap-4 sm:grid-cols-3">
        {items.map((item) => (
          <div key={item.titleKey} className="rounded-xl border border-emerald-100 bg-white/80 p-4">
            <span className="text-2xl">{item.icon}</span>
            <p className="mt-2 font-semibold text-[var(--color-text)]">{tr(item.titleKey)}</p>
            <p className="mt-1 text-sm leading-relaxed text-readable-muted">{tr(item.descKey)}</p>
          </div>
        ))}
      </div>
    </section>
  )
}