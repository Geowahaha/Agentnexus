import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../api/client'
import { ShowcaseCard } from '../components/ShowcaseCard'
import { DnaVerifiedPanel } from '../components/trust/DnaVerifiedPanel'
import { useLocale } from '../context/LocaleContext'
import { FABLE5_PREMIUM_SKILL_ID } from '../config/featuredSkills'
import {
  OBOLLA_CHARTER_RULES_EN,
  OBOLLA_CHARTER_RULES_TH,
  OBOLLA_COMPANION_TH,
  OBOLLA_DNA,
  OBOLLA_MANIFESTO_EN,
  OBOLLA_MANIFESTO_TH,
} from '../config/obollaManifesto'
import type { CommunityLeaderboardEntry, CommunityVision, SkillShowcase } from '../types'

const COMPANION_EN = "We're beside you in building it."

export function Community() {
  const { locale, tr } = useLocale()
  const [vision, setVision] = useState<CommunityVision | null>(null)
  const [leaderboard, setLeaderboard] = useState<CommunityLeaderboardEntry[]>([])
  const [showcases, setShowcases] = useState<SkillShowcase[]>([])
  const [loading, setLoading] = useState(true)

  const manifesto =
    locale === 'th'
      ? (vision?.manifesto_th ?? OBOLLA_MANIFESTO_TH)
      : (vision?.manifesto_en ?? vision?.mission ?? OBOLLA_MANIFESTO_EN)

  const companion = locale === 'th' ? (vision?.companion_th ?? OBOLLA_COMPANION_TH) : COMPANION_EN

  const dnaLines =
    locale === 'th'
      ? (vision?.dna_th ?? OBOLLA_DNA.map((d) => d.th))
      : (vision?.dna ?? OBOLLA_DNA.map((d) => d.en))

  const charterRules =
    locale === 'th' ? [...OBOLLA_CHARTER_RULES_TH] : (vision?.charter_rules ?? [...OBOLLA_CHARTER_RULES_EN])

  useEffect(() => {
    Promise.all([
      api.getCommunityVision().catch(() => null),
      api.getCommunityLeaderboard().catch(() => []),
      api.listShowcases({ featured_only: true }).catch(() => api.listShowcases().catch(() => [])),
    ])
      .then(([v, lb, sc]) => {
        setVision(v)
        setLeaderboard(lb)
        setShowcases(sc.slice(0, 10))
      })
      .finally(() => setLoading(false))
  }, [])

  return (
    <div className="page-shell mx-auto max-w-7xl">
      <p className="text-xs font-bold uppercase tracking-[0.2em] text-[var(--color-sage)]">
        {tr('communityEyebrow')}
      </p>
      <h1 className="mt-2 max-w-4xl text-xl font-bold leading-snug text-[var(--color-text)] sm:text-3xl">
        {manifesto}
      </h1>
      <p className="mt-3 text-sm font-medium italic text-[var(--color-text-soft)]">{companion}</p>

      <div className="mt-6 grid gap-4 sm:mt-8 sm:gap-6 lg:grid-cols-3">
        <section className="garden-card lg:col-span-2 p-4 sm:p-6">
          <h2 className="text-sm font-bold uppercase tracking-wide text-[var(--color-text-soft)]">
            {tr('communityDna')}
          </h2>
          <ul className="mt-4 space-y-3">
            {dnaLines.map((line) => (
              <li key={line} className="flex gap-3 text-sm font-medium text-readable-muted">
                <span className="text-[var(--color-bloom)] shrink-0">✿</span>
                <span className="text-[var(--color-text)]">{line}</span>
              </li>
            ))}
          </ul>

          <details className="mt-6 sm:mt-8 sm:hidden">
            <summary className="cursor-pointer text-sm font-bold uppercase tracking-wide text-[var(--color-text-soft)]">
              {tr('communityCharter')}
            </summary>
            <ul className="mt-3 space-y-2">
              {charterRules.map((rule) => (
                <li key={rule} className="text-sm font-medium text-readable-muted">
                  ✓ {rule}
                </li>
              ))}
            </ul>
          </details>
          <div className="mt-8 hidden sm:block">
            <h2 className="text-sm font-bold uppercase tracking-wide text-[var(--color-text-soft)]">
              {tr('communityCharter')}
            </h2>
            <ul className="mt-4 space-y-2">
              {charterRules.map((rule) => (
                <li key={rule} className="text-sm font-medium text-readable-muted">
                  ✓ {rule}
                </li>
              ))}
            </ul>
          </div>
        </section>

        <section className="coffee-corner p-4 sm:p-6">
          <h2 className="text-sm font-bold uppercase tracking-wide text-[var(--color-coffee)]">
            {tr('communityEarn')}
          </h2>
          <ol className="mt-4 space-y-4 text-sm font-medium text-readable-muted">
            <li>
              <span className="font-bold text-[var(--color-text)]">1.</span> {tr('communityEarn1')}{' '}
              <Link to="/creator" className="font-semibold text-[var(--color-market-hover)] hover:underline">
                {tr('communityEarn1Link')}
              </Link>{' '}
              {tr('communityEarn1Rest')}
            </li>
            <li>
              <span className="font-bold text-[var(--color-text)]">2.</span> {tr('communityEarn2')}{' '}
              <strong className="text-[var(--color-text)]">{tr('communityEarn2Bold')}</strong>{' '}
              {tr('communityEarn2Rest')}
            </li>
            <li>
              <span className="font-bold text-[var(--color-text)]">3.</span> {tr('communityEarn3')}
            </li>
          </ol>
          <Link
            to="/garden"
            className="touch-target mt-5 block rounded-xl bg-[var(--color-market)] px-4 py-3 text-center text-sm font-bold text-white hover:bg-[var(--color-market-hover)] sm:mt-6 sm:rounded-lg sm:py-2.5"
          >
            {tr('communityGardenBtn')}
          </Link>
          <Link
            to={`/expert-skills/${FABLE5_PREMIUM_SKILL_ID}`}
            className="touch-target mt-2 block rounded-xl border border-[var(--color-border)] bg-white/80 px-4 py-3 text-center text-sm font-semibold text-[var(--color-text)] hover:bg-white sm:mt-3 sm:rounded-lg sm:py-2.5"
          >
            {tr('communityProBtn')}
          </Link>
        </section>
      </div>

      <DnaVerifiedPanel />

      {!loading && leaderboard.length > 0 && (
        <section className="mt-10">
          <h2 className="text-xl font-bold text-[var(--color-text)]">{tr('communityLeaderboard')}</h2>
          <p className="mt-1 text-sm font-medium text-readable-muted">{tr('communityLeaderboardDesc')}</p>
          <div className="mt-5 grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
            {leaderboard.map((row, index) => (
              <Link
                key={row.owner_id}
                to={`/creators/${row.owner_id}`}
                className="rounded-xl border border-[var(--color-border)] bg-[var(--color-surface-raised)] p-4 hover:border-[var(--color-market)]/40"
              >
                <div className="flex items-center gap-3">
                  <span className="flex h-8 w-8 items-center justify-center rounded-full bg-[var(--color-market)]/15 text-sm font-bold text-[var(--color-market-hover)]">
                    {index + 1}
                  </span>
                  <div>
                    <p className="font-semibold text-[var(--color-text)]">{row.owner_name}</p>
                    <p className="text-xs font-medium text-readable-muted">
                      {row.flow_count} flow{locale === 'en' && row.flow_count !== 1 ? 's' : ''}
                      {(row.earning_runs ?? 0) > 0
                        ? ` · ${row.earning_runs} community run${locale === 'en' && row.earning_runs !== 1 ? 's' : ''}`
                        : ''}
                      {row.categories.length > 0 ? ` · ${row.categories.join(', ')}` : ''}
                    </p>
                  </div>
                </div>
                {row.featured_flow && (
                  <p className="mt-3 text-xs text-[var(--color-text-soft)] truncate">{row.featured_flow.name}</p>
                )}
              </Link>
            ))}
          </div>
        </section>
      )}

      {showcases.length > 0 && (
        <section className="mt-12">
          <h2 className="text-xl font-bold text-[var(--color-text)]">{tr('caseStudiesTitle')}</h2>
          <p className="mt-1 text-sm font-medium text-readable-muted">{tr('caseStudiesDesc')}</p>
          <div className="mt-5 grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
            {showcases.map((showcase) => (
              <ShowcaseCard key={showcase.id} showcase={showcase} />
            ))}
          </div>
        </section>
      )}
    </div>
  )
}