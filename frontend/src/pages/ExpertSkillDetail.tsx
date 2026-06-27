import { useEffect, useRef, useState, type FormEvent } from 'react'
import { Link, useLocation, useNavigate, useParams, useSearchParams } from 'react-router-dom'
import { api } from '../api/client'
import { AgentThumbnail } from '../components/AgentThumbnail'
import { BeforeAfterSection } from '../components/BeforeAfterSection'
import { SpeechToTextControl } from '../components/SpeechToTextControl'
import { CreatorAttribution } from '../components/product/CreatorAttribution'
import { LocalBridgeSelector } from '../components/LocalBridgeSelector'
import { RemoteSupportConsent } from '../components/trust/RemoteSupportConsent'
import { useLocalBridge } from '../hooks/useLocalBridge'
import { SecurityTrustStrip } from '../components/trust/SecurityTrustStrip'
import { AttributionCredits } from '../components/AttributionCredits'
import { LineartPresetPicker, defaultLineartSelection } from '../components/lineart/LineartPresetPicker'
import { resolveSkillMeta, type SkillInputMode } from '../config/expertSkillMeta'
import {
  buildLineartPresetBlock,
  isLineartKemlifeSlug,
  lineartFormatFromSlug,
  mergeLineartPresetsIntoText,
  stripLineartPresetBlock,
  validateLineartPresets,
  type LineartPresetSelection,
} from '../config/lineartKemlifePresets'
import { FABLE5_LORA_HF_URL } from '../config/fable5Credits'
import { normalizeSiteUrl } from '../utils/normalizeSiteUrl'
import { useAuth } from '../context/AuthContext'
import { useLocale } from '../context/LocaleContext'
import {
  formatRunCta,
  localizeAttribution,
  localizeCapability,
  localizeCategory,
  localizeDeliverable,
  localizePipelineLabel,
  localizeRunTitle,
  localizeStepTitle,
} from '../i18n/skillDetail'
import type { CostEstimate, ExpertSkill, SkillShowcase } from '../types'

function formatToolLabel(tool: string): string {
  if (tool.includes('aibotauth')) return 'AIBotAuth Scanner'
  if (tool.startsWith('mcp.')) return tool.replace('mcp.', '').replace('.', ' · ')
  return tool
}

export function ExpertSkillDetail() {
  const { id } = useParams<{ id: string }>()
  const { locale, tr, trf } = useLocale()
  const { token, user } = useAuth()
  const location = useLocation()
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const linkedFarmId = searchParams.get('farm_id') ?? ''
  const runSectionRef = useRef<HTMLDivElement>(null)
  const [skill, setSkill] = useState<ExpertSkill | null>(null)
  const [task, setTask] = useState('')
  const [loading, setLoading] = useState(true)
  const [running, setRunning] = useState(false)
  const [runSeconds, setRunSeconds] = useState(0)
  const [error, setError] = useState('')
  const [estimate, setEstimate] = useState<CostEstimate | null>(null)
  const [showcases, setShowcases] = useState<SkillShowcase[]>([])
  const [consentAccepted, setConsentAccepted] = useState(false)
  const [lineartPresets, setLineartPresets] = useState<LineartPresetSelection | null>(null)
  const {
    devices: bridgeDevices,
    enabled: bridgeEnabled,
    setEnabled: setBridgeEnabled,
    deviceId: bridgeDeviceId,
    setDeviceId: setBridgeDeviceId,
    bridgeDeviceId: selectedBridgeDeviceId,
  } = useLocalBridge(token)

  useEffect(() => {
    if (!running) {
      setRunSeconds(0)
      return
    }
    const start = Date.now()
    const timer = setInterval(() => setRunSeconds(Math.floor((Date.now() - start) / 1000)), 1000)
    return () => clearInterval(timer)
  }, [running])

  useEffect(() => {
    if (!skill?.slug || !isLineartKemlifeSlug(skill.slug)) return
    const format = lineartFormatFromSlug(skill.slug)
    setLineartPresets((prev) => {
      if (prev && prev.format === format) return prev
      return defaultLineartSelection(format, locale)
    })
  }, [skill?.slug, locale])

  useEffect(() => {
    if (!id) return

    // Force redirect for the flagship to the clean preferred URL
    if (id === '33333333-3333-4333-8333-333333333310' || id === 'agent-ready-auto-fix') {
      navigate('/agent-ready', { replace: true })
      return
    }

    let cancelled = false
    setLoading(true)
    api
      .getExpertSkill(id, locale)
      .then((data) => {
        if (!cancelled) setSkill(data)
      })
      .catch((err) => {
        if (!cancelled) setError(err instanceof Error ? err.message : 'Skill not found')
      })
      .finally(() => {
        if (!cancelled) setLoading(false)
      })
    return () => {
      cancelled = true
    }
  }, [id, locale])

  useEffect(() => {
    if (!token || !id) return
    api
      .estimateCost(token, { workflow_type: 'expert_skill', expert_skill_id: id })
      .then(setEstimate)
      .catch(() => setEstimate(null))
  }, [token, id])

  useEffect(() => {
    if (!id) return
    api
      .listShowcases({ expert_skill_id: id })
      .then(setShowcases)
      .catch(() => setShowcases([]))
  }, [id])

  function scrollToRun() {
    runSectionRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' })
  }

  async function handleRun(e: FormEvent) {
    e.preventDefault()
    if (!token || !skill) return
    if (!consentAccepted) {
      setError(tr('skillConsentRequired'))
      return
    }

    const inputMode = resolveSkillMeta(skill).inputMode ?? 'task'
    let taskDescription = task.trim()
    if (inputMode === 'url') {
      const { normalized, error: urlError } = normalizeSiteUrl(task)
      if (urlError) {
        setError(urlError)
        return
      }
      taskDescription = normalized
    } else if (skill && isLineartKemlifeSlug(skill.slug) && lineartPresets) {
      const presetError = validateLineartPresets(lineartPresets, stripLineartPresetBlock(taskDescription))
      if (presetError) {
        setError(presetError)
        return
      }
      taskDescription = mergeLineartPresetsIntoText(taskDescription, lineartPresets).trim()
      if (!taskDescription) {
        setError(tr('skillPickLineart'))
        return
      }
    } else if (!taskDescription) {
      setError(tr('skillTaskRequired'))
      return
    }

    setRunning(true)
    setError('')
    if (taskDescription !== task.trim()) {
      setTask(taskDescription)
    }
    const skillInputMode = resolveSkillMeta(skill).inputMode ?? 'task'
    try {
      const result = await api.runWorkflow(token, {
        task_description: taskDescription,
        workflow_type: 'expert_skill',
        expert_skill_id: skill.id,
        bridge_device_id: skillInputMode === 'task' ? selectedBridgeDeviceId : undefined,
        task_context: {
          expert_skill_id: skill.id,
          expert_skill_slug: skill.slug,
          ...(linkedFarmId ? { smart_farm_id: linkedFarmId } : {}),
        },
      })
      navigate(`/workflows/${result.workflow_id}`, { replace: true })
      return
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to run skill')
      setRunning(false)
    }
  }

  if (loading) {
    return <div className="mx-auto max-w-4xl px-4 py-16 text-[var(--color-muted)]">{tr('skillLoading')}</div>
  }

  if (!skill) {
    return (
      <div className="mx-auto max-w-4xl px-4 py-16">
        <p className="font-medium text-red-800">{error || tr('skillNotFound')}</p>
      </div>
    )
  }

  const price = Number(skill.price_usd_per_run)
  const estLlm = estimate ? Number(estimate.estimated_llm_cost_usd) : 0.12
  const estTotal = price + estLlm
  const balance = estimate ? Number(estimate.current_balance_usd) : null
  const canAfford = estimate?.sufficient_balance ?? true
  const steps = skill.pipeline_steps ?? []
  const isFreeRun = price <= 0
  const skillMeta = resolveSkillMeta(skill)
  const inputMode: SkillInputMode = skillMeta.inputMode ?? 'task'
  const isTaskMode = inputMode === 'task'
  const runTitle = localizeRunTitle(
    locale,
    skillMeta.runTitle ?? (inputMode === 'task' ? 'Run Agent Flow' : 'Run Visibility Audit'),
  )
  const runCta = formatRunCta(locale, isFreeRun, estTotal, estLlm, isTaskMode, skillMeta.runCta)
  const pipelineLabel = localizePipelineLabel(locale, skillMeta.pipelineLabel)
  const deliverables = skillMeta.deliverables.map((d) => localizeDeliverable(locale, d))
  const localizedAttribution = skill.attribution
    ? localizeAttribution(locale, skill.attribution, price)
    : null
  const isLineartKemlife = isLineartKemlifeSlug(skill.slug)
  const lineartFormat = lineartFormatFromSlug(skill.slug)
  const requiresOllama = skillMeta.requiresLocalOllama === true
  const upgradeSkillId = skillMeta.upgradeSkillId
  const featuredShowcase =
    showcases.find((s) => s.before_after?.bots?.length) ??
    showcases.find((s) => s.before_after?.score_before) ??
    showcases[0]

  // Special sub-page flags — beautiful dedicated experiences for strong flagship flows
  const isAgentReadyPro = skill.slug === 'agent-ready-auto-fix' || id === '33333333-3333-4333-8333-333333333310'
  const isMelonDatasetPack = skill.slug === 'japanese-melon-dataset-pack' || skill.pack_slug === 'japanese-melon-dataset'

  // Links to beautiful dedicated child pages
  const dedicatedLink = isAgentReadyPro
    ? '/agent-ready'
    : isMelonDatasetPack
      ? (linkedFarmId ? `/japanese-melon-pack?farm_id=${linkedFarmId}` : '/japanese-melon-pack')
      : null

  const containerClass = isAgentReadyPro || isMelonDatasetPack ? 'mx-auto max-w-5xl' : 'mx-auto max-w-4xl'

  return (
    <div className={`page-shell ${containerClass}`}>
      <Link to="/" className="text-sm font-medium text-readable-muted hover:text-[var(--color-text)] inline-flex items-center gap-1">
        ← {tr('skillBackMarketplace')}
      </Link>

      {/* Beautiful enhanced hero */}
      <div className="mt-4 rich-hero overflow-hidden sm:mt-6">
        <div className="flex flex-col lg:flex-row lg:items-stretch">
          <AgentThumbnail
            packSlug={skill.pack_slug}
            slug={skill.slug}
            id={skill.id}
            name={skill.name}
            category={skill.category}
            featured
            className="lg:min-h-[240px] lg:w-80"
          />
          <div className="flex flex-1 flex-col gap-4 p-5 sm:gap-5 sm:p-8">
            <div>
              <div className="flex flex-wrap items-center gap-2">
                <span className="price-pill">{isAgentReadyPro ? 'Pro Agent Flow' : tr('skillBadgeFlow')}</span>
                {isAgentReadyPro && <span className="pro-badge">Level 5 • Reference 100%</span>}
                {isMelonDatasetPack && <span className="pro-badge">Smart Farm Data</span>}
              </div>

              <h1 className="mt-2 text-2xl font-bold tracking-[-0.015em] text-[var(--color-text)] sm:mt-2.5 sm:text-[32px] leading-tight">{skill.name}</h1>

              {locale === 'th' && skill.display_locale === 'en' && (
                <p className="mt-1.5 text-xs font-medium text-amber-800/90">{tr('skillEnglishFallback')}</p>
              )}

              <p className="mt-2.5 max-w-3xl text-[15px] leading-relaxed text-readable-muted sm:text-base">
                {skill.description}
              </p>

              <div className="mt-4 flex flex-wrap items-center gap-x-3 gap-y-1.5 text-sm">
                {skill.category && (
                  <span className="rounded-full border border-[var(--color-border)] bg-[var(--color-surface-overlay)] px-3 py-0.5 text-xs font-medium capitalize text-[var(--color-text-soft)]">
                    {localizeCategory(locale, skill.category)}
                  </span>
                )}
                {skill.owner_id && skill.owner_name && (
                  <CreatorAttribution ownerId={skill.owner_id} ownerName={skill.owner_name} />
                )}
              </div>
            </div>

            {/* Premium pricing card — mobile friendly */}
            <div className="mt-auto w-full rounded-2xl border border-[var(--color-border)] bg-white/95 p-4 sm:p-5 lg:w-auto lg:min-w-[238px]">
              <div className="flex items-baseline justify-between">
                <div>
                  <div className="text-xs font-semibold uppercase tracking-widest text-[var(--color-text-soft)]">{tr('skillPricePerRun')}</div>
                  <div className="mt-0.5 text-3xl font-semibold tabular-nums text-[var(--color-text)]">
                    {isFreeRun ? tr('skillFree') : `$${price.toFixed(2)}`}
                  </div>
                </div>
                {isAgentReadyPro && <div className="text-right text-[10px] font-mono text-emerald-800/80 leading-none">Pro<br/>Agent</div>}
              </div>

              <div className="mt-1 text-xs font-medium text-readable-muted">
                {isFreeRun
                  ? requiresOllama ? tr('skillPriceHotdogsGpu') : isTaskMode ? tr('skillPriceLlmCredits') : tr('skillPriceLocalOllama')
                  : trf('skillPricePlusLlm', { amount: estLlm.toFixed(2) })}
              </div>

              <div className="mt-2 font-mono text-sm font-semibold text-[var(--color-market-hover)]">
                {isFreeRun
                  ? requiresOllama ? tr('skillPriceRunFeeLlm') : isTaskMode ? trf('skillPriceLlmZeroRun', { amount: estLlm.toFixed(2) }) : trf('skillPriceCloudLlm', { amount: estLlm.toFixed(2) })
                  : trf('skillPriceTotal', { amount: estTotal.toFixed(2) })}
              </div>

              <p className="mt-2 text-xs text-[var(--color-text-soft)]">{tr('skillResultsTiming')}</p>

              {user ? (
                <button onClick={scrollToRun} className="touch-target mt-4 w-full rounded-2xl bg-[var(--color-market)] py-3 text-sm font-bold text-white hover:bg-[var(--color-market-hover)] active:scale-[0.985]">
                  {runTitle}
                </button>
              ) : (
                <Link to="/register" state={{ from: location }} className="touch-target mt-4 block w-full rounded-2xl bg-violet-600 py-3 text-center text-sm font-bold text-white hover:bg-violet-500">
                  {runTitle}
                </Link>
              )}
            </div>
          </div>
        </div>

        {dedicatedLink && (
          <div className="mt-3 text-center">
            <Link to={dedicatedLink} className="inline-flex items-center text-sm font-semibold text-[var(--color-market-hover)] hover:underline">
              ✨ Open the beautiful dedicated experience page →
            </Link>
          </div>
        )}
      </div>

      {localizedAttribution && (
        <div className="mt-6">
          <AttributionCredits attribution={localizedAttribution} />
        </div>
      )}

      {/* =========================================
          SPECIAL BEAUTIFUL SUB-PAGES / CHILD PAGES
          Strong professional experience for flagship flows
          ========================================= */}
      {isAgentReadyPro && (
        <div className="mt-8 pro-section">
          <div className="flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
            <div>
              <span className="pro-badge mb-2">Flagship • Strong Agent Flow</span>
              <h2 className="text-2xl font-semibold tracking-tight">Agent-Ready Auto Fix Pro</h2>
              <p className="mt-1 max-w-prose text-[15px] text-readable-muted">
                URL → Complete Level 5 deployable fix pack. Reference: successcasting.com (25% → 100%).
              </p>
            </div>
            <a href="https://isitagentready.com" target="_blank" rel="noreferrer" className="text-sm font-semibold text-[var(--color-market-hover)] hover:underline">See isitagentready.com taxonomy →</a>
          </div>

          <div className="mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {[
              ['Discoverability', 'robots.txt, Link headers, sitemap, DNS-AID playbook'],
              ['Content', 'Markdown negotiation + Content-Signal'],
              ['Bot Access', 'llms.txt + ai.txt + agents.txt aligned'],
              ['API + MCP', 'api-catalog, OAuth, WebMCP, agent-skills stubs'],
              ['Commerce Layer', 'UCP / ACP / x402 templates (if product detected)'],
              ['Deploy + Verify', 'Stack-specific steps + re-verify checklist'],
            ].map(([title, desc], i) => (
              <div key={i} className="rounded-2xl border border-[var(--color-border)] bg-[var(--color-surface-overlay)]/60 p-4">
                <div className="font-semibold text-[var(--color-text)]">{title}</div>
                <div className="mt-1 text-sm text-readable-muted leading-snug">{desc}</div>
              </div>
            ))}
          </div>

          <div className="mt-6 rounded-2xl border-l-4 border-[var(--color-market)] bg-emerald-50/70 p-4 text-sm font-medium text-[var(--color-text)]">
            <strong>Honest limits:</strong> We generate paste-ready files and exact commands. DNS changes, wallets, and final deploy steps are yours (or grant us access for full auto).
          </div>
        </div>
      )}

      {isMelonDatasetPack && (
        <div className="mt-8 pro-section">
          <div className="mb-3">
            <span className="pro-badge">Smart Farm Exclusive</span>
            <h2 className="mt-1 text-2xl font-semibold tracking-tight">Japanese Melon Greenhouse Dataset Pack</h2>
            <p className="mt-1 text-readable-muted">Production telemetry exports aligned to greenhouse research schema. Fresh from your farm sensors.</p>
          </div>

          <div className="grid gap-3 sm:grid-cols-2">
            <div className="rounded-2xl border bg-white p-5 text-sm">
              <div className="font-semibold mb-2">What you receive per export</div>
              <ul className="list-disc pl-5 space-y-1 text-readable-muted">
                <li>Schema-aligned JSON + CSV</li>
                <li>Coverage report vs Japanese melon greenhouse schema</li>
                <li>Latest telemetry pack download link</li>
                <li>Import notes for IoT / automation systems</li>
              </ul>
            </div>
            <div className="rounded-2xl border bg-white p-5 text-sm">
              <div className="font-semibold mb-2">Data sources</div>
              <div className="font-mono text-xs text-readable-muted space-y-1">
                <div>POST /api/v1/smart-farm/ingest</div>
                <div>MQTT TLS: obolla/farm/&#123;farm_id&#125;/telemetry</div>
                <div>Manual upload at /smart-farm</div>
              </div>
              {linkedFarmId && <p className="mt-3 text-xs text-[var(--color-market-hover)]">Farm context: {linkedFarmId}</p>}
            </div>
          </div>
        </div>
      )}

      {requiresOllama && (
        <>
          <div className="mt-4 rounded-2xl border border-amber-300/80 bg-amber-50 p-4 sm:p-5">
            <p className="font-semibold text-amber-950">{tr('skillOllamaTitle')}</p>
            <p className="mt-2 text-sm font-medium leading-relaxed text-amber-900/90">
              {locale === 'th' ? (
                <>
                  ระดับฟรีนี้รัน{' '}
                  <a
                    href={FABLE5_LORA_HF_URL}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="font-mono font-semibold text-amber-950 underline underline-offset-2 hover:text-[var(--color-text)]"
                  >
                    hotdogs/qwen3.6-27b-fable5-lora
                  </a>{' '}
                  เป็น <span className="font-mono font-semibold text-amber-950">qwen3.6-27b-fable5</span> บน GPU
                  ของคุณ — ครบสี่ขั้น ไม่มี cloud fallback
                </>
              ) : (
                <>
                  This free tier runs{' '}
                  <a
                    href={FABLE5_LORA_HF_URL}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="font-mono font-semibold text-amber-950 underline underline-offset-2 hover:text-[var(--color-text)]"
                  >
                    hotdogs/qwen3.6-27b-fable5-lora
                  </a>{' '}
                  as <span className="font-mono font-semibold text-amber-950">qwen3.6-27b-fable5</span> on your
                  GPU — all four steps. No cloud fallback.
                </>
              )}
            </p>
            {upgradeSkillId && (
              <Link
                to={upgradeSkillId === '33333333-3333-4333-8333-333333333310' ? '/agent-ready' : `/expert-skills/${upgradeSkillId}`}
                className="mt-3 inline-block text-sm font-bold text-[var(--color-market-hover)] hover:underline"
              >
                {tr('skillOllamaUpgrade')}
              </Link>
            )}
          </div>
        </>
      )}

      {skill.slug === 'fable5-coding-agent-premium' && (
        <div className="mt-6 rounded-2xl border border-violet-200 bg-violet-50/90 p-4 sm:p-5">
          <p className="font-semibold text-violet-950">{tr('skillCloudPremiumTitle')}</p>
          <p className="mt-2 text-sm font-medium leading-relaxed text-violet-900/90">{tr('skillCloudPremiumBody')}</p>
        </div>
      )}

      {/* What 1 run includes — more beautiful + professional */}
      <div className="mt-6 sm:mt-7 pro-section">
        <div className="mb-4 flex items-baseline justify-between">
          <div>
            <h2 className="form-section-title">{tr('skillWhatYouGet')}</h2>
            <p className="text-sm text-[var(--color-text-soft)]">{pipelineLabel} — {deliverables.length} deliverables</p>
          </div>
          <div className="font-mono text-sm font-semibold text-[var(--color-market-hover)]">{isFreeRun ? 'Free' : `$${price.toFixed(2)}`}</div>
        </div>

        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
          {deliverables.map((item, idx) => (
            <div key={idx} className="rounded-2xl border border-[var(--color-border)] bg-white p-5 transition hover:shadow-sm">
              <div className="text-2xl mb-2">{item.icon}</div>
              <div className="font-semibold text-[var(--color-text)]">{item.title}</div>
              <div className="mt-1 text-sm leading-snug text-readable-muted">{item.desc}</div>
            </div>
          ))}
        </div>
      </div>

      {/* Before & After from case studies */}
      {featuredShowcase?.before_after && (
        <div className="mt-6">
          <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
            <h2 className="text-sm font-bold uppercase tracking-wide text-[var(--color-text)]">
              {tr('skillRealResults')}
            </h2>
            <Link
              to={`/showcases/${featuredShowcase.id}`}
              className="text-xs font-semibold text-[var(--color-market-hover)] hover:underline"
            >
              {featuredShowcase.site_name} {tr('skillCaseStudySuffix')}
            </Link>
          </div>
          <BeforeAfterSection data={featuredShowcase.before_after} />
        </div>
      )}

      <div className="mt-5 grid gap-5 sm:mt-7 sm:gap-6 lg:grid-cols-2">
        {/* Tools & pipeline — polished */}
        <div className="pro-section">
          <h2 className="form-section-title mb-3">{tr('skillToolsTitle')}</h2>
          {typeof skill.crew_config?.model_tier_id === 'string' && skill.crew_config.model_tier_id !== 'standard' && !skill.model_tier_runtime?.downgraded && (
            <p className="mb-3 text-sm font-medium text-readable-muted">
              {tr('skillModelTier')}: {String(locale === 'th' ? (skill.crew_config.model_tier_label_th ?? skill.crew_config.model_tier_id) : (skill.crew_config.model_tier_label_en ?? skill.crew_config.model_tier_id))}
            </p>
          )}

          <ol className="space-y-2.5">
            {steps.map((step, index) => (
              <li key={step.id} className="pipeline-step text-sm">
                <div className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-[var(--color-sage)]/30 text-xs font-bold text-[var(--color-market-hover)] mt-0.5">{index + 1}</div>
                <div className="min-w-0 flex-1">
                  <div className="font-medium">{localizeStepTitle(locale, step.title)}</div>
                  <div className="text-xs text-readable-muted truncate">{step.step_type === 'tool' ? formatToolLabel(step.tool_or_model ?? '') : step.tool_or_model}</div>
                </div>
              </li>
            ))}
          </ol>
        </div>

        {/* Capabilities */}
        <div className="pro-section">
          <h2 className="form-section-title mb-4">{tr('skillCapabilities')}</h2>
          <div className="flex flex-wrap gap-2">
            {(skill.capabilities ?? []).map((cap) => (
              <span key={cap} className="rounded-xl border border-emerald-200 bg-emerald-50/70 px-3.5 py-1 text-sm font-medium text-[var(--color-text)]">
                {localizeCapability(locale, cap)}
              </span>
            ))}
          </div>
          {skill.skill_preview && (
            <details className="mt-5 rounded-xl border bg-white p-4">
              <summary className="cursor-pointer text-sm font-semibold text-[var(--color-text-soft)]">{tr('skillPlaybook')}</summary>
              <pre className="mt-3 max-h-52 overflow-auto whitespace-pre-wrap text-xs font-medium text-readable-muted font-sans bg-[var(--color-surface-overlay)] p-3 rounded">{skill.skill_preview}</pre>
            </details>
          )}
        </div>
      </div>

      {/* Run Agent Flow — beautiful, pro, mobile friendly */}
      <div
        ref={runSectionRef}
        id="run"
        className="mt-6 pro-section border-2 border-[var(--color-sage)]/50 bg-white sm:mt-8"
      >
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-y-1">
          <h2 className="text-[19px] font-semibold tracking-[-0.01em]">{runTitle}</h2>
          <div className="text-xs text-[var(--color-text-soft)] font-medium">{pipelineLabel}</div>
        </div>
        <p className="mt-1.5 text-sm text-readable-muted">
          {inputMode === 'task' ? tr('skillRunDescribeTask') : tr('skillRunPasteUrl')}
          {skillMeta.runHint ? ` — ${skillMeta.runHint}` : ''}. {tr('skillRunProgressHint')}
        </p>

        {!user ? (
          <div className="mt-5 rounded-xl border border-[var(--color-sage)]/50 bg-[var(--color-surface-overlay)]/80 p-4 sm:p-5">
            <p className="text-sm font-medium text-[var(--color-text)]">
              {tr('skillFreeAccount')}{' '}
              <span className="font-semibold text-[var(--color-market-hover)]">{tr('skillFreeCredit')}</span>,{' '}
              {isTaskMode
                ? trf('skillEnoughCodingRuns', { amount: estLlm.toFixed(2) })
                : trf('skillEnoughFirstAudit', { amount: estTotal.toFixed(2) })}
            </p>
            <div className="mt-4 flex flex-wrap gap-3">
              <Link
                to="/register"
                state={{ from: location }}
                className="rounded-xl bg-[var(--color-market)] px-5 py-2.5 text-sm font-bold text-white hover:bg-[var(--color-market-hover)]"
              >
                {runTitle}
              </Link>
              <Link
                to="/login"
                state={{ from: location }}
                className="rounded-lg border border-[var(--color-border)] px-5 py-2.5 text-sm text-[var(--color-text-soft)]"
              >
                {tr('skillHaveAccount')}
              </Link>
            </div>
          </div>
        ) : (
          <form onSubmit={handleRun} className="mt-5 space-y-4">
            {estimate && (
              <div className="rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)] px-4 py-3 text-sm">
                <p className="text-[var(--color-text-soft)]">
                  {isFreeRun ? (
                    <>
                      {tr('skillFeeZero')}{' '}
                      <span className="font-mono font-semibold text-emerald-800">$0</span>.{' '}
                      <span className="font-mono font-semibold text-[var(--color-market-hover)]">~${estLlm.toFixed(2)}</span>{' '}
                      {tr('skillFeeLlmSuffix')}
                    </>
                  ) : (
                    <>
                      {trf('skillPayWhenDone', { amount: estTotal.toFixed(2) })}
                    </>
                  )}
                </p>
                <p className="mt-1 text-xs text-[var(--color-muted)]">
                  {tr('skillYourBalance')}: ${balance?.toFixed(2) ?? '—'}
                  {!canAfford && (
                    <span className="font-medium text-red-700">
                      {' '}
                      {tr('skillNotEnough')}{' '}
                      <Link to="/billing" className="underline">
                        {tr('skillAddCredits')}
                      </Link>
                    </span>
                  )}
                </p>
              </div>
            )}
            <RemoteSupportConsent
              checked={consentAccepted}
              onChange={setConsentAccepted}
              disabled={running}
              inputMode={inputMode}
            />
            {inputMode === 'task' && (
              <LocalBridgeSelector
                devices={bridgeDevices}
                enabled={bridgeEnabled}
                onEnabledChange={setBridgeEnabled}
                deviceId={bridgeDeviceId}
                onDeviceIdChange={setBridgeDeviceId}
                hint={tr('bridgeHint')}
              />
            )}
            {isTaskMode && isLineartKemlife && lineartPresets && (
              <LineartPresetPicker
                format={lineartFormat}
                locale={locale}
                selection={lineartPresets}
                onChange={setLineartPresets}
              />
            )}
            <div>
              <label className="form-label mb-1.5 block">
                {inputMode === 'task'
                  ? isLineartKemlife
                    ? tr('skillExtraNotes')
                    : tr('skillTaskLabel')
                  : tr('skillUrlLabel')}
              </label>
              {inputMode === 'task' ? (
                <>
                <SpeechToTextControl
                  prominent
                  hintKey="sttTaskHint"
                  showLanguageToggle={false}
                  disabled={running}
                  value={task}
                  onChange={(v) => {
                    setTask(v)
                    if (error) setError('')
                  }}
                  className="mb-2"
                />
                <textarea
                  rows={4}
                  value={task}
                  onChange={(e) => {
                    setTask(e.target.value)
                    if (error) setError('')
                  }}
                  placeholder={
                    isLineartKemlife
                      ? locale === 'th'
                        ? lineartFormat === 'reel'
                          ? 'เช่น อยากเน้น hook เรื่องลืมความฝัน / ความยาว 60 วิ / อ้างอิง Reel ตัวอย่าง'
                          : 'เช่น อยากทำคลิป 10 นาที เรื่องลืมความฝัน / อ้างอิงช่อง Zenn'
                        : lineartFormat === 'reel'
                          ? 'e.g. 60s reel on forgetting dreams / match reference Reel pacing'
                          : 'e.g. 10-min video on dream forgetting / Zenn-style curiosity'
                      : skill.category === 'content'
                        ? tr('skillTaskPlaceholderContent')
                        : tr('skillTaskPlaceholderDefault')
                  }
                  className="form-input resize-y min-h-[100px]"
                />
                </>
              ) : (
                <input
                  required
                  type="text"
                  inputMode="url"
                  autoComplete="url"
                  value={task}
                  onChange={(e) => {
                    setTask(e.target.value)
                    if (error && error.includes('valid URL')) setError('')
                  }}
                  placeholder="yoursite.com or https://yoursite.com"
                  className="form-input"
                />
              )}
              <p className="mt-1.5 text-xs font-medium text-readable-muted">
                {inputMode === 'task'
                  ? isLineartKemlife
                    ? tr('skillTaskHintLineart')
                    : tr('skillTaskHintDefault')
                  : tr('skillTaskHintUrl')}
              </p>
              {isTaskMode && isLineartKemlife && lineartPresets && (
                <p className="mt-2 rounded-lg bg-[var(--color-surface-overlay)] px-3 py-2 font-mono text-xs text-readable-muted whitespace-pre-wrap">
                  {buildLineartPresetBlock(lineartPresets).trim()}
                </p>
              )}
            </div>
            {running && (
              <p className="text-sm font-medium text-[var(--color-market-hover)] animate-pulse">
                {isTaskMode ? tr('skillStartingPipeline') : tr('skillStartingAudit')} {runSeconds}s —{' '}
                {tr('skillOpeningProgress')}.
              </p>
            )}
            {error && (
              <p className="rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-sm font-medium text-red-800">
                {error}
                {error.toLowerCase().includes('insufficient') && (
                  <>
                    {' '}
                    <Link to="/billing" className="underline">
                      Add credits
                    </Link>
                  </>
                )}
              </p>
            )}
            <button
              type="submit"
              disabled={running || !consentAccepted || (estimate != null && !canAfford)}
              className="touch-target w-full rounded-2xl bg-[var(--color-market)] px-8 py-[15px] text-sm font-bold text-white hover:bg-[var(--color-market-hover)] disabled:opacity-50 active:scale-[0.985] transition"
            >
              {running ? `${tr('skillRunning')} ${runSeconds}s` : runCta}
            </button>
          </form>
        )}
      </div>

      <div className="mt-8">
        <SecurityTrustStrip compact />
      </div>
    </div>
  )
}