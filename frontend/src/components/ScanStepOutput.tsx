import { useLocale } from '../context/LocaleContext'
import {
  localizeScanWarning,
  parseScanStepOutput,
  shouldHideRawScanJson,
} from '../lib/scanStepDisplay'

export function ScanStepOutput({ output }: { output: string }) {
  const { tr, locale } = useLocale()
  const parsed = parseScanStepOutput(output)
  const hideJson = shouldHideRawScanJson(parsed)

  if (!parsed.limited) {
    return <pre className="workflow-step-output">{output}</pre>
  }

  const warnings =
    parsed.warningLines.length > 0
      ? parsed.warningLines.map((line) => localizeScanWarning(locale, line))
      : []

  return (
    <div className="mt-3 space-y-3 text-sm">
      <div className="rounded-xl border border-amber-300/80 bg-amber-50 px-4 py-3">
        <div className="flex flex-wrap items-center gap-2">
          <p className="font-bold text-amber-950">{tr('workflowScanLimited')}</p>
          {parsed.statusCode != null && (
            <span className="rounded-md bg-amber-200/80 px-2 py-0.5 font-mono text-xs font-bold text-amber-950">
              HTTP {parsed.statusCode}
            </span>
          )}
        </div>
        {warnings.length > 0 && (
          <ul className="mt-2 list-disc space-y-1 pl-5 font-medium text-amber-950/90">
            {warnings.map((line) => (
              <li key={line}>{line}</li>
            ))}
          </ul>
        )}
      </div>

      <div className="rounded-xl border border-[var(--color-border)] bg-white px-4 py-3">
        <p className="font-semibold text-[var(--color-text)]">{tr('workflowScanStillGet')}</p>
        <ul className="mt-2 list-disc space-y-1 pl-5 font-medium text-readable-muted">
          <li>{tr('workflowScanStill1')}</li>
          <li>{tr('workflowScanStill2')}</li>
          <li>{tr('workflowScanStill3')}</li>
        </ul>
      </div>

      <div className="rounded-xl border border-[var(--color-sage)]/40 bg-[var(--color-surface-overlay)]/50 px-4 py-3">
        <p className="font-semibold text-[var(--color-text)]">{tr('workflowScanFixTitle')}</p>
        <ol className="mt-2 list-decimal space-y-1 pl-5 font-medium text-readable-muted">
          <li>{tr('workflowScanFix1')}</li>
          <li>{tr('workflowScanFix2')}</li>
          <li>{tr('workflowScanFix3')}</li>
        </ol>
      </div>

      {!hideJson && parsed.rawJson && (
        <pre className="workflow-step-output max-h-48 overflow-auto rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)] p-3 text-xs">
          {parsed.rawJson}
        </pre>
      )}
    </div>
  )
}