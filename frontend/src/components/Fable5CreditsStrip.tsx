import {
  FABLE5_LOCAL_CREDIT_LINE,
  FABLE5_LOCAL_CREDITS,
} from '../config/fable5Credits'

export function Fable5CreditsStrip({ compact = false }: { compact?: boolean }) {
  if (compact) {
    return (
      <p className="text-xs text-[var(--color-muted)]">
        {FABLE5_LOCAL_CREDIT_LINE}{' '}
        {FABLE5_LOCAL_CREDITS.map((item, index) => (
          <span key={item.href}>
            {index > 0 ? ' · ' : ''}
            <a
              href={item.href}
              target="_blank"
              rel="noopener noreferrer"
              className="text-emerald-700 hover:text-emerald-900 underline underline-offset-2"
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
      <p className="text-sm font-medium text-emerald-800">Credits — upstream model & data</p>
      <p className="mt-2 text-sm text-[var(--color-text-soft)] leading-relaxed">{FABLE5_LOCAL_CREDIT_LINE}</p>
      <ul className="mt-4 space-y-3">
        {FABLE5_LOCAL_CREDITS.map((item) => (
          <li key={item.href}>
            <a
              href={item.href}
              target="_blank"
              rel="noopener noreferrer"
              className="text-sm font-medium text-emerald-700 hover:text-emerald-900 underline underline-offset-2"
            >
              {item.label}
            </a>
            <p className="mt-0.5 text-xs text-[var(--color-muted)]">{item.detail}</p>
          </li>
        ))}
      </ul>
    </div>
  )
}