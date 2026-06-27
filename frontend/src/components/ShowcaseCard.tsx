import { Link } from 'react-router-dom'
import type { SkillShowcase } from '../types'

export function ShowcaseCard({ showcase }: { showcase: SkillShowcase }) {
  const price = showcase.skill ? Number(showcase.skill.price_usd_per_run) : null
  const stats = showcase.stats ?? {}

  return (
    <Link
      to={`/showcases/${showcase.id}`}
      className="group flex flex-col rounded-xl border border-[var(--color-border)]/70 bg-white/90 p-5 transition-all hover:border-[var(--color-sage)]/50 hover:shadow-lg bloom-accent"
    >
      <div className="flex items-start justify-between gap-3">
        <div>
          <div className="flex flex-wrap items-center gap-2">
            <span className="rounded-full bg-rose-100 px-2 py-0.5 text-[10px] font-semibold uppercase text-rose-700">
              ✿ Case study
            </span>
            {showcase.skill?.category && (
              <span className="rounded-full bg-emerald-50 px-2 py-0.5 text-[10px] text-emerald-700 capitalize">
                {showcase.skill.category}
              </span>
            )}
          </div>
          <h3 className="mt-2 font-semibold text-[var(--color-text)] group-hover:text-emerald-800 transition-colors">
            {showcase.title}
          </h3>
          {showcase.site_url && (
            <a
              href={showcase.site_url}
              target="_blank"
              rel="noopener noreferrer"
              onClick={(e) => e.stopPropagation()}
              className="mt-1 inline-block text-sm text-sky-700 hover:text-sky-900"
            >
              {showcase.site_name} ↗
            </a>
          )}
          {!showcase.site_url && showcase.site_name && (
            <p className="mt-1 text-sm text-[var(--color-muted)]">{showcase.site_name}</p>
          )}
        </div>
        {showcase.metric_value && (
          <div className="shrink-0 rounded-lg border border-amber-200 bg-amber-50 px-3 py-2 text-right">
            <p className="text-[10px] uppercase tracking-wide text-amber-700/80">
              {showcase.metric_label || 'Result'}
            </p>
            <p className="mt-0.5 text-xs font-medium text-amber-900">{showcase.metric_value}</p>
          </div>
        )}
      </div>

      <p className="mt-3 flex-1 text-sm leading-relaxed text-[var(--color-muted)] line-clamp-2">
        {showcase.summary}
      </p>

      {Object.keys(stats).length > 0 && (
        <div className="mt-4 grid grid-cols-2 gap-2 text-[11px]">
          {stats.score && (
            <div className="rounded-md bg-emerald-50 px-2 py-1.5">
              <p className="text-[var(--color-muted)]">Score</p>
              <p className="font-medium text-[var(--color-text)]">{stats.score}</p>
            </div>
          )}
          {stats.time_saved && (
            <div className="rounded-md bg-emerald-50 px-2 py-1.5">
              <p className="text-[var(--color-muted)]">Time saved</p>
              <p className="font-medium text-[var(--color-text)]">{stats.time_saved}</p>
            </div>
          )}
          {stats.runtime && (
            <div className="rounded-md bg-emerald-50 px-2 py-1.5">
              <p className="text-[var(--color-muted)]">Runtime</p>
              <p className="font-medium text-[var(--color-text)]">{stats.runtime}</p>
            </div>
          )}
          {stats.deliverables_count && (
            <div className="rounded-md bg-emerald-50 px-2 py-1.5">
              <p className="text-[var(--color-muted)]">Deliverables</p>
              <p className="font-medium text-[var(--color-text)]">{stats.deliverables_count}</p>
            </div>
          )}
        </div>
      )}

      <div className="mt-4 flex items-center justify-between border-t border-emerald-100 pt-3 text-xs">
        {showcase.skill ? (
          <span className="text-emerald-700">{showcase.skill.name}</span>
        ) : (
          <span className="text-[var(--color-muted)]">Expert skill</span>
        )}
        {price != null && !Number.isNaN(price) && (
          <span className="font-mono text-amber-800">${price.toFixed(2)}</span>
        )}
      </div>
    </Link>
  )
}