import { useEffect, useMemo, useState } from 'react'
import { Link, useLocation, useParams } from 'react-router-dom'
import { api } from '../api/client'
import { AgentThumbnail } from '../components/AgentThumbnail'
import { ExpertSkillCard } from '../components/ExpertSkillCard'
import { PublishReadinessPanel } from '../components/garden/PublishReadinessPanel'
import { SecurityTrustStrip } from '../components/trust/SecurityTrustStrip'
import { useAuth } from '../context/AuthContext'
import { useLocale } from '../context/LocaleContext'
import type { Agent, CreatorSkillItem, ExpertSkill, PublishReadinessMeta, PublishValueInsight } from '../types'

type GardenWelcomeState = {
  gardenWelcome?: boolean
  newSkillId?: string
  flowName?: string
}

function initials(name: string): string {
  return name
    .split(/\s+/)
    .slice(0, 2)
    .map((p) => p[0]?.toUpperCase() ?? '')
    .join('')
}

export function CreatorProfile() {
  const { ownerId } = useParams<{ ownerId: string }>()
  const { user, token } = useAuth()
  const { locale, tr } = useLocale()
  const location = useLocation()
  const welcomeState = (location.state ?? {}) as GardenWelcomeState
  const gardenWelcome = welcomeState.gardenWelcome === true
  const newSkillId = welcomeState.newSkillId
  const welcomeFlowName = welcomeState.flowName

  const [publicSkills, setPublicSkills] = useState<ExpertSkill[]>([])
  const [ownSkills, setOwnSkills] = useState<CreatorSkillItem[]>([])
  const [agents, setAgents] = useState<Agent[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [valueInsight, setValueInsight] = useState<PublishValueInsight | null>(null)
  const [insightLoading, setInsightLoading] = useState(false)

  const isOwnStore = user?.id === ownerId

  useEffect(() => {
    if (!ownerId) return
    setLoading(true)
    setError('')

    const loads: Promise<void>[] = [
      api
        .listExpertSkills(undefined, locale)
        .then((allSkills) => {
          setPublicSkills(allSkills.filter((s) => s.owner_id === ownerId && s.is_active))
        })
        .catch((err) => {
          throw err
        }),
      api
        .listMarketplaceAgents({})
        .then((allAgents) => {
          setAgents(allAgents.filter((a) => a.owner_id === ownerId && a.is_active))
        })
        .catch(() => {
          setAgents([])
        }),
    ]

    if (isOwnStore && token) {
      loads.push(
        api.getCreatorSkills(token).then((skills) => {
          setOwnSkills(skills)
        }),
      )
    } else {
      setOwnSkills([])
    }

    Promise.all(loads)
      .catch((err) => setError(err instanceof Error ? err.message : 'Failed to load creator'))
      .finally(() => setLoading(false))
  }, [ownerId, isOwnStore, token, locale])

  const displaySkills = useMemo(() => {
    if (isOwnStore && ownSkills.length > 0) return ownSkills
    return publicSkills
  }, [isOwnStore, ownSkills, publicSkills])

  const creatorName = useMemo(() => {
    if (isOwnStore && user?.full_name) return user.full_name
    const fromSkill = displaySkills.find((s) => s.owner_name)?.owner_name
    const fromAgent = agents.find((a) => a.owner_name)?.owner_name
    return fromSkill ?? fromAgent ?? 'Creator'
  }, [isOwnStore, user?.full_name, displaySkills, agents])

  const activeCount = displaySkills.filter((s) => s.is_active).length
  const draftCount = displaySkills.length - activeCount

  const highlightedSkill = useMemo(
    () => (newSkillId ? displaySkills.find((s) => s.id === newSkillId) : undefined),
    [displaySkills, newSkillId],
  )

  const highlightReadiness = useMemo(() => {
    if (!highlightedSkill?.crew_config) return null
    return (highlightedSkill.crew_config as { publish_readiness?: PublishReadinessMeta }).publish_readiness ?? null
  }, [highlightedSkill])

  useEffect(() => {
    if (!highlightedSkill || !gardenWelcome) return
    let cancelled = false
    setInsightLoading(true)
    api
      .creatorGardenValueInsight({
        locale,
        workflow_name: highlightedSkill.name,
        description: highlightedSkill.description,
        category: highlightedSkill.category ?? 'quality',
        model_tier_id:
          typeof highlightedSkill.crew_config?.model_tier_id === 'string'
            ? highlightedSkill.crew_config.model_tier_id
            : 'standard',
      })
      .then((insight) => {
        if (!cancelled) setValueInsight(insight)
      })
      .catch(() => {
        if (!cancelled) setValueInsight(null)
      })
      .finally(() => {
        if (!cancelled) setInsightLoading(false)
      })
    return () => {
      cancelled = true
    }
  }, [highlightedSkill, gardenWelcome, locale])

  if (loading) {
    return <div className="page-shell mx-auto max-w-7xl text-[var(--color-muted)]">Loading creator…</div>
  }

  if (error) {
    return (
      <div className="page-shell mx-auto max-w-7xl py-20 text-center">
        <p className="text-red-400">{error}</p>
        <Link to="/" className="mt-4 inline-block text-sm text-[var(--color-market)] hover:underline">
          ← Back to marketplace
        </Link>
      </div>
    )
  }

  if (!displaySkills.length && !agents.length && !gardenWelcome) {
    return (
      <div className="page-shell mx-auto max-w-7xl py-20 text-center">
        <p className="text-[var(--color-muted)]">Creator storefront not found or has no public products.</p>
        {isOwnStore && (
          <Link
            to="/garden"
            className="mt-4 inline-block rounded-xl bg-[var(--color-market)] px-5 py-3 text-sm font-bold text-white"
          >
            {tr('btnGarden')}
          </Link>
        )}
        <Link to="/" className="mt-4 block text-sm text-[var(--color-market)] hover:underline">
          ← Back to marketplace
        </Link>
      </div>
    )
  }

  return (
    <div className="page-shell mx-auto max-w-7xl">
      {gardenWelcome && isOwnStore && (
        <section className="garden-card mb-6 border-2 border-[var(--color-sage)]/45 p-4 sm:p-6">
          <p className="text-xs font-bold uppercase tracking-[0.15em] text-[var(--color-sage)]">OBOLLA Garden</p>
          <h2 className="mt-2 text-xl font-bold text-[var(--color-text)] sm:text-2xl">{tr('gardenStoreWelcomeTitle')}</h2>
          <p className="mt-2 text-sm font-medium leading-relaxed text-readable-muted">
            {welcomeFlowName
              ? locale === 'th'
                ? `“${welcomeFlowName}” — ${tr('gardenStoreWelcomeBody')}`
                : `"${welcomeFlowName}" — ${tr('gardenStoreWelcomeBody')}`
              : tr('gardenStoreWelcomeBody')}
          </p>
          <div className="mt-4 flex flex-col gap-2 sm:flex-row sm:flex-wrap">
            {newSkillId && (
              <Link
                to={`/creator/products/${newSkillId}/edit`}
                className="touch-target flex items-center justify-center rounded-xl border border-[var(--color-border)] bg-white px-4 py-3 text-sm font-semibold text-[var(--color-text)] hover:bg-[var(--color-surface-overlay)] sm:rounded-lg sm:py-2.5"
              >
                {tr('gardenStoreEditBtn')}
              </Link>
            )}
            <Link
              to="/creator?tab=skills"
              className="touch-target flex items-center justify-center rounded-xl bg-[var(--color-market)] px-4 py-3 text-sm font-bold text-white hover:bg-[var(--color-market-hover)] sm:rounded-lg sm:py-2.5"
            >
              {tr('gardenStoreManageBtn')}
            </Link>
          </div>
          {newSkillId && token && (
            <div className="mt-4">
              <PublishReadinessPanel
                insight={valueInsight}
                loading={insightLoading}
                skillId={newSkillId}
                token={token}
                publishReadiness={highlightReadiness}
                currentPrice={highlightedSkill?.price_usd_per_run}
              />
            </div>
          )}
        </section>
      )}

      <div className="rounded-2xl border border-[var(--color-border)] bg-[var(--color-surface-raised)] p-4 sm:p-8">
        <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between sm:gap-6">
          <div className="flex items-center gap-4">
            <span className="flex h-14 w-14 shrink-0 items-center justify-center rounded-2xl bg-gradient-to-br from-[var(--color-market)] to-[var(--color-accent)] text-lg font-black text-black sm:h-16 sm:w-16 sm:text-xl">
              {initials(creatorName)}
            </span>
            <div>
              <p className="text-xs font-semibold uppercase tracking-widest text-[var(--color-muted)]">
                {isOwnStore ? (locale === 'th' ? 'ร้านของคุณ' : 'Your store') : 'Creator home'}
              </p>
              <h1 className="text-display text-xl font-bold text-[var(--color-text)] sm:text-3xl">{creatorName}</h1>
              <p className="mt-1 text-sm text-[var(--color-muted)]">
                {activeCount} agent flow{locale === 'en' && activeCount !== 1 ? 's' : ''}
                {isOwnStore && draftCount > 0
                  ? locale === 'th'
                    ? ` · ร่าง ${draftCount}`
                    : ` · ${draftCount} draft${draftCount !== 1 ? 's' : ''}`
                  : ''}
                {locale === 'th' ? ' · รองรับด้วยความยินยอม' : ' · Remote support with consent'}
              </p>
            </div>
          </div>
          <div className="flex flex-wrap gap-2">
            {isOwnStore && (
              <Link
                to="/creator"
                className="touch-target rounded-xl bg-[var(--color-market)] px-4 py-3 text-sm font-bold text-black hover:bg-[var(--color-market-hover)] sm:rounded-lg sm:py-2"
              >
                {tr('gardenStoreManageBtn')}
              </Link>
            )}
            {isOwnStore && (
              <Link
                to="/garden"
                className="touch-target rounded-xl border border-[var(--color-border)] px-4 py-3 text-sm text-[var(--color-text-soft)] hover:bg-[var(--color-surface-overlay)] sm:rounded-lg sm:py-2"
              >
                {tr('navGarden')}
              </Link>
            )}
          </div>
        </div>
      </div>

      {displaySkills.length > 0 && (
        <section className="mt-6 sm:mt-8">
          <h2 className="text-lg font-bold text-[var(--color-text)]">
            {locale === 'th' ? 'Agent flows' : 'Agent flows'}
          </h2>
          <p className="mt-1 text-sm text-[var(--color-muted)]">
            {isOwnStore
              ? locale === 'th'
                ? 'รายการ agent ในร้านของคุณ — ร่างจะยังไม่โชว์บน marketplace'
                : 'Agents in your store — drafts stay hidden from the public marketplace'
              : locale === 'th'
                ? 'Pipeline ที่ creator ดูแล — ราคาและ deliverables ต่อรัน'
                : 'Proven pipelines this creator maintains — pricing and deliverables per run'}
          </p>
          <div className="mt-5 grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
            {displaySkills.map((skill) => (
              <div
                key={skill.id}
                className={`relative ${newSkillId === skill.id ? 'rounded-2xl ring-2 ring-[var(--color-sage)] ring-offset-2' : ''}`}
              >
                {!skill.is_active && isOwnStore && (
                  <span className="absolute left-3 top-3 z-10 rounded-full bg-amber-100 px-2.5 py-1 text-[10px] font-bold uppercase tracking-wide text-amber-900 shadow-sm">
                    {tr('gardenStoreDraftBadge')}
                  </span>
                )}
                <ExpertSkillCard skill={skill} />
              </div>
            ))}
          </div>
        </section>
      )}

      {agents.length > 0 && (
        <section className="mt-8 sm:mt-10">
          <h2 className="text-lg font-bold text-[var(--color-text)]">Raw agents</h2>
          <div className="mt-4 grid gap-3 sm:grid-cols-2">
            {agents.map((agent) => (
              <Link
                key={agent.id}
                to={`/agents/${agent.id}`}
                className="gumroad-card flex flex-col overflow-hidden"
              >
                <AgentThumbnail
                  slug={agent.name.toLowerCase().replace(/[^a-z0-9]+/g, '-').slice(0, 48) || agent.id}
                  id={agent.id}
                  name={agent.name}
                  category={agent.category}
                  className="rounded-none"
                />
                <div className="p-4">
                  <p className="font-semibold text-[var(--color-text)]">{agent.name}</p>
                  <p className="mt-1 text-sm text-[var(--color-muted)] line-clamp-2">{agent.description}</p>
                  <span className="price-pill mt-3">${Number(agent.price_usd_per_run).toFixed(2)}</span>
                </div>
              </Link>
            ))}
          </div>
        </section>
      )}

      <div className="mt-10 sm:mt-12">
        <SecurityTrustStrip />
      </div>
    </div>
  )
}