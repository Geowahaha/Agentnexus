import { useLocale } from '../../context/LocaleContext'

const AIBOTAUTH_HOME = 'https://aibotauth.com'
const CRAWLTEST_POC = 'https://aibotauth.com/api/crawltest-poc'

export function AibotauthTrustStrip({ compact = false }: { compact?: boolean }) {
  const { tr } = useLocale()

  if (compact) {
    return (
      <p className="text-xs font-medium text-readable-muted">
        {tr('aibotauthPoweredEyebrow')} ·{' '}
        <a
          href={AIBOTAUTH_HOME}
          target="_blank"
          rel="noopener noreferrer"
          className="font-semibold text-emerald-800 underline decoration-emerald-300 underline-offset-2 hover:text-emerald-900"
        >
          {tr('aibotauthPoweredTitle')}
        </a>
      </p>
    )
  }

  return (
    <section className="garden-card border border-emerald-200/80 bg-gradient-to-br from-emerald-50/90 to-white p-5 sm:p-6">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
        <div className="min-w-0">
          <p className="text-xs font-bold uppercase tracking-[0.18em] text-emerald-700">
            {tr('aibotauthPoweredEyebrow')}
          </p>
          <h2 className="mt-1 text-lg font-bold text-[var(--color-text)] sm:text-xl">
            {tr('aibotauthPoweredTitle')}
          </h2>
          <p className="mt-2 max-w-2xl text-sm leading-relaxed text-readable-muted">
            {tr('aibotauthPoweredDesc')}
          </p>
        </div>
        <div className="flex shrink-0 flex-col gap-2 sm:items-end">
          <a
            href={AIBOTAUTH_HOME}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center justify-center rounded-lg border border-emerald-200 bg-white px-4 py-2 text-sm font-semibold text-emerald-900 shadow-sm hover:bg-emerald-50"
          >
            aibotauth.com →
          </a>
          <a
            href={CRAWLTEST_POC}
            target="_blank"
            rel="noopener noreferrer"
            className="text-sm font-medium text-emerald-800 underline decoration-emerald-300 underline-offset-4 hover:text-emerald-900"
          >
            {tr('aibotauthPoweredLink')}
          </a>
        </div>
      </div>
    </section>
  )
}