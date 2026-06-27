import { useCallback, useEffect, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { api } from '../../api/client'
import { useLocale } from '../../context/LocaleContext'
import type { StringKey } from '../../i18n/strings'
import type { PublishReadinessMeta, PublishValueInsight } from '../../types'

type Props = {
  insight: PublishValueInsight | null
  loading?: boolean
  skillId?: string
  token?: string | null
  publishReadiness?: PublishReadinessMeta | null
  currentPrice?: string
  onApplyPrice?: (price: string) => void
  onReadinessChange?: (meta: PublishReadinessMeta | null) => void
  compact?: boolean
}

export function PublishReadinessPanel({
  insight,
  loading = false,
  skillId,
  token,
  publishReadiness,
  currentPrice,
  onApplyPrice,
  onReadinessChange,
  compact = false,
}: Props) {
  const { locale, tr } = useLocale()
  const navigate = useNavigate()
  const [testing, setTesting] = useState(false)
  const [testError, setTestError] = useState('')
  const [readiness, setReadiness] = useState<PublishReadinessMeta | null>(publishReadiness ?? null)

  useEffect(() => {
    setReadiness(publishReadiness ?? null)
  }, [publishReadiness])

  const finalizeTest = useCallback(
    async (workflowId: string) => {
      if (!token || !skillId) return
      try {
        const res = await api.finalizeCreatorTestRun(token, skillId, workflowId)
        const meta = (res.skill?.crew_config as { publish_readiness?: PublishReadinessMeta } | undefined)
          ?.publish_readiness
        if (meta) {
          setReadiness(meta)
          onReadinessChange?.(meta)
        }
      } catch {
        // workflow may still be running
      }
    },
    [token, skillId, onReadinessChange],
  )

  useEffect(() => {
    if (!token || !skillId || !readiness?.test_workflow_id) return
    if (readiness.passed !== null && readiness.passed !== undefined && readiness.status !== 'running') return

    let cancelled = false
    const workflowId = readiness.test_workflow_id

    async function poll() {
      try {
        const wf = await api.getWorkflow(token!, workflowId)
        if (cancelled) return
        if (wf.status === 'running' || wf.status === 'pending' || wf.status === 'waiting_human') {
          setTimeout(poll, 4000)
          return
        }
        await finalizeTest(workflowId)
      } catch {
        if (!cancelled) setTimeout(poll, 5000)
      }
    }

    void poll()
    return () => {
      cancelled = true
    }
  }, [token, skillId, readiness?.test_workflow_id, readiness?.passed, readiness?.status, finalizeTest])

  async function handleTestRun() {
    if (!token || !skillId) return
    setTesting(true)
    setTestError('')
    try {
      const res = await api.creatorSkillTestRun(token, skillId)
      const meta = (res.skill?.crew_config as { publish_readiness?: PublishReadinessMeta } | undefined)
        ?.publish_readiness
      if (meta) {
        setReadiness(meta)
        onReadinessChange?.(meta)
      }
      navigate(`/workflows/${res.workflow_id}`, {
        state: { creatorTestSkillId: skillId },
      })
    } catch (err) {
      setTestError(err instanceof Error ? err.message : 'Could not start test run')
    } finally {
      setTesting(false)
    }
  }

  if (loading) {
    return (
      <div className="garden-card animate-pulse p-4 sm:p-5">
        <div className="h-4 w-2/3 rounded bg-[var(--color-surface-overlay)]" />
        <div className="mt-3 h-16 rounded bg-[var(--color-surface-overlay)]" />
      </div>
    )
  }

  if (!insight) return null

  const trends = locale === 'th' ? insight.trend_signals_th : insight.trend_signals_en
  const valueStory = locale === 'th' ? insight.value_story_th : insight.value_story_en
  const priceRationale = locale === 'th' ? insight.price_rationale_th : insight.price_rationale_en
  const encouragement = locale === 'th' ? insight.encouragement_th : insight.encouragement_en
  const futureFit = locale === 'th' ? insight.future_fit_th : insight.future_fit_en
  const ceiling = insight.max_price_usd ?? insight.pricing_ceiling_usd ?? insight.price_usd
  const priceDiffers = currentPrice && insight.price_usd && currentPrice !== insight.price_usd
  const testPassed = readiness?.passed === true
  const testRunning = readiness?.status === 'running' || readiness?.passed === null
  const tierKey: StringKey =
    insight.value_tier === 'premium'
      ? 'publishValueTierPremium'
      : insight.value_tier === 'strong'
        ? 'publishValueTierStrong'
        : insight.value_tier === 'growing'
          ? 'publishValueTierGrowing'
          : 'publishValueTierStarter'

  return (
    <section className="garden-promise garden-card space-y-4 p-4 sm:p-5">
      <div>
        <p className="text-xs font-bold uppercase tracking-[0.12em] text-[var(--color-sage)]">
          Companion · DNA
        </p>
        <h3 className="mt-1 text-base font-bold text-[var(--color-text)] sm:text-lg">{tr('publishInsightTitle')}</h3>
        {!compact && (
          <p className="mt-1 text-xs font-medium text-readable-muted">{tr('publishInsightDna')}</p>
        )}
      </div>

      {trends.length > 0 && (
        <div>
          <p className="text-xs font-bold uppercase tracking-wide text-[var(--color-text-soft)]">
            {tr('publishInsightTrends')}
          </p>
          <ul className="mt-2 space-y-1.5">
            {trends.slice(0, 3).map((line) => (
              <li key={line} className="flex gap-2 text-sm font-medium leading-snug text-[var(--color-text)]">
                <span className="shrink-0 text-[var(--color-bloom)]">✿</span>
                <span>{line}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {valueStory && (
        <div>
          <p className="text-xs font-bold uppercase tracking-wide text-[var(--color-text-soft)]">
            {tr('publishInsightValue')}
          </p>
          <p className="mt-2 text-sm font-medium leading-relaxed text-readable-muted">{valueStory}</p>
        </div>
      )}

      {typeof insight.value_score === 'number' && (
        <div className="flex flex-wrap items-center gap-2">
          <span className="rounded-full bg-[var(--color-market)]/15 px-3 py-1 text-xs font-bold text-[var(--color-market-hover)]">
            {tr('publishValueScore')}: {insight.value_score}/100
          </span>
          <span className="text-xs font-medium text-readable-muted">{tr(tierKey)}</span>
        </div>
      )}

      <div className="rounded-xl border border-[var(--color-sage)]/35 bg-white/80 p-3 sm:p-4">
        <p className="text-xs font-bold uppercase tracking-wide text-[var(--color-text-soft)]">
          {tr('publishInsightPrice')}
        </p>
        <p className="mt-1 font-mono text-2xl font-bold text-[var(--color-terracotta)]">${insight.price_usd}</p>
        {ceiling && (
          <p className="mt-1 text-xs font-semibold text-[var(--color-text-soft)]">
            {tr('publishPriceCeiling')}: ${ceiling} — {tr('publishPriceCeilingHint')}
          </p>
        )}
        {priceRationale && (
          <p className="mt-2 text-xs font-medium leading-relaxed text-readable-muted">{priceRationale}</p>
        )}
        {priceDiffers && onApplyPrice && (
          <button
            type="button"
            onClick={() => onApplyPrice(insight.price_usd)}
            className="mt-3 rounded-lg border border-[var(--color-market)] px-3 py-2 text-xs font-bold text-[var(--color-market-hover)] hover:bg-[var(--color-market)]/10"
          >
            {tr('publishApplyPrice')}
          </button>
        )}
      </div>

      {futureFit && (
        <p className="text-xs font-medium italic text-[var(--color-text-soft)]">
          <span className="font-bold not-italic text-[var(--color-text)]">{tr('publishInsightFuture')}: </span>
          {futureFit}
        </p>
      )}

      {encouragement && (
        <p className="rounded-lg bg-amber-50/90 px-3 py-2.5 text-sm font-medium text-[var(--color-text)]">
          <span className="font-bold text-[var(--color-coffee)]">{tr('publishInsightEncourage')}: </span>
          {encouragement}
        </p>
      )}

      {skillId && token && (
        <div className="border-t border-[var(--color-border)]/60 pt-4">
          {testPassed ? (
            <p className="mb-3 rounded-lg border border-emerald-300/60 bg-emerald-50 px-3 py-2 text-sm font-semibold text-emerald-900">
              ✓ {tr('publishTestPassed')}
            </p>
          ) : testRunning && readiness?.test_workflow_id ? (
            <div className="mb-3 flex flex-col gap-2 sm:flex-row sm:items-center">
              <p className="text-sm font-medium text-readable-muted">{tr('publishTestPending')}</p>
              <Link
                to={`/workflows/${readiness.test_workflow_id}`}
                className="text-sm font-bold text-[var(--color-market-hover)] hover:underline"
              >
                {tr('publishOpenProgress')} →
              </Link>
            </div>
          ) : null}

          <button
            type="button"
            disabled={testing}
            onClick={() => void handleTestRun()}
            className="touch-target w-full rounded-xl bg-[var(--color-market)] px-4 py-3.5 text-base font-bold text-white shadow-md hover:bg-[var(--color-market-hover)] disabled:opacity-50 sm:text-lg"
          >
            {testing
              ? tr('publishTestRunning')
              : testPassed || testRunning
                ? tr('publishTestRetry')
                : tr('publishTestBtn')}
          </button>
          {testError && (
            <p className="mt-2 text-xs font-medium text-red-700">{testError}</p>
          )}
        </div>
      )}
    </section>
  )
}