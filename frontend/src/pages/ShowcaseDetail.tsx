import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { api } from '../api/client'
import { BeforeAfterSection } from '../components/BeforeAfterSection'
import type { SkillShowcase } from '../types'
import { useLocale } from '../context/LocaleContext'

export function ShowcaseDetail() {
  const { tr } = useLocale()
  const { showcaseId } = useParams<{ showcaseId: string }>()
  const [showcase, setShowcase] = useState<SkillShowcase | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    if (!showcaseId) return
    api
      .getShowcase(showcaseId)
      .then(setShowcase)
      .catch((err) => setError(err instanceof Error ? err.message : 'Showcase not found'))
      .finally(() => setLoading(false))
  }, [showcaseId])

  if (loading) {
    return <div className="mx-auto max-w-3xl px-4 py-16 text-[var(--color-muted)]">{tr('skillLoading')}</div>
  }

  if (!showcase) {
    return (
      <div className="mx-auto max-w-3xl px-4 py-16">
        <p className="font-medium text-red-800">{error || 'Showcase not found'}</p>
      </div>
    )
  }

  const price = showcase.skill ? Number(showcase.skill.price_usd_per_run) : null
  const estTotal = price != null && !Number.isNaN(price) ? price + 0.12 : null

  return (
    <div className="page-shell mx-auto max-w-3xl">
      <Link to="/" className="text-sm font-medium text-readable-muted hover:text-[var(--color-text)]">
        {tr('showcaseBack')}
      </Link>

      <div className="mt-6 garden-card p-6 sm:p-8">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <span className="rounded-full border border-amber-200 bg-amber-50 px-2.5 py-0.5 text-xs font-semibold text-amber-900">
              {tr('showcaseLiveBadge')}
            </span>
            <h1 className="mt-2 text-2xl font-bold text-[var(--color-text)]">{showcase.title}</h1>
            <a
              href={showcase.site_url}
              target="_blank"
              rel="noopener noreferrer"
              className="mt-2 inline-block text-sm font-semibold text-[var(--color-market-hover)] hover:underline"
            >
              Visit {showcase.site_name} ↗
            </a>
          </div>
          {showcase.metric_value && (
            <div className="rounded-xl border border-amber-200 bg-amber-50 px-4 py-3 text-right">
              <p className="text-xs font-bold uppercase tracking-wide text-amber-800/80">
                {showcase.metric_label || 'Built with'}
              </p>
              <p className="mt-1 font-semibold text-amber-950">{showcase.metric_value}</p>
            </div>
          )}
        </div>

        <p className="mt-5 font-medium leading-relaxed text-readable-muted">{showcase.summary}</p>

        {showcase.workflow_id && (
          <p className="mt-3 text-xs font-medium text-emerald-800">
            {tr('showcaseVerifiedRun')} {showcase.workflow_id.slice(0, 8)}…
          </p>
        )}

        <div className="mt-5 flex flex-wrap gap-1.5">
          {showcase.highlights.map((item) => (
            <span
              key={item}
              className="rounded-md border border-emerald-200/80 bg-emerald-50 px-2 py-0.5 text-xs font-medium text-[var(--color-text)]"
            >
              {item}
            </span>
          ))}
        </div>
      </div>

      {showcase.before_after &&
        (showcase.before_after.bots?.length > 0 ||
          showcase.before_after.score_before ||
          showcase.before_after.fixes_applied?.length > 0) && (
          <div className="mt-6">
            <BeforeAfterSection data={showcase.before_after} />
          </div>
        )}

      {showcase.deliverables.length > 0 && (
        <div className="mt-6 surface-panel p-6">
          <h2 className="form-section-title">{tr('showcaseDeliverables')}</h2>
          <ul className="mt-3 grid gap-2 text-sm font-medium text-[var(--color-text)] sm:grid-cols-2">
            {showcase.deliverables.map((item) => (
              <li key={item} className="flex gap-2">
                <span className="font-bold text-emerald-700">✓</span>
                {item}
              </li>
            ))}
          </ul>
        </div>
      )}

      {showcase.sample_output && (
        <div className="mt-6 rounded-2xl border border-emerald-200 bg-emerald-50/80 p-6">
          <h2 className="text-lg font-semibold text-emerald-950">{tr('showcaseSampleOutput')}</h2>
          <p className="mt-1 text-sm font-medium text-readable-muted">{tr('showcaseSampleDesc')}</p>
          <pre className="workflow-step-output mt-4 max-h-96 overflow-y-auto rounded-lg border border-[var(--color-border)] bg-white p-4">
            {showcase.sample_output}
          </pre>
        </div>
      )}

      {showcase.skill && (
        <div className="mt-8 rounded-2xl border border-violet-200 bg-violet-50/90 p-6 sm:p-8">
          <h2 className="text-lg font-semibold text-[var(--color-text)]">{tr('showcaseBuySkill')}</h2>
          <p className="mt-2 text-sm font-medium text-readable-muted">
            {tr('showcaseBuyDesc')}{' '}
            <span className="font-semibold text-violet-950">{showcase.skill.name}</span>{' '}
            {tr('showcaseBuyDescSuffix')} {showcase.site_name}.
          </p>
          <div className="mt-5 flex flex-wrap items-center gap-4">
            {estTotal != null && (
              <div>
                <p className="font-mono text-lg font-semibold text-[var(--color-market-hover)]">~${estTotal.toFixed(2)}</p>
                <p className="text-xs font-medium text-[var(--color-text-soft)]">{tr('showcaseSkillLlm')}</p>
              </div>
            )}
            <Link
              to={`/expert-skills/${showcase.skill.id}`}
              className="rounded-lg bg-violet-500 px-5 py-2.5 text-sm font-bold text-slate-900 hover:bg-violet-400"
            >
              {tr('pricingRunAudit')}
            </Link>
            <Link
              to="/register"
              state={{ from: { pathname: `/expert-skills/${showcase.skill.id}` } }}
              className="rounded-lg border border-[var(--color-border)] bg-white px-5 py-2.5 text-sm font-medium text-[var(--color-text)] hover:border-[var(--color-sage)]"
            >
              {tr('showcaseSignUp')}
            </Link>
          </div>
        </div>
      )}
    </div>
  )
}