import { Link } from 'react-router-dom'
import type { SkillInputMode } from '../../config/expertSkillMeta'
import { useLocale } from '../../context/LocaleContext'

export function RemoteSupportConsent({
  checked,
  onChange,
  disabled = false,
  inputMode = 'task',
}: {
  checked: boolean
  onChange: (value: boolean) => void
  disabled?: boolean
  inputMode?: SkillInputMode
}) {
  const { tr } = useLocale()
  const copy = inputMode === 'url' ? tr('consentUrl') : tr('consentTask')

  return (
    <label className="flex cursor-pointer gap-3 rounded-xl border border-[var(--color-border)] bg-white p-4">
      <input
        type="checkbox"
        checked={checked}
        disabled={disabled}
        onChange={(e) => onChange(e.target.checked)}
        className="mt-1 h-4 w-4 rounded border-[var(--color-border)] accent-[var(--color-market)]"
      />
      <span className="text-sm font-medium leading-relaxed text-readable-muted">
        {copy} {tr('consentAccept')}{' '}
        <Link to="/terms" className="font-semibold text-[var(--color-market-hover)] hover:underline">
          {tr('consentTerms')}
        </Link>
        , {tr('consentLiability')}{' '}
        <Link to="/security" className="font-semibold text-[var(--color-market-hover)] hover:underline">
          {tr('consentSafety')}
        </Link>
        .
      </span>
    </label>
  )
}