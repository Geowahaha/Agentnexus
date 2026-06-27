import { useLocale } from '../../context/LocaleContext'
import type { Locale } from '../../i18n/strings'

const OPTIONS: { id: Locale; label: string }[] = [
  { id: 'th', label: 'ไทย' },
  { id: 'en', label: 'EN' },
]

export function LanguageSwitcher({ compact = false }: { compact?: boolean }) {
  const { locale, setLocale } = useLocale()

  return (
    <div
      className={`inline-flex rounded-lg border border-[var(--color-border)] bg-white p-0.5 shadow-sm ${
        compact ? 'text-xs' : 'text-sm'
      }`}
      role="group"
      aria-label="Language"
    >
      {OPTIONS.map((opt) => (
        <button
          key={opt.id}
          type="button"
          onClick={() => setLocale(opt.id)}
          className={`rounded-md px-2.5 py-1 font-semibold transition-colors ${
            locale === opt.id
              ? 'bg-[var(--color-market)] text-white shadow-sm'
              : 'text-[var(--color-text-soft)] hover:bg-[var(--color-surface-overlay)] hover:text-[var(--color-text)]'
          }`}
          aria-pressed={locale === opt.id}
        >
          {opt.label}
        </button>
      ))}
    </div>
  )
}