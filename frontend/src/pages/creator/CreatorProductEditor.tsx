import { useCallback, useEffect, useState, type FormEvent } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { api, apiErrorMessage } from '../../api/client'
import { GardenModelTierPicker } from '../../components/garden/GardenModelTierPicker'
import { PublishReadinessPanel } from '../../components/garden/PublishReadinessPanel'
import { ExpertSkillCard } from '../../components/ExpertSkillCard'
import { SecurityTrustStrip } from '../../components/trust/SecurityTrustStrip'
import { useAuth } from '../../context/AuthContext'
import { useLocale } from '../../context/LocaleContext'
import type {
  CreatorSkillItem,
  ExpertSkill,
  GardenModelTier,
  PublishReadinessMeta,
  PublishValueInsight,
} from '../../types'

const CATEGORIES = ['research', 'content', 'quality', 'seo', 'support'] as const

type FormState = {
  name: string
  slug: string
  description: string
  category: string
  price: string
  capabilities: string
  is_active: boolean
  input_mode: 'task' | 'url'
  pipeline_label: string
  run_title: string
  skill_md: string
  model_tier_id: string
}

function slugify(name: string): string {
  return name
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-|-$/g, '')
}

function emptyForm(): FormState {
  return {
    name: '',
    slug: '',
    description: '',
    category: '',
    price: '4.99',
    capabilities: '',
    is_active: true,
    input_mode: 'task',
    pipeline_label: 'Research → Draft → Edit → Publish',
    run_title: 'Run Agent Flow',
    skill_md: '',
    model_tier_id: 'standard',
  }
}

function formFromSkill(skill: CreatorSkillItem | ExpertSkill): FormState {
  const cc = skill.crew_config ?? {}
  return {
    name: skill.name,
    slug: skill.slug,
    description: skill.description,
    category: skill.category ?? '',
    price: String(skill.price_usd_per_run),
    capabilities: skill.capabilities.join(', '),
    is_active: skill.is_active,
    input_mode: cc.input_mode === 'url' ? 'url' : 'task',
    pipeline_label: typeof cc.pipeline_label === 'string' ? cc.pipeline_label : 'Intake → Work → Review → Deliver',
    run_title: typeof cc.run_title === 'string' ? cc.run_title : 'Run Agent Flow',
    skill_md: typeof cc.skill_md === 'string' ? cc.skill_md : '',
    model_tier_id: typeof cc.model_tier_id === 'string' ? cc.model_tier_id : 'standard',
  }
}

function clampPriceToCeiling(value: string, ceiling: string | undefined): string {
  if (!ceiling) return value
  const n = Number(value)
  const max = Number(ceiling)
  if (!Number.isFinite(n) || !Number.isFinite(max)) return value
  if (n > max) return ceiling
  return value
}

function priceCeilingFromCrew(crew: Record<string, unknown>): string | undefined {
  const raw = crew.pricing_ceiling_usd
  return typeof raw === 'string' || typeof raw === 'number' ? String(raw) : undefined
}

function crewConfigFromForm(
  form: FormState,
  base: Record<string, unknown> = {},
): Record<string, unknown> {
  return {
    ...base,
    input_mode: form.input_mode,
    pipeline_label: form.pipeline_label,
    run_title: form.run_title,
    skill_md: form.skill_md,
    category: form.category || undefined,
    model_tier_id: form.model_tier_id,
  }
}

function previewSkill(
  form: FormState,
  ownerId: string,
  ownerName: string,
  crewBase: Record<string, unknown>,
): ExpertSkill {
  return {
    id: 'preview',
    slug: form.slug || 'preview-slug',
    name: form.name || 'Untitled agent flow',
    description: form.description || 'Describe what buyers get from one run.',
    category: form.category || null,
    pack_slug: 'custom',
    crew_config: crewConfigFromForm(form, crewBase),
    capabilities: form.capabilities
      .split(',')
      .map((c) => c.trim())
      .filter(Boolean),
    price_usd_per_run: form.price || '0',
    owner_id: ownerId,
    is_active: form.is_active,
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
    owner_name: ownerName,
  }
}

export function CreatorProductEditor() {
  const { id } = useParams<{ id: string }>()
  const isNew = !id || id === 'new'
  const { locale, tr } = useLocale()
  const { token, user } = useAuth()
  const navigate = useNavigate()

  const [form, setForm] = useState<FormState>(emptyForm())
  const [crewConfig, setCrewConfig] = useState<Record<string, unknown>>({})
  const [modelTiers, setModelTiers] = useState<GardenModelTier[]>([])
  const [basePriceUsd, setBasePriceUsd] = useState('0.99')
  const [tierApplying, setTierApplying] = useState(false)
  const [stats, setStats] = useState<CreatorSkillItem['stats'] | null>(null)
  const [loading, setLoading] = useState(!isNew)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')
  const [notice, setNotice] = useState('')
  const [valueInsight, setValueInsight] = useState<PublishValueInsight | null>(null)
  const [insightLoading, setInsightLoading] = useState(false)
  const [publishReadiness, setPublishReadiness] = useState<PublishReadinessMeta | null>(null)

  useEffect(() => {
    api
      .getGardenModelTiers()
      .then((res) => {
        setModelTiers(res.tiers)
        setBasePriceUsd(res.base_price_usd)
      })
      .catch(() => {
        // optional
      })
  }, [])

  const applyModelTier = useCallback(
    async (tierId: string) => {
      setTierApplying(true)
      setError('')
      try {
        const applied = await api.creatorGardenApplyTier({
          model_tier_id: tierId,
          crew_config: crewConfig,
        })
        setCrewConfig(applied.crew_config)
        setForm((f) => {
          const ceiling = priceCeilingFromCrew(crewConfig) ?? valueInsight?.max_price_usd
          return {
            ...f,
            model_tier_id: applied.model_tier_id,
            price: clampPriceToCeiling(applied.suggested_price_usd, ceiling),
            pipeline_label:
              typeof applied.pipeline_label === 'string' ? applied.pipeline_label : f.pipeline_label,
          }
        })
      } catch (err) {
        setError(apiErrorMessage(err, locale))
      } finally {
        setTierApplying(false)
      }
    },
    [crewConfig, valueInsight?.max_price_usd],
  )

  useEffect(() => {
    if (!isNew) return
    try {
      const raw = localStorage.getItem('obolla-garden-product-draft')
      if (!raw) return
      const garden = JSON.parse(raw) as {
        name?: string
        description?: string
        category?: string
        capabilities?: string
        price?: string
        input_mode?: 'task' | 'url'
        pipeline_label?: string
        run_title?: string
        skill_md?: string
        model_tier_id?: string
        crew_config?: Record<string, unknown>
      }
      const gardenCrew = garden.crew_config ?? {}
      setCrewConfig(gardenCrew)
      setForm((prev) => ({
        ...prev,
        name: garden.name || prev.name,
        slug: garden.name ? slugify(garden.name) : prev.slug,
        description: garden.description || prev.description,
        category: garden.category || prev.category,
        capabilities: garden.capabilities || prev.capabilities,
        price: garden.price || prev.price,
        input_mode: garden.input_mode || (garden.category === 'seo' ? 'url' : 'task'),
        pipeline_label: garden.pipeline_label || prev.pipeline_label,
        run_title: garden.run_title || prev.run_title,
        skill_md: garden.skill_md || prev.skill_md,
        model_tier_id:
          garden.model_tier_id ||
          (typeof gardenCrew.model_tier_id === 'string' ? gardenCrew.model_tier_id : prev.model_tier_id),
      }))
      localStorage.removeItem('obolla-garden-product-draft')
      setNotice('Loaded from Free Creator Garden — edit and publish when ready.')
    } catch {
      // ignore invalid garden draft
    }
  }, [isNew])

  useEffect(() => {
    if (!token || isNew) return
    setLoading(true)
    api
      .getCreatorSkills(token)
      .then((skills) => {
        const skill = skills.find((s) => s.id === id)
        if (!skill) throw new Error('Product not found')
        setForm(formFromSkill(skill))
        setCrewConfig(skill.crew_config ?? {})
        setStats(skill.stats)
        const readiness = (skill.crew_config as { publish_readiness?: PublishReadinessMeta } | undefined)
          ?.publish_readiness
        setPublishReadiness(readiness ?? null)
      })
      .catch((err) => setError(apiErrorMessage(err, locale)))
      .finally(() => setLoading(false))
  }, [token, id, isNew])

  useEffect(() => {
    if (!form.name.trim()) return
    let cancelled = false
    setInsightLoading(true)
    api
      .creatorGardenValueInsight({
        locale,
        workflow_name: form.name,
        description: form.description,
        category: form.category || 'quality',
        model_tier_id: form.model_tier_id,
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
  }, [form.name, form.description, form.category, form.model_tier_id, locale])

  async function handleSubmit(e: FormEvent) {
    e.preventDefault()
    if (!token) return
    const ceiling = priceCeiling ?? valueInsight?.max_price_usd
    const priceToSave = clampPriceToCeiling(form.price, ceiling)
    if (ceiling && Number(priceToSave) > Number(ceiling)) {
      setError(
        locale === 'th'
          ? `ราคาสูงสุด $${ceiling} — ลดได้ แต่เพิ่มเกินราคาแรกไม่ได้`
          : `Price ceiling is $${ceiling} — lower OK, raise not allowed`,
      )
      return
    }
    setSaving(true)
    setError('')
    setNotice('')
    const capabilities = form.capabilities
      .split(',')
      .map((c) => c.trim())
      .filter(Boolean)

    try {
      if (isNew) {
        const created = await api.createCreatorSkill(token, {
          name: form.name,
          slug: form.slug || slugify(form.name),
          description: form.description,
          category: form.category || undefined,
          price_usd_per_run: priceToSave,
        })
        const initialCrew = crewConfigFromForm(form, crewConfig)
        const ceilingToStore = ceiling ?? priceToSave
        await api.updateCreatorSkill(token, created.id, {
          capabilities,
          crew_config: {
            ...initialCrew,
            pricing_ceiling_usd: ceilingToStore,
            value_score: valueInsight?.value_score ?? crewConfig.value_score,
            value_tier: valueInsight?.value_tier ?? crewConfig.value_tier,
          },
          is_active: form.is_active,
        })
        navigate(`/creator/products/${created.id}/edit`, { replace: true })
        return
      }

      const mergedCrew = {
        ...crewConfigFromForm(form, crewConfig),
        ...(priceCeiling ? { pricing_ceiling_usd: priceCeiling } : {}),
        ...(valueInsight?.value_score != null && !crewConfig.value_score
          ? { value_score: valueInsight.value_score, value_tier: valueInsight.value_tier }
          : {}),
      }
      if (!priceCeiling && valueInsight?.max_price_usd) {
        mergedCrew.pricing_ceiling_usd = valueInsight.max_price_usd
      }
      await api.updateCreatorSkill(token, id!, {
        name: form.name,
        description: form.description,
        category: form.category || undefined,
        price_usd_per_run: priceToSave,
        is_active: form.is_active,
        capabilities,
        crew_config: mergedCrew,
      })
      setNotice('Product saved.')
    } catch (err) {
      setError(apiErrorMessage(err, locale))
    } finally {
      setSaving(false)
    }
  }

  async function handleDelete() {
    if (!token || isNew || !id) return
    if (!window.confirm(`Delete "${form.name}"? This cannot be undone.`)) return
    try {
      await api.deleteCreatorSkill(token, id)
      navigate('/creator?tab=skills')
    } catch (err) {
      setError(apiErrorMessage(err, locale))
    }
  }

  if (loading) {
    return <div className="mx-auto max-w-6xl px-4 py-16 text-[var(--color-muted)]">Loading product…</div>
  }

  const ownerId = user?.id ?? ''
  const ownerName = user?.full_name ?? 'Creator'
  const priceCeiling =
    priceCeilingFromCrew(crewConfig) ?? valueInsight?.max_price_usd ?? valueInsight?.pricing_ceiling_usd

  return (
    <div className="mx-auto max-w-6xl px-4 py-8 sm:px-6">
      <div className="mb-6 flex flex-wrap items-center justify-between gap-4">
        <div>
          <Link to="/creator?tab=skills" className="text-sm text-[var(--color-muted)] hover:text-[var(--color-market)]">
            ← My products
          </Link>
          <h1 className="text-display mt-2 text-2xl font-bold text-[var(--color-text)] sm:text-3xl">
            {isNew ? 'New agent flow' : 'Edit product'}
          </h1>
          <p className="mt-1 text-sm text-[var(--color-muted)]">
            Gumroad-style listing — you are responsible for deliverables, support, and buyer safety terms.
          </p>
        </div>
        {!isNew && (
          <div className="flex gap-2">
            <Link
              to={`/expert-skills/${id}`}
              className="rounded-lg border border-[var(--color-border)] px-4 py-2 text-sm text-[var(--color-text-soft)] hover:bg-[var(--color-surface-overlay)]"
            >
              View live
            </Link>
            {user && (
              <Link
                to={`/creators/${user.id}`}
                className="rounded-lg border border-[var(--color-border)] px-4 py-2 text-sm text-[var(--color-text-soft)] hover:bg-[var(--color-surface-overlay)]"
              >
                My storefront
              </Link>
            )}
          </div>
        )}
      </div>

      {error && (
        <div className="mb-4 rounded-lg border border-red-500/40 bg-red-500/10 px-4 py-3 text-sm text-red-300">{error}</div>
      )}
      {notice && (
        <div className="mb-4 rounded-lg border border-emerald-500/40 bg-emerald-500/10 px-4 py-3 text-sm text-emerald-700">{notice}</div>
      )}

      <div className="grid gap-8 lg:grid-cols-5">
        <form onSubmit={handleSubmit} className="lg:col-span-3 space-y-6">
          <section className="surface-panel p-6">
            <h2 className="form-section-title">Product details</h2>
            <div className="mt-4 grid gap-4 sm:grid-cols-2">
              <label className="block sm:col-span-2">
                <span className="form-label">Name</span>
                <input
                  required
                  value={form.name}
                  onChange={(e) =>
                    setForm((f) => ({
                      ...f,
                      name: e.target.value,
                      slug: isNew && !f.slug ? slugify(e.target.value) : f.slug,
                    }))
                  }
                  className="form-input mt-1"
                />
              </label>
              <label className="block">
                <span className="form-label">URL slug</span>
                <input
                  required
                  disabled={!isNew}
                  pattern="^[a-z][a-z0-9-]*$"
                  value={form.slug}
                  onChange={(e) => setForm((f) => ({ ...f, slug: e.target.value }))}
                  className="form-input mt-1 font-mono disabled:opacity-60"
                />
              </label>
              <label className="block">
                <span className="form-label">Category</span>
                <select
                  value={form.category}
                  onChange={(e) => {
                    const category = e.target.value
                    setForm((f) => ({
                      ...f,
                      category,
                      input_mode: category === 'seo' ? 'url' : 'task',
                      pipeline_label:
                        category === 'content'
                          ? 'Research → Draft → Edit → Publish'
                          : category === 'coding'
                            ? 'Plan → Implement → Review → QA'
                            : f.pipeline_label,
                      run_title:
                        category === 'content' ? 'Run Content Pipeline' : f.run_title,
                    }))
                  }}
                  className="form-input mt-1"
                >
                  <option value="">Select category</option>
                  {CATEGORIES.map((cat) => (
                    <option key={cat} value={cat}>
                      {cat}
                    </option>
                  ))}
                </select>
              </label>
              <label className="block sm:col-span-2">
                <span className="form-label">Description</span>
                <textarea
                  required
                  rows={5}
                  value={form.description}
                  onChange={(e) => setForm((f) => ({ ...f, description: e.target.value }))}
                  placeholder="What does one run deliver? Who is it for?"
                  className="form-input mt-1"
                />
              </label>
              <p className="sm:col-span-2 rounded-xl border border-emerald-200/80 bg-emerald-50/60 px-4 py-3 text-sm leading-relaxed text-emerald-950">
                {locale === 'th'
                  ? '☕ OBOLLA จัดการ copy ภาษาไทยให้อัตโนมัติ (โทนมุมกาแฟ ตรงความสามารถจริง) — คุณโฟกัสภาษาอังกฤษหรือภาษาใดก็ได้ที่สะดวก ไม่ต้องแปลเอง'
                  : '☕ OBOLLA writes Thai marketplace copy for you (coffee-corner tone, capability-honest) — focus on your flow; no manual Thai needed.'}
              </p>
              <label className="block">
                <span className="form-label">Price per run (USD)</span>
                <input
                  required
                  type="number"
                  min="0"
                  max={priceCeiling ?? undefined}
                  step="0.01"
                  value={form.price}
                  onChange={(e) =>
                    setForm((f) => ({
                      ...f,
                      price: clampPriceToCeiling(e.target.value, priceCeiling),
                    }))
                  }
                  className="form-input mt-1 font-mono"
                />
                {priceCeiling && (
                  <p className="mt-1.5 text-xs font-medium text-readable-muted">
                    {tr('publishPriceCeiling')}: ${priceCeiling} — {tr('publishPriceCeilingHint')}
                  </p>
                )}
              </label>
              {modelTiers.length > 0 && (
                <div className="sm:col-span-2">
                  <GardenModelTierPicker
                    tiers={modelTiers}
                    selectedId={form.model_tier_id}
                    locale={locale}
                    basePriceUsd={basePriceUsd}
                    disabled={tierApplying || saving}
                    onSelect={(tierId) => void applyModelTier(tierId)}
                    labels={{
                      title: tr('gardenTierTitle'),
                      hint: tr('gardenTierHint'),
                      perRun: tr('gardenTierPerRun'),
                      base: tr('gardenTierBase'),
                      addon: tr('gardenTierAddon'),
                      unavailable: tr('gardenTierUnavailable'),
                    }}
                  />
                  <p className="mt-2 text-xs font-medium text-readable-muted">
                    If a premium API is not ready on the server, buyers run on Standard models at base
                    price — no extra charge.
                  </p>
                </div>
              )}
              <label className="block">
                <span className="form-label">Buyer input</span>
                <select
                  value={form.input_mode}
                  onChange={(e) =>
                    setForm((f) => ({ ...f, input_mode: e.target.value as 'task' | 'url' }))
                  }
                  className="form-input mt-1"
                >
                  <option value="task">Task description (garden default)</option>
                  <option value="url">Website URL (SEO / visibility)</option>
                </select>
              </label>
              <label className="block sm:col-span-2">
                <span className="form-label">Pipeline label</span>
                <input
                  value={form.pipeline_label}
                  onChange={(e) => setForm((f) => ({ ...f, pipeline_label: e.target.value }))}
                  placeholder="Research → Draft → Edit → Publish"
                  className="form-input mt-1"
                />
              </label>
              <label className="block sm:col-span-2">
                <span className="form-label">Run button title</span>
                <input
                  value={form.run_title}
                  onChange={(e) => setForm((f) => ({ ...f, run_title: e.target.value }))}
                  placeholder="Run Content Pipeline"
                  className="form-input mt-1"
                />
              </label>
              <label className="block sm:col-span-2">
                <span className="form-label">Capabilities (comma-separated)</span>
                <input
                  value={form.capabilities}
                  onChange={(e) => setForm((f) => ({ ...f, capabilities: e.target.value }))}
                  placeholder="content, research, editing"
                  className="form-input mt-1"
                />
              </label>
              <label className="block sm:col-span-2">
                <span className="form-label">SKILL.md playbook</span>
                <textarea
                  rows={10}
                  value={form.skill_md}
                  onChange={(e) => setForm((f) => ({ ...f, skill_md: e.target.value }))}
                  placeholder="# Your flow name&#10;&#10;## Purpose&#10;What the agent does per run..."
                  className="form-input mt-1 font-mono text-xs"
                />
                <p className="mt-1.5 text-xs font-medium text-readable-muted">
                  Optional but recommended — guides the AI pipeline like a creator garden playbook.
                </p>
              </label>
            </div>
          </section>

          <section className="surface-panel p-4 sm:p-6 space-y-4">
            <h2 className="form-section-title">Publish</h2>
            {!isNew && (
              <PublishReadinessPanel
                insight={valueInsight}
                loading={insightLoading}
                skillId={id}
                token={token}
                publishReadiness={publishReadiness}
                currentPrice={form.price}
                onApplyPrice={(price) =>
                  setForm((f) => ({ ...f, price: clampPriceToCeiling(price, priceCeiling) }))
                }
                onReadinessChange={setPublishReadiness}
              />
            )}
            <label className="mt-2 flex items-start gap-3">
              <input
                type="checkbox"
                checked={form.is_active}
                disabled={!isNew && publishReadiness?.passed !== true}
                onChange={(e) => setForm((f) => ({ ...f, is_active: e.target.checked }))}
                className="mt-1 h-4 w-4 rounded accent-[var(--color-market)] disabled:opacity-40"
              />
              <span className="text-sm text-[var(--color-text-soft)]">
                Listed on marketplace {form.is_active ? '(live)' : '(paused — hidden from buyers)'}
                {!isNew && publishReadiness?.passed !== true && (
                  <span className="mt-1 block text-xs font-medium text-amber-800">
                    {tr('publishTestBtn')} — {locale === 'th' ? 'ต้องทดสอบผ่านก่อนเปิดขาย' : 'pass test run before going live'}
                  </span>
                )}
              </span>
            </label>
            <p className="mt-3 text-xs leading-relaxed text-[var(--color-muted)]">
              By publishing you agree to maintain this flow, honor buyer support threads, and follow our{' '}
              <Link to="/terms" className="text-[var(--color-market)] hover:underline">creator terms</Link>.
              Remote bridge tools require buyer consent for every action.
            </p>
          </section>

          <div className="flex flex-wrap gap-3">
            <button
              type="submit"
              disabled={saving}
              className="rounded-lg bg-[var(--color-market)] px-6 py-2.5 text-sm font-bold text-black hover:bg-[var(--color-market-hover)] disabled:opacity-50"
            >
              {saving ? 'Saving…' : isNew ? 'Create product' : 'Save changes'}
            </button>
            <Link
              to="/creator?tab=skills"
              className="rounded-lg border border-[var(--color-border)] px-6 py-2.5 text-sm text-[var(--color-text-soft)] hover:bg-[var(--color-surface-overlay)]"
            >
              Cancel
            </Link>
            {!isNew && (
              <button
                type="button"
                onClick={handleDelete}
                className="ml-auto rounded-lg border border-red-500/40 px-4 py-2.5 text-sm text-red-400 hover:bg-red-500/10"
              >
                Delete product
              </button>
            )}
          </div>
        </form>

        <aside className="lg:col-span-2 space-y-6">
          <div>
            <p className="mb-3 form-section-title">Preview</p>
            <ExpertSkillCard skill={previewSkill(form, ownerId, ownerName, crewConfig)} />
          </div>

          {!isNew && stats && (
            <div className="rounded-2xl border border-[var(--color-border)] bg-[var(--color-surface-raised)] p-5">
              <p className="text-xs font-semibold uppercase tracking-wider text-[var(--color-muted)]">Performance</p>
              <dl className="mt-4 grid grid-cols-2 gap-4 text-sm">
                <div>
                  <dt className="text-[var(--color-muted)]">Runs</dt>
                  <dd className="font-mono text-xl text-white">{stats.total_runs}</dd>
                </div>
                <div>
                  <dt className="text-[var(--color-muted)]">Earnings</dt>
                  <dd className="font-mono text-xl text-emerald-400">${Number(stats.total_earnings_usd).toFixed(2)}</dd>
                </div>
                <div>
                  <dt className="text-[var(--color-muted)]">Rating</dt>
                  <dd className="text-white">
                    {stats.average_rating != null ? `${stats.average_rating.toFixed(1)} ★` : '—'}
                  </dd>
                </div>
                <div>
                  <dt className="text-[var(--color-muted)]">Reviews</dt>
                  <dd className="text-white">{stats.review_count}</dd>
                </div>
              </dl>
            </div>
          )}

          <SecurityTrustStrip compact />
        </aside>
      </div>
    </div>
  )
}