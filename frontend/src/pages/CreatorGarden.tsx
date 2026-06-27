import { useCallback, useEffect, useMemo, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { api, apiErrorMessage } from '../api/client'
import { SpeechToTextControl } from '../components/SpeechToTextControl'
import { GardenAttachmentBar } from '../components/garden/GardenAttachmentBar'
import { GardenModelTierPicker } from '../components/garden/GardenModelTierPicker'
import { PublishReadinessPanel } from '../components/garden/PublishReadinessPanel'
import {
  mergeStoryWithAttachments,
  type GardenAttachment,
} from '../components/garden/gardenAttachments'
import { useAuth } from '../context/AuthContext'
import { useLocale } from '../context/LocaleContext'
import {
  GARDEN_STORAGE_KEY,
  GARDEN_STORY_KEY,
  OBOLLA_COMPANION_TH,
  OBOLLA_GARDEN_STORY_EN,
  OBOLLA_GARDEN_STORY_TH,
  OBOLLA_MANIFESTO_EN,
  OBOLLA_MANIFESTO_TH,
} from '../config/obollaManifesto'
import { LineartPresetPicker, defaultLineartSelection } from '../components/lineart/LineartPresetPicker'
import {
  GARDEN_STORY_TEMPLATES,
  LINEART_FACEBOOK_REEL_KEMLIFE_SKILL_ID,
  LINEART_YOUTUBE_KEMLIFE_SKILL_ID,
} from '../config/gardenStoryTemplates'
import {
  mergeLineartPresetsIntoText,
  type LineartFormat,
  type LineartPresetSelection,
} from '../config/lineartKemlifePresets'
import type { StringKey } from '../i18n/strings'
import { composeGardenStoryFallback } from '../lib/gardenComposeFallback'
import type {
  CreatorGardenCoachResponse,
  CreatorGardenSuggestedDraft,
  GardenModelTier,
} from '../types'

type GardenMode = 'compose' | 'steps'
type GardenStep = 'identity' | 'audience' | 'problem' | 'workflow' | 'publish'

type GardenDraft = {
  identity: string
  audience: string
  problem: string
  workflow_name: string
  workflow_description: string
  price_note: string
  selected_idea_index: number
}

const STEPS: { id: GardenStep; labelKey: StringKey }[] = [
  { id: 'identity', labelKey: 'stepIdentity' },
  { id: 'audience', labelKey: 'stepAudience' },
  { id: 'problem', labelKey: 'stepProblem' },
  { id: 'workflow', labelKey: 'stepWorkflow' },
  { id: 'publish', labelKey: 'stepPublish' },
]

const COMPANION_EN = "We're beside you — keep going, one step at a time."

function emptyDraft(): GardenDraft {
  return {
    identity: '',
    audience: '',
    problem: '',
    workflow_name: '',
    workflow_description: '',
    price_note: '',
    selected_idea_index: 0,
  }
}

function loadDraft(): GardenDraft {
  try {
    const raw = localStorage.getItem(GARDEN_STORAGE_KEY)
    if (!raw) return emptyDraft()
    return { ...emptyDraft(), ...JSON.parse(raw) }
  } catch {
    return emptyDraft()
  }
}

function loadStory(): string {
  try {
    return localStorage.getItem(GARDEN_STORY_KEY) || ''
  } catch {
    return ''
  }
}

function slugify(name: string): string {
  return name
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-|-$/g, '')
}

function productDraftFromSuggested(suggested: CreatorGardenSuggestedDraft, draft?: GardenDraft) {
  return {
    name: draft?.workflow_name || suggested.name || '',
    description: draft?.workflow_description || suggested.description || '',
    category: suggested.category || '',
    capabilities: (suggested.capabilities ?? []).join(', '),
    price: suggested.suggested_price_usd || '0.99',
    input_mode: suggested.input_mode || 'task',
    pipeline_label: suggested.pipeline_label || '',
    run_title: suggested.run_title || '',
    skill_md: suggested.skill_md || '',
    model_tier_id: suggested.model_tier_id || 'standard',
    crew_config: suggested.crew_config || {},
    from_garden: true,
  }
}

export function CreatorGarden() {
  const { locale, tr } = useLocale()
  const { user, token } = useAuth()
  const navigate = useNavigate()

  const [mode, setMode] = useState<GardenMode>('compose')
  const [rawStory, setRawStory] = useState(loadStory)
  const [linkedSkillId, setLinkedSkillId] = useState<string | null>(null)
  const [lineartPresets, setLineartPresets] = useState<LineartPresetSelection>(() =>
    defaultLineartSelection('reel', locale),
  )
  const [step, setStep] = useState<GardenStep>('identity')
  const [draft, setDraft] = useState<GardenDraft>(loadDraft)
  const [coach, setCoach] = useState<CreatorGardenCoachResponse | null>(null)
  const [coaching, setCoaching] = useState(false)
  const [pdfImporting, setPdfImporting] = useState(false)
  const [creating, setCreating] = useState(false)
  const [createError, setCreateError] = useState('')
  const [modelTiers, setModelTiers] = useState<GardenModelTier[]>([])
  const [basePriceUsd, setBasePriceUsd] = useState('0.99')
  const [selectedTierId, setSelectedTierId] = useState('standard')
  const [tierApplying, setTierApplying] = useState(false)
  const [attachments, setAttachments] = useState<GardenAttachment[]>([])

  const lineartFormat: LineartFormat =
    linkedSkillId === LINEART_YOUTUBE_KEMLIFE_SKILL_ID ? 'youtube' : 'reel'
  const showLineartPresets =
    linkedSkillId === LINEART_FACEBOOK_REEL_KEMLIFE_SKILL_ID ||
    linkedSkillId === LINEART_YOUTUBE_KEMLIFE_SKILL_ID ||
    linkedSkillId === null

  useEffect(() => {
    setLineartPresets((prev) => {
      if (prev.format === lineartFormat && prev.language === locale) return prev
      return { ...defaultLineartSelection(lineartFormat, locale), customTopic: prev.customTopic }
    })
  }, [lineartFormat, locale])

  const stepIndex = STEPS.findIndex((s) => s.id === step)
  const gardenStory = locale === 'th' ? OBOLLA_GARDEN_STORY_TH : OBOLLA_GARDEN_STORY_EN
  const manifesto = locale === 'th' ? OBOLLA_MANIFESTO_TH : OBOLLA_MANIFESTO_EN

  const coachMessage = useMemo(() => {
    if (!coach) return ''
    return locale === 'th' ? coach.message_th : (coach.message_en ?? coach.message_th)
  }, [coach, locale])

  const companionLine = useMemo(() => {
    if (!coach) return locale === 'th' ? OBOLLA_COMPANION_TH : COMPANION_EN
    return locale === 'th' ? (coach.companion_th ?? OBOLLA_COMPANION_TH) : COMPANION_EN
  }, [coach, locale])

  const suggested = coach?.suggested_draft
  const composed = Boolean(coach?.composed && suggested?.name)
  const valueInsight = coach?.value_insight ?? null

  const persist = useCallback((next: GardenDraft) => {
    setDraft(next)
    localStorage.setItem(GARDEN_STORAGE_KEY, JSON.stringify(next))
  }, [])

  const resetCompose = useCallback(() => {
    setRawStory('')
    setAttachments([])
    setCoach(null)
    setCreateError('')
    setLinkedSkillId(null)
    setLineartPresets(defaultLineartSelection('reel', locale))
    localStorage.removeItem(GARDEN_STORY_KEY)
  }, [locale])

  const hasComposeContent =
    Boolean(rawStory.trim()) || attachments.length > 0 || Boolean(coach) || Boolean(createError)

  const askCompanion = useCallback(
    async (currentStep: GardenStep, answers: GardenDraft) => {
      setCoaching(true)
      try {
        const response = await api.creatorGardenCoach({
          step: currentStep,
          answers: answers as unknown as Record<string, string>,
        })
        setCoach(response)
        if (currentStep === 'problem' && response.workflow_ideas.length > 0) {
          const idea = response.workflow_ideas[answers.selected_idea_index] ?? response.workflow_ideas[0]
          persist({
            ...answers,
            workflow_name: answers.workflow_name || idea.name,
            workflow_description: answers.workflow_description || idea.pitch,
          })
        }
      } catch {
        setCoach({
          message_th: OBOLLA_COMPANION_TH,
          message_en: COMPANION_EN,
          workflow_ideas: [],
          suggested_draft: {},
          companion_th: OBOLLA_COMPANION_TH,
        })
      } finally {
        setCoaching(false)
      }
    },
    [persist],
  )

  const applyGardenResponse = useCallback(
    (response: CreatorGardenCoachResponse) => {
      setCoach(response)
      if (response.model_tiers?.length) setModelTiers(response.model_tiers)
      const s = response.suggested_draft
      if (s?.model_tier_id) setSelectedTierId(s.model_tier_id)
      if (s?.name) {
        persist({
          ...draft,
          identity: s.identity || draft.identity,
          audience: s.audience || draft.audience,
          problem: s.problem || draft.problem,
          workflow_name: s.name,
          workflow_description: s.description || '',
        })
      }
      if (response.pdf_import) {
        const summary =
          locale === 'th'
            ? response.pdf_import.summary_th
            : response.pdf_import.summary_en
        if (summary) {
          const header =
            locale === 'th'
              ? `[จาก PDF: ${response.pdf_import.filename}]\n\n`
              : `[From PDF: ${response.pdf_import.filename}]\n\n`
          setRawStory(`${header}${summary}`)
        }
      }
    },
    [draft, locale, persist],
  )

  const importPdfSkill = useCallback(
    async (file: File) => {
      setPdfImporting(true)
      setCreateError('')
      try {
        const response = await api.creatorGardenImportPdf(file, locale, selectedTierId)
        applyGardenResponse(response)
        if (!response.composed && response.error) {
          setCreateError(response.error)
        }
      } catch (err) {
        setCreateError(err instanceof Error ? err.message : 'Could not import PDF')
        setCoach({
          message_th: 'ขออภัยครับ — ลอง PDF อื่นหรือพิมพ์สรุปในช่องด้านล่างแทน เราอยู่ข้างคุณ',
          message_en: 'Sorry — try another PDF or paste a summary below. We are still beside you.',
          workflow_ideas: [],
          suggested_draft: {},
          companion_th: OBOLLA_COMPANION_TH,
          composed: false,
        })
      } finally {
        setPdfImporting(false)
      }
    },
    [applyGardenResponse, locale, selectedTierId],
  )

  const storyForCompose = useMemo(
    () => mergeStoryWithAttachments(rawStory, attachments, locale),
    [rawStory, attachments, locale],
  )

  const composeStory = useCallback(async () => {
    setCoaching(true)
    setCreateError('')
    localStorage.setItem(GARDEN_STORY_KEY, rawStory)
    try {
      const response = await api.creatorGardenCompose({
        raw_story: storyForCompose,
        locale,
        model_tier_id: selectedTierId,
      })
      applyGardenResponse(response)
    } catch {
      applyGardenResponse(composeGardenStoryFallback(storyForCompose, locale, selectedTierId))
    } finally {
      setCoaching(false)
    }
  }, [applyGardenResponse, locale, rawStory, selectedTierId, storyForCompose])

  const applyModelTier = useCallback(
    async (tierId: string) => {
      if (!suggested?.crew_config) {
        setSelectedTierId(tierId)
        return
      }
      setTierApplying(true)
      setCreateError('')
      try {
        const applied = await api.creatorGardenApplyTier({
          model_tier_id: tierId,
          crew_config: suggested.crew_config,
        })
        setSelectedTierId(applied.model_tier_id)
        setCoach((prev) =>
          prev
            ? {
                ...prev,
                suggested_draft: {
                  ...prev.suggested_draft,
                  model_tier_id: applied.model_tier_id,
                  suggested_price_usd: applied.suggested_price_usd,
                  pipeline_label: applied.pipeline_label ?? prev.suggested_draft.pipeline_label,
                  crew_config: applied.crew_config,
                },
              }
            : prev,
        )
      } catch (err) {
        setCreateError(err instanceof Error ? err.message : 'Could not apply model tier')
      } finally {
        setTierApplying(false)
      }
    },
    [suggested?.crew_config],
  )

  useEffect(() => {
    api
      .getGardenModelTiers()
      .then((res) => {
        setModelTiers(res.tiers)
        setBasePriceUsd(res.base_price_usd)
      })
      .catch(() => {
        // tiers optional — compose still works
      })
  }, [])

  useEffect(() => {
    if (mode !== 'steps') return
    askCompanion(step, draft)
  }, [step, mode]) // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    localStorage.setItem(GARDEN_STORY_KEY, rawStory)
  }, [rawStory])

  useEffect(() => {
    localStorage.setItem(GARDEN_STORAGE_KEY, JSON.stringify(draft))
  }, [draft])

  function updateField<K extends keyof GardenDraft>(key: K, value: GardenDraft[K]) {
    persist({ ...draft, [key]: value })
  }

  function selectIdea(index: number) {
    const idea = coach?.workflow_ideas[index]
    if (!idea) return
    persist({
      ...draft,
      selected_idea_index: index,
      workflow_name: idea.name,
      workflow_description: idea.pitch,
    })
  }

  function goNext() {
    const next = STEPS[stepIndex + 1]
    if (next) setStep(next.id)
  }

  function goBack() {
    const prev = STEPS[stepIndex - 1]
    if (prev) setStep(prev.id)
  }

  function saveProductDraftAndNavigate() {
    const productDraft = productDraftFromSuggested(suggested ?? {}, draft)
    localStorage.setItem('obolla-garden-product-draft', JSON.stringify(productDraft))
    if (user) {
      navigate('/creator/products/new')
    } else {
      navigate('/register', { state: { from: { pathname: '/creator/products/new' } } })
    }
  }

  async function createFlowNow() {
    if (!suggested?.name && !draft.workflow_name) return
    setCreating(true)
    setCreateError('')
    const productDraft = productDraftFromSuggested(suggested ?? {}, draft)
    const flowName = productDraft.name
    const flowDesc = productDraft.description

    if (token && user) {
      try {
        const created = await api.createCreatorSkill(token, {
          name: flowName,
          slug: slugify(flowName) || `flow-${Date.now()}`,
          description: flowDesc || flowName,
          category: productDraft.category || undefined,
          price_usd_per_run: productDraft.price,
        })
        const ceiling =
          valueInsight?.pricing_ceiling_usd ?? valueInsight?.max_price_usd ?? productDraft.price
        const crewConfig = {
          ...(suggested?.crew_config ?? {
            input_mode: productDraft.input_mode,
            pipeline_label: productDraft.pipeline_label,
            run_title: productDraft.run_title,
            skill_md: productDraft.skill_md,
            category: productDraft.category || undefined,
          }),
          pricing_ceiling_usd: ceiling,
          value_score: valueInsight?.value_score,
          value_tier: valueInsight?.value_tier,
        }
        await api.updateCreatorSkill(token, created.id, {
          capabilities: productDraft.capabilities
            .split(',')
            .map((c) => c.trim())
            .filter(Boolean),
          crew_config: crewConfig,
          is_active: false,
        })
        setCreating(false)
        navigate(`/creators/${user.id}`, {
          replace: true,
          state: {
            gardenWelcome: true,
            newSkillId: created.id,
            flowName,
          },
        })
        return
      } catch (err) {
        setCreateError(apiErrorMessage(err, locale))
        setCreating(false)
        return
      }
    }

    saveProductDraftAndNavigate()
    setCreating(false)
  }

  const inputClass =
    'w-full rounded-xl border-2 border-[var(--color-border)] bg-white p-4 text-lg font-medium leading-relaxed text-[var(--color-text)] placeholder:text-[var(--color-muted)] focus:border-[var(--color-sage)] focus:ring-4 focus:ring-[var(--color-sage)]/20 focus:outline-none'

  const attachmentLabels = {
    attach: tr('gardenAttachPdf'),
    pdf: tr('gardenAttachPdf'),
    image: tr('gardenAttachImage'),
    link: tr('gardenAttachLink'),
    linkPrompt: tr('gardenAttachLinkPrompt'),
    addLink: tr('gardenAttachAddLink'),
    cancel: tr('gardenAttachCancel'),
  }

  return (
    <div className="garden-studio mx-auto max-w-5xl px-4 py-4 sm:py-8 sm:px-6">
      <p className="hidden text-sm font-bold uppercase tracking-[0.2em] text-[var(--color-sage)] sm:block">
        {tr('gardenEyebrow')}
      </p>
      <h1 className="mt-0 text-2xl font-bold text-[var(--color-text)] sm:mt-2 sm:text-4xl">{tr('gardenTitle')}</h1>
      <p className="mt-1 text-sm font-medium text-readable-muted sm:mt-2">{tr('gardenMobileHint')}</p>
      <p className="mt-1 hidden text-base font-medium text-readable-muted md:block">{tr('gardenSubtitle')}</p>

      <section className="garden-promise garden-card mt-3 p-3 sm:mt-4 sm:p-4" aria-label={tr('gardenPromise')}>
        <p className="text-sm font-bold leading-snug text-[var(--color-text)]">{tr('gardenPromise')}</p>
        <ol className="mt-2.5 grid gap-2 sm:grid-cols-3 sm:gap-3">
          {(['gardenStep1', 'gardenStep2', 'gardenStep3'] as const).map((key, index) => (
            <li key={key} className="flex items-start gap-2 text-xs font-medium leading-snug text-readable-muted sm:text-sm">
              <span className="flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-[var(--color-sage)]/25 text-[10px] font-bold text-[var(--color-market-hover)]">
                {index + 1}
              </span>
              <span className="pt-0.5 text-[var(--color-text)]">{tr(key)}</span>
            </li>
          ))}
        </ol>
      </section>

      <section className="garden-card mt-6 hidden bloom-accent p-6 md:block sm:p-8">
        <h2 className="text-xl font-semibold text-[var(--color-text)]">{tr('gardenStoryTitle')}</h2>
        <div className="mt-4 space-y-3 text-base font-medium leading-relaxed text-readable-muted">
          {gardenStory.map((para) => (
            <p key={para}>{para}</p>
          ))}
        </div>
        <blockquote className="mt-6 border-l-4 border-[var(--color-sage)] pl-4 text-base font-medium italic text-[var(--color-text)]">
          {manifesto}
        </blockquote>
      </section>

      <div className="mt-3 flex flex-wrap gap-2 sm:mt-6">
        <button
          type="button"
          onClick={() => setMode('compose')}
          className={`rounded-full px-4 py-2 text-sm font-bold transition-colors sm:px-5 sm:py-2.5 sm:text-base ${
            mode === 'compose'
              ? 'bg-[var(--color-market)] text-white shadow-md'
              : 'border-2 border-[var(--color-border)] bg-white text-[var(--color-text-soft)]'
          }`}
        >
          {tr('gardenModeCompose')}
        </button>
        <button
          type="button"
          onClick={() => setMode('steps')}
          className={`hidden rounded-full px-4 py-2 text-sm font-bold transition-colors sm:inline-flex sm:px-5 sm:py-2.5 sm:text-base ${
            mode === 'steps'
              ? 'bg-[var(--color-market)] text-white shadow-md'
              : 'border-2 border-[var(--color-border)] bg-white text-[var(--color-text-soft)]'
          }`}
        >
          {tr('gardenModeSteps')}
        </button>
      </div>

      <div className="mt-4 grid gap-6 sm:mt-8 lg:grid-cols-5 lg:gap-8">
        <div className="lg:col-span-3">
          {mode === 'compose' ? (
            <div className="garden-compose-main space-y-4">
              <div className="garden-card p-4 sm:p-6 lg:p-8">
                <h3 className="hidden text-lg font-semibold text-[var(--color-text)] sm:block">
                  {tr('gardenComposeTitle')}
                </h3>
                <div className="mb-3 flex flex-wrap items-start justify-between gap-3">
                  <SpeechToTextControl
                    prominent
                    disabled={coaching || pdfImporting}
                    value={rawStory}
                    onChange={setRawStory}
                    showClearButton={hasComposeContent}
                    onClear={resetCompose}
                    clearLabelKey="gardenClearAll"
                    className="flex-1 min-w-[min(100%,18rem)]"
                  />
                </div>
                {hasComposeContent && (
                  <p className="mb-3 text-xs font-medium text-readable-muted">{tr('gardenClearAllHint')}</p>
                )}
                <textarea
                  value={rawStory}
                  onChange={(e) => setRawStory(e.target.value)}
                  rows={12}
                  placeholder={tr('gardenComposePlaceholder')}
                  className="garden-compose-textarea"
                  aria-label={tr('gardenComposeTitle')}
                />
                <div className="mt-3">
                  <GardenAttachmentBar
                    locale={locale}
                    disabled={coaching}
                    pdfImporting={pdfImporting}
                    attachments={attachments}
                    onAttachmentsChange={setAttachments}
                    onPdfImport={(file) => void importPdfSkill(file)}
                    labels={attachmentLabels}
                  />
                  <p className="mt-2 text-xs font-medium text-readable-muted">{tr('gardenPdfMaxSize')}</p>
                </div>

                {showLineartPresets && (
                  <details className="mt-4 rounded-xl border border-[var(--color-border)] bg-white/80 px-4 py-3">
                    <summary className="cursor-pointer text-sm font-semibold text-[var(--color-market-hover)]">
                      {tr('gardenExamplesToggle')}
                    </summary>
                    <div className="mt-4 space-y-4">
                      <LineartPresetPicker
                        format={lineartFormat}
                        locale={locale}
                        selection={lineartPresets}
                        compact
                        onChange={(next) => {
                          setLineartPresets(next)
                          setRawStory((prev) => mergeLineartPresetsIntoText(prev, next))
                        }}
                      />
                      <div className="flex flex-wrap gap-2">
                        {GARDEN_STORY_TEMPLATES.map((tpl) => (
                          <button
                            key={tpl.id}
                            type="button"
                            onClick={() => {
                              const format: LineartFormat =
                                tpl.skillId === LINEART_YOUTUBE_KEMLIFE_SKILL_ID ? 'youtube' : 'reel'
                              const presets = defaultLineartSelection(format, locale)
                              const story = locale === 'th' ? tpl.story_th : tpl.story_en
                              setLineartPresets(presets)
                              setRawStory(mergeLineartPresetsIntoText(story, presets))
                              setLinkedSkillId(tpl.skillId)
                            }}
                            className="rounded-lg border border-[var(--color-sage)]/50 bg-white px-3 py-2 text-xs font-semibold text-[var(--color-market-hover)] sm:text-sm"
                          >
                            {locale === 'th' ? tpl.label_th : tpl.label_en}
                          </button>
                        ))}
                        <Link
                          to={`/expert-skills/${linkedSkillId ?? GARDEN_STORY_TEMPLATES[0]?.skillId ?? ''}`}
                          className="rounded-lg border border-[var(--color-border)] px-3 py-2 text-xs font-medium text-readable-muted hover:text-[var(--color-text)] sm:text-sm"
                        >
                          {tr('gardenTemplateMarketplace')}
                        </Link>
                      </div>
                    </div>
                  </details>
                )}

                <div className="garden-sticky-actions mt-4 lg:mt-6">
                  {!user && (
                    <p className="mb-2 text-xs font-medium text-readable-muted">{tr('gardenComposeNoLogin')}</p>
                  )}
                  {(coachMessage || coaching) && (
                    <p className="mb-2 line-clamp-2 text-xs font-medium text-[var(--color-text-soft)] lg:hidden">
                      {coaching ? tr('gardenThinking') : coachMessage}
                    </p>
                  )}
                  <button
                    type="button"
                    disabled={coaching || pdfImporting || storyForCompose.trim().length < 8}
                    onClick={() => void composeStory()}
                    className="w-full min-h-[48px] rounded-xl bg-[var(--color-market)] px-6 py-3.5 text-base font-bold text-white shadow-md hover:bg-[var(--color-market-hover)] disabled:cursor-not-allowed disabled:opacity-50 sm:text-lg"
                  >
                    {coaching ? tr('gardenThinking') : tr('gardenComposeBtn')}
                  </button>
                </div>
              </div>

              {composed && suggested && (
                <div className="garden-card border-2 border-[var(--color-sage)]/40 p-6 sm:p-8">
                  <div className="flex flex-wrap items-center justify-between gap-2">
                    <h3 className="text-xl font-semibold text-[var(--color-text)]">{tr('gardenPreviewTitle')}</h3>
                    <span className="rounded-full bg-[var(--color-surface-overlay)] px-3 py-1 text-xs font-semibold text-[var(--color-text-soft)]">
                      {coach?.used_llm ? tr('gardenUsedLlm') : tr('gardenUsedRules')}
                    </span>
                  </div>
                  <p className="mt-2 text-base font-medium text-readable-muted">{tr('gardenComposeReady')}</p>
                  {coach?.pdf_import && (
                    <p className="mt-3 rounded-lg bg-[var(--color-surface-overlay)] px-3 py-2 text-sm font-medium text-readable-muted">
                      {tr('gardenPdfSummary')}: {coach.pdf_import.filename} · {coach.pdf_import.page_count}{' '}
                      {locale === 'th' ? 'หน้า' : 'pages'} · {coach.pdf_import.char_count}{' '}
                      {locale === 'th' ? 'ตัวอักษร' : 'chars'}
                    </p>
                  )}

                  <div className="mt-6 space-y-4 text-base">
                    <div>
                      <label className="form-label text-base">{tr('lblIdentity')}</label>
                      <input
                        value={draft.identity}
                        onChange={(e) => updateField('identity', e.target.value)}
                        className={`${inputClass} mt-1 text-base py-3`}
                      />
                    </div>
                    <div>
                      <label className="form-label text-base">{tr('lblAudience')}</label>
                      <input
                        value={draft.audience}
                        onChange={(e) => updateField('audience', e.target.value)}
                        className={`${inputClass} mt-1 text-base py-3`}
                      />
                    </div>
                    <div>
                      <label className="form-label text-base">{tr('lblFlow')}</label>
                      <input
                        value={draft.workflow_name}
                        onChange={(e) => updateField('workflow_name', e.target.value)}
                        className={`${inputClass} mt-1 text-base py-3`}
                      />
                    </div>
                    <div>
                      <label className="form-label text-base">{tr('phFlowDesc')}</label>
                      <textarea
                        value={draft.workflow_description}
                        onChange={(e) => updateField('workflow_description', e.target.value)}
                        rows={3}
                        className={`${inputClass} mt-1 text-base`}
                      />
                    </div>
                    {suggested.pipeline_label && (
                      <p className="text-sm font-medium text-readable-muted">
                        <strong className="text-[var(--color-text)]">{tr('gardenPipeline')}:</strong>{' '}
                        {suggested.pipeline_label}
                      </p>
                    )}
                    {suggested.suggested_price_usd && (
                      <p className="text-base font-semibold text-[var(--color-text)]">
                        {tr('gardenPriceLabel')}:{' '}
                        <span className="text-[var(--color-terracotta)]">${suggested.suggested_price_usd}</span>
                      </p>
                    )}
                  </div>

                  {modelTiers.length > 0 && (
                    <GardenModelTierPicker
                      tiers={modelTiers}
                      selectedId={selectedTierId}
                      locale={locale}
                      basePriceUsd={basePriceUsd}
                      disabled={tierApplying || coaching}
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
                  )}

                  {valueInsight && (
                    <div className="mt-6">
                      <PublishReadinessPanel
                        insight={valueInsight}
                        compact
                        currentPrice={suggested.suggested_price_usd}
                      />
                    </div>
                  )}

                  {createError && (
                    <p className="mt-4 rounded-lg bg-red-50 px-4 py-3 text-sm font-medium text-red-800">{createError}</p>
                  )}

                  <div className="mt-8 flex flex-col gap-3 sm:flex-row sm:flex-wrap">
                    <button
                      type="button"
                      disabled={creating || !draft.workflow_name}
                      onClick={() => void createFlowNow()}
                      className="flex-1 rounded-xl bg-[var(--color-terracotta)] px-6 py-4 text-lg font-bold text-white shadow-md hover:opacity-95 disabled:opacity-50"
                    >
                      {creating ? tr('gardenCreating') : tr('gardenCreateFlow')}
                    </button>
                    <button
                      type="button"
                      disabled={creating}
                      onClick={saveProductDraftAndNavigate}
                      className="rounded-xl border-2 border-[var(--color-border)] px-5 py-4 text-base font-semibold text-[var(--color-text)] hover:bg-[var(--color-surface-overlay)]"
                    >
                      {tr('gardenEditAfter')}
                    </button>
                  </div>
                </div>
              )}
            </div>
          ) : (
            <>
              <div className="mb-6 flex flex-wrap gap-2">
                {STEPS.map((s, i) => (
                  <button
                    key={s.id}
                    type="button"
                    onClick={() => setStep(s.id)}
                    className={`rounded-full px-4 py-2 text-sm font-semibold transition-colors ${
                      step === s.id
                        ? 'bg-[var(--color-market)] text-white shadow-sm'
                        : i < stepIndex
                          ? 'bg-[var(--color-surface-overlay)] text-[var(--color-text)]'
                          : 'border border-[var(--color-border)] bg-white text-[var(--color-text-soft)]'
                    }`}
                  >
                    {i + 1}. {tr(s.labelKey)}
                  </button>
                ))}
              </div>

              <div className="garden-card p-6">
                <h3 className="text-lg font-semibold text-[var(--color-text)]">{tr(STEPS[stepIndex].labelKey)}</h3>

                {step === 'identity' && (
                  <>
                    <SpeechToTextControl
                      prominent
                      value={draft.identity}
                      onChange={(v) => updateField('identity', v)}
                      className="mt-4"
                    />
                    <textarea
                      value={draft.identity}
                      onChange={(e) => updateField('identity', e.target.value)}
                      rows={4}
                      placeholder={tr('phIdentity')}
                      className={`${inputClass} mt-3 text-base`}
                    />
                  </>
                )}

                {step === 'audience' && (
                  <>
                    <SpeechToTextControl
                      prominent
                      value={draft.audience}
                      onChange={(v) => updateField('audience', v)}
                      className="mt-4"
                    />
                    <textarea
                      value={draft.audience}
                      onChange={(e) => updateField('audience', e.target.value)}
                      rows={3}
                      placeholder={tr('phAudience')}
                      className={`${inputClass} mt-3 text-base`}
                    />
                  </>
                )}

                {step === 'problem' && (
                  <>
                    <SpeechToTextControl
                      prominent
                      value={draft.problem}
                      onChange={(v) => updateField('problem', v)}
                      className="mt-4"
                    />
                    <textarea
                      value={draft.problem}
                      onChange={(e) => updateField('problem', e.target.value)}
                      rows={4}
                      placeholder={tr('phProblem')}
                      className={`${inputClass} mt-3 text-base`}
                    />
                  </>
                )}

                {step === 'workflow' && (
                  <div className="mt-4 space-y-4">
                    {(coach?.workflow_ideas ?? []).map((idea, index) => (
                      <button
                        key={idea.name}
                        type="button"
                        onClick={() => selectIdea(index)}
                        className={`w-full rounded-xl border-2 p-4 text-left transition-colors ${
                          draft.selected_idea_index === index
                            ? 'border-[var(--color-sage)]/70 bg-[var(--color-surface-overlay)]'
                            : 'border-[var(--color-border)] hover:border-[var(--color-sage)]/40'
                        }`}
                      >
                        <p className="font-semibold text-[var(--color-text)]">{idea.name}</p>
                        <p className="mt-1 text-sm font-medium text-readable-muted">{idea.pitch}</p>
                        <p className="mt-2 text-xs font-medium text-[var(--color-text-soft)]">{idea.steps}</p>
                      </button>
                    ))}
                    <input
                      value={draft.workflow_name}
                      onChange={(e) => updateField('workflow_name', e.target.value)}
                      placeholder={tr('phFlowName')}
                      className={`${inputClass} text-base py-3`}
                    />
                    <textarea
                      value={draft.workflow_description}
                      onChange={(e) => updateField('workflow_description', e.target.value)}
                      rows={3}
                      placeholder={tr('phFlowDesc')}
                      className={`${inputClass} text-base`}
                    />
                  </div>
                )}

                {step === 'publish' && (
                  <div className="mt-4 space-y-4 text-base font-medium text-readable-muted">
                    <p>
                      <strong className="text-[var(--color-text)]">{tr('lblIdentity')}:</strong> {draft.identity || '—'}
                    </p>
                    <p>
                      <strong className="text-[var(--color-text)]">{tr('lblAudience')}:</strong> {draft.audience || '—'}
                    </p>
                    <p>
                      <strong className="text-[var(--color-text)]">{tr('lblFlow')}:</strong> {draft.workflow_name || '—'}
                    </p>
                    <p>{draft.workflow_description}</p>
                    <input
                      value={draft.price_note}
                      onChange={(e) => updateField('price_note', e.target.value)}
                      placeholder={tr('phPrice')}
                      className={`${inputClass} text-base py-3`}
                    />
                  </div>
                )}

                <div className="mt-6 flex flex-wrap gap-3">
                  {stepIndex > 0 && (
                    <button
                      type="button"
                      onClick={goBack}
                      className="rounded-lg border border-[var(--color-border)] px-4 py-2 text-sm font-medium text-[var(--color-text-soft)] hover:bg-[var(--color-surface-overlay)]"
                    >
                      {tr('gardenBack')}
                    </button>
                  )}
                  {step !== 'publish' ? (
                    <button
                      type="button"
                      onClick={goNext}
                      className="rounded-lg bg-[var(--color-market)] px-4 py-2 text-sm font-bold text-white hover:bg-[var(--color-market-hover)]"
                    >
                      {tr('gardenNext')}
                    </button>
                  ) : (
                    <button
                      type="button"
                      onClick={saveProductDraftAndNavigate}
                      className="rounded-lg bg-[var(--color-terracotta)] px-4 py-2 text-sm font-bold text-white hover:opacity-90"
                    >
                      {tr('gardenPublish')}
                    </button>
                  )}
                </div>
              </div>
            </>
          )}
        </div>

        <aside className="hidden lg:col-span-2 lg:block">
          <div className="sticky top-24 coffee-corner p-6">
            <p className="text-sm font-bold uppercase tracking-widest text-[var(--color-coffee)]">
              {tr('gardenCompanion')}
            </p>
            <p className="mt-1 text-sm font-medium text-[var(--color-coffee)]/90">{tr('gardenCompanionSub')}</p>
            {coaching ? (
              <p className="mt-5 text-base font-medium text-readable-muted animate-pulse">{tr('gardenThinking')}</p>
            ) : (
              <p className="mt-5 text-base font-medium leading-relaxed text-[var(--color-text)]">
                {coachMessage || (locale === 'th' ? OBOLLA_COMPANION_TH : COMPANION_EN)}
              </p>
            )}
            <p className="mt-6 text-sm font-medium italic text-[var(--color-text-soft)]">{companionLine}</p>
            <button
              type="button"
              disabled={coaching}
              onClick={() => (mode === 'compose' ? void composeStory() : askCompanion(step, draft))}
              className="mt-5 w-full rounded-xl border-2 border-[var(--color-border)] bg-white/90 px-4 py-3 text-sm font-semibold text-[var(--color-text)] hover:bg-white disabled:opacity-50"
            >
              {tr('gardenAskAgain')}
            </button>
          </div>
        </aside>
      </div>

      {!composed && (coachMessage || coaching) && (
        <div className="garden-companion-dock lg:hidden">
          <p className="text-xs font-bold uppercase tracking-widest text-[var(--color-coffee)]">
            {tr('gardenCompanion')}
          </p>
          <p className="mt-2 text-sm font-medium leading-relaxed text-[var(--color-text)]">
            {coaching ? tr('gardenThinking') : coachMessage || companionLine}
          </p>
        </div>
      )}

      <p className="mt-6 hidden text-center text-sm font-medium text-readable-muted sm:mt-10 sm:block">
        <Link to="/community" className="font-semibold text-[var(--color-market-hover)] hover:underline">
          {tr('gardenBackCommunity')}
        </Link>
      </p>
    </div>
  )
}