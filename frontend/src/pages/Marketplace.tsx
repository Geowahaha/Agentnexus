import { useEffect, useMemo, useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import { api } from '../api/client'
import { ExpertSkillCard } from '../components/ExpertSkillCard'
import { CategoryNav } from '../components/marketplace/CategoryNav'
import { ShowcaseCard } from '../components/ShowcaseCard'
import { AibotauthTrustStrip } from '../components/trust/AibotauthTrustStrip'
import { SecurityTrustStrip } from '../components/trust/SecurityTrustStrip'
import { useLocale } from '../context/LocaleContext'
import { sortFeaturedSkills } from '../config/featuredSkills'
import type { ExpertSkill, SkillShowcase } from '../types'

type MarketTab = 'trending' | 'featured' | 'new'

export function Marketplace() {
  const { locale, tr } = useLocale()
  const isTh = locale === 'th'
  const [searchParams] = useSearchParams()
  const [skills, setSkills] = useState<ExpertSkill[]>([])
  const [category, setCategory] = useState('')
  const [marketTab, setMarketTab] = useState<MarketTab>('featured')
  const [showcases, setShowcases] = useState<SkillShowcase[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  const query = (searchParams.get('q') ?? '').trim().toLowerCase()

  useEffect(() => {
    setLoading(true)
    setError('')
    Promise.all([
      api.listExpertSkills(category || undefined, locale),
      api.listShowcases({ featured_only: true }).catch(() => api.listShowcases().catch(() => [])),
    ])
      .then(([skillList, showcaseList]) => {
        setSkills(skillList)
        setShowcases(showcaseList.slice(0, 6))
      })
      .catch((err) => setError(err instanceof Error ? err.message : 'Failed to load marketplace'))
      .finally(() => setLoading(false))
  }, [category, locale])

  const filtered = useMemo(() => {
    if (!query) return skills
    return skills.filter(
      (s) =>
        s.name.toLowerCase().includes(query) ||
        s.description.toLowerCase().includes(query) ||
        (s.owner_name?.toLowerCase().includes(query) ?? false) ||
        (s.category?.toLowerCase().includes(query) ?? false),
    )
  }, [skills, query])

  const sorted = useMemo(() => sortFeaturedSkills(filtered), [filtered])
  const featured = sorted.slice(0, 2)
  const rest = sorted.slice(2)

  const creators = useMemo(() => {
    const map = new Map<string, { id: string; name: string; count: number }>()
    for (const s of skills) {
      if (!s.owner_id || !s.owner_name) continue
      const cur = map.get(s.owner_id)
      if (cur) cur.count += 1
      else map.set(s.owner_id, { id: s.owner_id, name: s.owner_name, count: 1 })
    }
    return [...map.values()].sort((a, b) => b.count - a.count).slice(0, 6)
  }, [skills])

  const marketTabs: { id: MarketTab; label: string }[] = [
    { id: 'featured', label: tr('marketTabFeatured') },
    { id: 'trending', label: tr('marketTabTrending') },
    { id: 'new', label: tr('marketTabNew') },
  ]

  return (
    <div>
      <CategoryNav active={category} onChange={setCategory} />

      <div className="page-shell mx-auto max-w-7xl">
        {query && (
          <p className="mb-6 text-sm font-medium text-readable-muted">
            {tr('resultsFor')}{' '}
            <span className="text-[var(--color-text)]">&quot;{query}&quot;</span> — {filtered.length}{' '}
            {tr('flows')}
            {locale === 'en' && filtered.length !== 1 ? 's' : ''}
          </p>
        )}

        {/* Beautiful Professional Photo Hero — Real photography */}
        <section className="relative mb-10 overflow-hidden rounded-3xl border border-[var(--color-border)] shadow-xl">
          <div 
            className="absolute inset-0 bg-cover bg-center" 
            style={{ 
              backgroundImage: "url('https://images.unsplash.com/photo-1500076656116-558758c991c1?w=1600&q=80&ixlib=rb-4.0.3')",
            }}
          >
            {/* Dark overlay for readability and professional feel */}
            <div className="absolute inset-0 bg-gradient-to-b from-black/40 via-black/30 to-black/60" />
          </div>

          <div className="relative px-6 py-16 sm:px-10 sm:py-20 lg:py-24 text-white">
            <div className="max-w-4xl">
              <div className="inline-flex items-center gap-2 rounded-full bg-white/10 px-3 py-1 text-xs font-medium backdrop-blur">
                ☕ สวนชุมชนเอไอ • AI Garden Community
              </div>

              <h1 className="mt-4 text-4xl font-semibold tracking-[-1.5px] leading-none sm:text-5xl lg:text-6xl">
                {isTh ? 'สร้างสวนด้วยกัน\nAgent ช่วยทำงานหนัก' : 'Build the garden together.\nLet agents do the heavy work.'}
              </h1>

              <p className="mt-5 max-w-xl text-lg font-medium leading-relaxed text-white/90 sm:text-xl">
                {isTh 
                  ? 'ภาพจากสวนและฟาร์มจริง ทุก flow ที่รันได้ลิงก์ proof จากผู้ใช้จริง'
                  : 'Real photos from gardens and farms. Every run includes verifiable proof from real clients.'}
              </p>

              <div className="mt-7 flex flex-wrap gap-3">
                <Link
                  to="/garden"
                  className="touch-target rounded-2xl bg-white px-8 py-3 text-sm font-bold text-black hover:bg-white/90"
                >
                  {tr('btnGarden')}
                </Link>
                <Link
                  to="/agent-ready"
                  className="touch-target rounded-2xl border border-white/70 bg-white/10 px-7 py-3 text-sm font-semibold text-white backdrop-blur hover:bg-white/20"
                >
                  {isTh ? 'ลอง Strong Agent Flow' : 'Try Strong Agent Flow'}
                </Link>
              </div>

              <div className="mt-5 text-xs text-white/70">
                {tr('heroSubline')}
              </div>
            </div>
          </div>
        </section>

        {/* Trust strip with real feel */}
        <div className="mb-8">
          <AibotauthTrustStrip compact />
        </div>

        {/* Small beautiful intro with real photo vibe */}
        <section className="mb-8 rounded-2xl overflow-hidden border border-[var(--color-border)]">
          <div className="grid md:grid-cols-2 gap-0">
            <div className="p-6 sm:p-8">
              <h2 className="text-xl font-semibold tracking-tight">{isTh ? 'ภาพจริงจากสวนและฟาร์ม' : 'Real photos. Real gardens.'}</h2>
              <p className="mt-2 text-readable-muted">
                {isTh 
                  ? 'ภาพถ่ายมืออาชีพจากสวนและฟาร์มจริง เพื่อความอบอุ่นและเป็นธรรมชาติ'
                  : 'Professional photography from real gardens and farms — warm and authentic.'}
              </p>
            </div>
            <div 
              className="h-52 md:h-auto bg-cover bg-center"
              style={{ backgroundImage: "url('https://images.unsplash.com/photo-1464226184884-fa280b87c399?w=1200&q=80')" }}
            />
          </div>
        </section>

        {showcases.length > 0 && (
          <section id="case-studies" className="mb-12">
            <h2 className="text-xl font-bold text-[var(--color-text)]">{tr('caseStudiesTitle')}</h2>
            <p className="mt-1 text-sm font-medium text-readable-muted">{tr('caseStudiesDesc')}</p>
            <div className="mt-5 grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
              {showcases.map((showcase) => (
                <ShowcaseCard key={showcase.id} showcase={showcase} />
              ))}
            </div>
            <Link
              to="/community"
              className="mt-5 inline-block text-sm font-semibold text-[var(--color-market-hover)] hover:text-[var(--color-text)]"
            >
              {tr('caseStudiesLink')}
            </Link>
          </section>
        )}

        {loading && (
          <div className="grid gap-5 sm:grid-cols-2">
            {[1, 2, 3, 4].map((i) => (
              <div key={i} className="h-56 animate-pulse rounded-2xl bg-[var(--color-surface-raised)]" />
            ))}
          </div>
        )}

        {error && (
          <p className="rounded-lg border border-red-500/30 bg-red-500/10 px-4 py-3 text-sm text-red-400">{error}</p>
        )}

        {!loading && !error && filtered.length === 0 && (
          <p className="py-20 text-center font-medium text-readable-muted">{tr('noResults')}</p>
        )}

        {!loading && !error && featured.length > 0 && (
          <section id="featured" className="mb-12">
            <div className="mb-2 flex items-center justify-between">
              <div>
                <h2 className="text-xl font-semibold tracking-tight">{tr('featuredTitle')}</h2>
                <p className="text-xs text-readable-muted">Flagship flows with real proof</p>
              </div>
              <Link to="/pricing" className="text-sm font-medium text-[var(--color-market-hover)] hover:underline hidden sm:block">See full pricing →</Link>
            </div>
            <div className="mt-4 grid gap-5 lg:grid-cols-2">
              {featured.map((skill) => (
                <ExpertSkillCard key={skill.id} skill={skill} featured />
              ))}
            </div>
          </section>
        )}

        {!loading && !error && rest.length > 0 && (
          <section>
            <div className="flex flex-wrap items-center justify-between gap-4">
              <h2 className="text-xl font-bold text-[var(--color-text)]">{tr('marketTitle')}</h2>
              <div className="flex rounded-full border border-[var(--color-border)] bg-white p-1 text-sm shadow-sm">
                {marketTabs.map((tab) => (
                  <button
                    key={tab.id}
                    type="button"
                    onClick={() => setMarketTab(tab.id)}
                    className={`rounded-full px-3 py-1 font-medium transition-colors ${
                      marketTab === tab.id
                        ? 'bg-[var(--color-market)] text-white'
                        : 'text-[var(--color-text-soft)] hover:text-[var(--color-text)]'
                    }`}
                  >
                    {tab.label}
                  </button>
                ))}
              </div>
            </div>
            <div className="mt-5 grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
              {(marketTab === 'new' ? [...rest].reverse() : rest).map((skill) => (
                <ExpertSkillCard key={skill.id} skill={skill} />
              ))}
            </div>
          </section>
        )}

        {creators.length > 0 && (
          <section className="mt-14">
            <h2 className="text-xl font-bold text-[var(--color-text)]">{tr('creatorsTitle')}</h2>
            <p className="mt-1 text-sm font-medium text-readable-muted">{tr('creatorsDesc')}</p>
            <div className="mt-5 grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
              {creators.map((c) => (
                <Link
                  key={c.id}
                  to={`/creators/${c.id}`}
                  className="gumroad-card flex items-center justify-between p-4"
                >
                  <div>
                    <p className="font-semibold text-[var(--color-text)]">{c.name}</p>
                    <p className="text-xs font-medium text-readable-muted">
                      {c.count} product{locale === 'en' && c.count !== 1 ? 's' : ''}
                    </p>
                  </div>
                  <span className="text-[var(--color-market)]">→</span>
                </Link>
              ))}
            </div>
          </section>
        )}

        <div className="mt-14 space-y-8">
          <AibotauthTrustStrip />
          <SecurityTrustStrip />
        </div>
      </div>
    </div>
  )
}