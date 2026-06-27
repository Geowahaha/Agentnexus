import { useLocale } from '../context/LocaleContext'
import type { StringKey } from '../i18n/strings'

const STATUS_STYLES: Record<string, string> = {
  completed: 'bg-emerald-100 text-emerald-800 border-emerald-300/60',
  running: 'bg-cyan-100 text-cyan-900 border-cyan-300/60',
  waiting_human: 'bg-amber-100 text-amber-900 border-amber-300/60',
  failed: 'bg-red-100 text-red-800 border-red-300/60',
}

const STATUS_KEYS: Record<string, StringKey> = {
  completed: 'workflowStatusCompleted',
  running: 'workflowStatusRunning',
  waiting_human: 'workflowStatusWaiting',
  failed: 'workflowStatusFailed',
}

export function StatusBadge({ status }: { status: string }) {
  const { tr } = useLocale()
  const style = STATUS_STYLES[status] ?? 'bg-slate-100 text-[var(--color-text-soft)] border-slate-300/60'
  const labelKey = STATUS_KEYS[status]
  const label = labelKey ? tr(labelKey) : status.replace('_', ' ')
  return (
    <span className={`inline-flex rounded-full border px-2.5 py-0.5 text-xs font-semibold ${style}`}>
      {label}
    </span>
  )
}