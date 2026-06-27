import { useCallback, useEffect, useMemo, useState, type FormEvent } from 'react'
import { Link, useLocation, useParams } from 'react-router-dom'
import { api, ApiError } from '../api/client'
import { BuyerReviewPanel } from '../components/buyer/BuyerReviewPanel'
import { ExpertStepOutput } from '../components/ExpertStepOutput'
import { ScanStepOutput } from '../components/ScanStepOutput'
import { StatusBadge } from '../components/StatusBadge'
import { getExpertStepLabel } from '../config/expertSkillMeta'
import { useAuth } from '../context/AuthContext'
import { useLocale } from '../context/LocaleContext'
import { localizeScanWarning } from '../lib/scanStepDisplay'
import type { Agent, WorkflowResponse } from '../types'

type RoutingStep = { next_agent: string; reasoning: string }

export function Workflow() {
  const { tr, trf, locale } = useLocale()
  const { workflowId } = useParams<{ workflowId: string }>()
  const location = useLocation()

  const creatorTestSkillId = (location.state as { creatorTestSkillId?: string } | null)?.creatorTestSkillId
  const { token, user } = useAuth()
  const [workflow, setWorkflow] = useState<WorkflowResponse | null>(null)
  const [agents, setAgents] = useState<Agent[]>([])
  const [feedback, setFeedback] = useState('')
  const [loading, setLoading] = useState(true)
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState('')
  const [pinAgentId, setPinAgentId] = useState('')
  const [pinTitle, setPinTitle] = useState('')
  const [pinning, setPinning] = useState(false)
  const [pinMessage, setPinMessage] = useState('')
  const [pinError, setPinError] = useState('')
  const [canPublishCaseStudy, setCanPublishCaseStudy] = useState(false)
  const [caseStudyTitle, setCaseStudyTitle] = useState('')
  const [publishingCaseStudy, setPublishingCaseStudy] = useState(false)
  const [caseStudyMessage, setCaseStudyMessage] = useState('')
  const [caseStudyError, setCaseStudyError] = useState('')
  const [publishedShowcaseId, setPublishedShowcaseId] = useState<string | null>(null)

  // Extract links outside the boxes - user request
  const extractLinks = (text: string | null | undefined): string[] => {
    if (!text) return []
    const urls = new Set<string>()
    const regex = /(https?:\/\/[^\s<>"')]+)/g
    let match
    while ((match = regex.exec(text)) !== null) {
      const url = match[1].replace(/[.,;:!?]$/, '')
      if (url.length > 10) urls.add(url)
    }
    return Array.from(urls)
  }

  const allImportantLinks = useMemo(() => {
    if (!workflow) return []
    const links = new Set<string>()
    const scan = (str: string | undefined | null) => {
      extractLinks(str).forEach(l => links.add(l))
    }
    scan(workflow.final_output)
    scan(workflow.error_message)
    return Array.from(links).slice(0, 8)
  }, [workflow])

  function agentLabel(agentId: string): string {
    if (agentId === 'FINISH' || agentId === 'supervisor') return agentId
    const agent = agents.find((a) => a.id === agentId)
    if (!agent) return agentId.slice(0, 8) + '…'
    return `${agent.name} (${agent.llm_model})`
  }

  const refresh = useCallback(async () => {
    if (!token || !workflowId) return
    const data = await api.getWorkflow(token, workflowId)
    setWorkflow(data)
    return data
  }, [token, workflowId])

  useEffect(() => {
    if (!token || !workflowId) return
    let cancelled = false

    async function loadWorkflowWithRetry() {
      const maxAttempts = 30
      for (let attempt = 0; attempt < maxAttempts && !cancelled; attempt += 1) {
        try {
          const data = await api.getWorkflow(token!, workflowId!)
          if (cancelled) return
          setWorkflow(data)
          setLoading(false)
          return
        } catch (err) {
          const isStarting =
            err instanceof ApiError && err.status === 404 && attempt < maxAttempts - 1
          if (isStarting) {
            await new Promise((resolve) => setTimeout(resolve, 1500))
            continue
          }
          if (!cancelled) {
            setError(err instanceof Error ? err.message : 'Failed to load workflow')
            setLoading(false)
          }
          return
        }
      }
      if (!cancelled) {
        setError('Workflow is still starting. Refresh this page in a moment.')
        setLoading(false)
      }
    }

    void loadWorkflowWithRetry()
    api
      .listAgents(token)
      .then(setAgents)
      .catch(() => setAgents([]))

    return () => {
      cancelled = true
    }
  }, [token, workflowId])

  useEffect(() => {
    if (!workflow || workflow.status !== 'running') return
    const interval = setInterval(() => {
      refresh().catch(() => undefined)
    }, 3000)
    return () => clearInterval(interval)
  }, [workflow?.status, refresh])

  useEffect(() => {
    if (
      !token ||
      !workflowId ||
      !creatorTestSkillId ||
      !workflow ||
      (workflow.status !== 'completed' && workflow.status !== 'failed')
    ) {
      return
    }
    void api.finalizeCreatorTestRun(token, creatorTestSkillId, workflowId).catch(() => undefined)
  }, [token, workflowId, creatorTestSkillId, workflow?.status])

  useEffect(() => {
    if (!token || !user || !workflow || workflow.status !== 'completed' || !workflow.expert_skill_id) {
      setCanPublishCaseStudy(false)
      return
    }
    api
      .getExpertSkill(workflow.expert_skill_id)
      .then((skill) => setCanPublishCaseStudy(skill.owner_id === user.id))
      .catch(() => setCanPublishCaseStudy(false))
  }, [token, user, workflow?.status, workflow?.expert_skill_id])

  async function handleResume(e: FormEvent, approve = false) {
    e.preventDefault()
    if (!token || !workflowId) return
    setSubmitting(true)
    setError('')
    try {
      const result = await api.resumeWorkflow(
        token,
        workflowId,
        approve ? 'approve' : feedback,
      )
      setWorkflow(result)
      if (!approve) setFeedback('')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to resume workflow')
    } finally {
      setSubmitting(false)
    }
  }

  if (loading) {
    return <div className="mx-auto max-w-3xl px-4 py-16 text-[var(--color-muted)]">{tr('workflowLoading')}</div>
  }

  if (!workflow) {
    return (
      <div className="mx-auto max-w-3xl px-4 py-16">
        <p className="text-red-800 font-medium">{error || tr('workflowNotFound')}</p>
      </div>
    )
  }

  const intermediate = workflow.intermediate_results ?? {}
  const crew = (workflow.agents_used ?? intermediate.crew ?? []) as string[]
  const agentOutputs = (intermediate.agent_outputs ?? {}) as Record<string, string>
  const routingHistory = (intermediate.routing_history ?? []) as RoutingStep[]
  const hasMultiAgentDetails = crew.length > 0 && Object.keys(agentOutputs).length > 0
  const bridgeDevice = intermediate.bridge_device as
    | { id?: string; device_name?: string; capabilities?: string[] }
    | undefined
  const toolCalls = (intermediate.tool_calls ?? []) as Array<{
    tool: string
    input: Record<string, unknown>
    output: string
  }>
  const expertSteps = (intermediate.expert_skill_steps ?? {}) as Record<string, string>
  const expertPackSlug = (intermediate.pack_slug as string | undefined) ?? ''
  const expertWarnings = (intermediate.expert_skill_warnings ?? []) as string[]
  const scanBlocked = Boolean(intermediate.scan_blocked)
  const hydratedFromFinal = Boolean(intermediate.hydrated_from_final_output)
  const hasExpertSkillDetails = Object.keys(expertSteps).length > 0
  const deliveryQuality = (intermediate.delivery_quality as string | undefined) ?? workflow.billing?.delivery_quality
  const hasExpertWarnings = expertWarnings.length > 0
  const isCompletedWithWarnings =
    workflow.status === 'completed' && Boolean(workflow.error_message) && hasExpertSkillDetails
  const workflowAgentIds = [
    ...(workflow.agent_id ? [workflow.agent_id] : []),
    ...crew,
  ].filter((id, index, all) => all.indexOf(id) === index)
  const myOwnedAgentsInWorkflow = agents.filter(
    (agent) => agent.owner_id === user?.id && workflowAgentIds.includes(agent.id),
  )
  const canPinToPortfolio =
    workflow.status === 'completed' && Boolean(token) && myOwnedAgentsInWorkflow.length > 0
  const isExpertSkillRun =
    workflow.workflow_type === 'expert_skill' ||
    Boolean(workflow.expert_skill_id) ||
    hasExpertSkillDetails
  const showBuyerReview =
    workflow.status === 'completed' && Boolean(token) && isExpertSkillRun
  const localizedWarnings = expertWarnings.map((warning) => localizeScanWarning(locale, warning))
  const showScanBlockedBanner =
    scanBlocked && !localizedWarnings.some((w) => w.includes('401') || w.includes('403'))

  async function handlePublishCaseStudy(e: FormEvent) {
    e.preventDefault()
    if (!token || !workflowId) return
    setPublishingCaseStudy(true)
    setCaseStudyError('')
    setCaseStudyMessage('')
    try {
      const showcase = await api.createShowcaseFromWorkflow(token, {
        workflow_id: workflowId,
        title: caseStudyTitle.trim() || undefined,
      })
      setPublishedShowcaseId(showcase.id)
      setCaseStudyMessage('Case study published — buyers can see this verified run.')
    } catch (err) {
      setCaseStudyError(err instanceof Error ? err.message : 'Failed to publish case study')
    } finally {
      setPublishingCaseStudy(false)
    }
  }

  async function handlePinPortfolio(e: FormEvent) {
    e.preventDefault()
    if (!token || !workflowId || !pinAgentId) return
    setPinning(true)
    setPinError('')
    setPinMessage('')
    try {
      await api.addPortfolioItem(token, pinAgentId, {
        workflow_id: workflowId,
        title: pinTitle.trim() || undefined,
      })
      setPinMessage('Added to agent portfolio. View it on the agent profile page.')
      setPinTitle('')
    } catch (err) {
      setPinError(err instanceof Error ? err.message : 'Failed to add to portfolio')
    } finally {
      setPinning(false)
    }
  }

  return (
    <div className="page-shell mx-auto max-w-3xl">
      <Link to="/dashboard" className="text-sm font-medium text-readable-muted hover:text-[var(--color-text)]">
        {tr('workflowBack')}
      </Link>

      <div className="mt-6 flex items-center gap-3">
        <h1 className="text-2xl font-bold text-[var(--color-text)]">{tr('workflowTitle')}</h1>
        <StatusBadge status={workflow.status} />
      </div>
      <p className="mt-1 font-mono text-xs text-[var(--color-muted)]">{workflow.workflow_id}</p>

      <div className="mt-6 grid gap-4 sm:grid-cols-3">
        <div className="rounded-xl border border-[var(--color-border)] bg-[var(--color-surface-raised)] p-4">
          <p className="text-xs font-semibold text-[var(--color-text-soft)]">{tr('workflowTokens')}</p>
          <p className="mt-1 font-mono text-lg font-semibold text-[var(--color-text)]">{workflow.total_tokens}</p>
        </div>
        <div className="rounded-xl border border-[var(--color-border)] bg-[var(--color-surface-raised)] p-4">
          <p className="text-xs font-semibold text-[var(--color-text-soft)]">{tr('workflowCost')}</p>
          <p className="mt-1 font-mono text-lg font-semibold text-[var(--color-market-hover)]">
            ${workflow.total_cost_usd.toFixed(6)}
          </p>
        </div>
        <div className="rounded-xl border border-[var(--color-border)] bg-[var(--color-surface-raised)] p-4">
          <p className="text-xs font-semibold text-[var(--color-text-soft)]">{tr('workflowDuration')}</p>
          <p className="mt-1 font-mono text-lg font-semibold text-[var(--color-text)]">
            {workflow.execution_time_seconds != null
              ? `${workflow.execution_time_seconds.toFixed(1)}s`
              : '—'}
          </p>
        </div>
      </div>

      {/* Observability + Attribution - to make people dare to use and monetize */}
      <div className="mt-6 rounded-2xl border border-emerald-500/30 bg-emerald-500/5 p-5">
        <h3 className="font-semibold text-emerald-400">Observability & Attribution</h3>
        <div className="mt-2 grid grid-cols-1 sm:grid-cols-3 gap-4 text-sm">
          <div>
            <div className="text-xs text-[var(--color-muted)]">Total Cost</div>
            <div className="font-mono">${workflow.total_cost_usd.toFixed(4)}</div>
          </div>
          <div>
            <div className="text-xs text-[var(--color-muted)]">Attributed to Creator</div>
            <div className="font-mono">${(workflow.total_cost_usd * 0.8).toFixed(4)} (80%)</div>
          </div>
          <div>
            <div className="text-xs text-[var(--color-muted)]">Platform Fee</div>
            <div className="font-mono">${(workflow.total_cost_usd * 0.2).toFixed(4)}</div>
          </div>
        </div>
        <p className="mt-2 text-xs text-[var(--color-muted)]">Trace: {workflow.workflow_id} • Full logs available to creator for trust.</p>
      </div>

      {/* Prominent Quick Links - OUTSIDE the boxes, easy to find */}
      {allImportantLinks.length > 0 && (
        <div className="mt-6 rounded-2xl border-2 border-[var(--color-market)]/60 bg-white p-5 shadow-sm">
          <div className="flex items-center gap-2 mb-3">
            <span className="text-lg">🔗</span>
            <h3 className="font-semibold text-[var(--color-text)]">{locale === 'th' ? 'ลิงก์สำคัญ (กดได้เลย)' : 'Quick Links (Click to open)'}</h3>
          </div>
          <div className="flex flex-wrap gap-2">
            {allImportantLinks.map((link, idx) => {
              const short = link.length > 55 ? link.slice(0, 52) + '…' : link
              return (
                <a 
                  key={idx} 
                  href={link} 
                  target="_blank" 
                  rel="noreferrer"
                  className="inline-flex items-center gap-1.5 rounded-xl border border-[var(--color-border)] bg-white px-4 py-2 text-sm font-medium text-[var(--color-market-hover)] hover:bg-[var(--color-surface-overlay)] hover:border-[var(--color-market)] transition-colors"
                >
                  {short} ↗
                </a>
              )
            })}
          </div>
          <p className="mt-2 text-xs text-readable-muted">{locale === 'th' ? 'ลิงก์เหล่านี้ถูกดึงออกมาจากผลลัพธ์เพื่อให้หาง่าย ไม่ต้องเลื่อนในกล่องข้อความ' : 'These links were extracted from the run results and placed here for easy access.'}</p>
        </div>
      )}

      {workflow.error_message && workflow.status === 'failed' && (
        <p className="mt-4 rounded-lg border border-red-500/30 bg-red-500/10 px-4 py-3 text-sm text-red-400">
          {workflow.error_message}
        </p>
      )}

      {(hasExpertWarnings || isCompletedWithWarnings || scanBlocked) && (
        <div className="mt-4 rounded-lg border border-amber-600/35 bg-amber-50 px-4 py-3 text-sm text-[var(--color-text)]">
          <p className="font-semibold text-amber-900">
            {workflow.status === 'failed' ? tr('workflowIssuesRun') : tr('workflowCompletedWarnings')}
          </p>
          {showScanBlockedBanner && <p className="mt-2 font-medium">{tr('workflowScanBlocked')}</p>}
          {hasExpertWarnings ? (
            <ul className="mt-2 list-disc space-y-1 pl-5 font-medium">
              {localizedWarnings.map((warning) => (
                <li key={warning}>{warning}</li>
              ))}
            </ul>
          ) : (
            workflow.error_message && <p className="mt-2">{workflow.error_message}</p>
          )}
        </div>
      )}

      {bridgeDevice?.device_name && (
        <div className="mt-4 rounded-lg border border-violet-200 bg-violet-50/90 px-4 py-3 text-sm font-medium text-[var(--color-text)]">
          {tr('workflowLocalBridge')}: <span className="font-semibold text-violet-950">{bridgeDevice.device_name}</span>
          {bridgeDevice.capabilities && bridgeDevice.capabilities.length > 0 && (
            <span className="ml-2 text-xs font-medium text-[var(--color-text-soft)]">
              ({bridgeDevice.capabilities.join(', ')})
            </span>
          )}
        </div>
      )}

      {toolCalls.length > 0 && (
        <div className="mt-6 rounded-xl border border-[var(--color-border)] bg-[var(--color-surface-raised)] p-5">
          <h2 className="text-sm font-medium text-[var(--color-muted)] uppercase tracking-wide">
            Tool activity
          </h2>
          <div className="mt-4 space-y-3">
            {toolCalls.map((call, index) => (
              <div
                key={`${call.tool}-${index}`}
                className="rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)] p-4"
              >
                <p className="font-mono text-sm text-cyan-400">{call.tool}</p>
                <pre className="mt-2 max-h-40 overflow-auto text-xs text-[var(--color-muted)]">
                  {JSON.stringify(call.input, null, 2)}
                </pre>
                <pre className="workflow-output-block mt-2 max-h-48 overflow-auto text-xs">
                  {call.output}
                </pre>
              </div>
            ))}
          </div>
        </div>
      )}

      {workflow.human_prompt && workflow.status === 'waiting_human' && (
        <div className="mt-6 rounded-xl border border-amber-500/30 bg-amber-500/5 p-5">
          <h2 className="font-semibold text-amber-400">Human review required</h2>
          <p className="mt-2 text-sm text-[var(--color-text-soft)]">{workflow.human_prompt}</p>
        </div>
      )}

      {hasExpertSkillDetails && (
        <div className="mt-6 rounded-xl border border-violet-600/25 bg-violet-50/80 p-5">
          <h2 className="text-sm font-bold uppercase tracking-wide text-violet-900">{tr('workflowExpertPipeline')}</h2>
          {hydratedFromFinal && (
            <p className="mt-1 text-xs font-medium text-[var(--color-text-soft)]">{tr('workflowHydratedNote')}</p>
          )}
          <div className="mt-4 space-y-4">
            {Object.entries(expertSteps).map(([step, output], index) => (
              <div
                key={step}
                className="rounded-lg border border-[var(--color-border)] bg-white p-4 shadow-sm"
              >
                <div className="flex items-center gap-2">
                  <span className="flex h-6 w-6 items-center justify-center rounded-full bg-violet-600/15 text-xs font-bold text-violet-900">
                    {index + 1}
                  </span>
                  <h3 className="text-sm font-bold text-[var(--color-text)]">
                    {getExpertStepLabel(expertPackSlug, step)}
                  </h3>
                </div>
                {step === 'scan' && scanBlocked ? (
                  <ScanStepOutput output={output} />
                ) : (
                  <ExpertStepOutput output={output} />
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {hasMultiAgentDetails && (
        <div className="mt-6 space-y-4">
          <div className="rounded-xl border border-[var(--color-border)] bg-[var(--color-surface-raised)] p-5">
            <h2 className="text-sm font-medium text-[var(--color-muted)] uppercase tracking-wide">Crew</h2>
            <p className="mt-2 text-sm text-cyan-400">
              {crew.map((id) => agentLabel(id)).join(' → ')}
            </p>
          </div>

          <div className="rounded-xl border border-[var(--color-border)] bg-[var(--color-surface-raised)] p-5">
            <h2 className="text-sm font-medium text-[var(--color-muted)] uppercase tracking-wide">
              Agent contributions
            </h2>
            <p className="mt-1 text-xs text-[var(--color-muted)]">
              Each section shows what that agent produced during the run.
            </p>
            <div className="mt-4 space-y-4">
              {crew
                .filter((id) => agentOutputs[id])
                .map((id, index) => (
                  <div
                    key={id}
                    className="rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)] p-4"
                  >
                    <div className="flex items-center gap-2">
                      <span className="flex h-6 w-6 items-center justify-center rounded-full bg-cyan-500/20 text-xs font-semibold text-cyan-400">
                        {index + 1}
                      </span>
                      <h3 className="text-sm font-semibold text-[var(--color-text)]">{agentLabel(id)}</h3>
                    </div>
                    <pre className="workflow-output-block mt-3">{agentOutputs[id]}</pre>
                  </div>
                ))}
              {Object.entries(agentOutputs)
                .filter(([id]) => !crew.includes(id))
                .map(([id, output]) => (
                  <div
                    key={id}
                    className="rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)] p-4"
                  >
                    <h3 className="text-sm font-semibold text-[var(--color-text)]">{agentLabel(id)}</h3>
                    <pre className="workflow-output-block mt-3">{output}</pre>
                  </div>
                ))}
            </div>
          </div>

          {routingHistory.length > 0 && (
            <details className="rounded-xl border border-[var(--color-border)] bg-[var(--color-surface-raised)] p-5">
              <summary className="cursor-pointer text-sm font-medium text-[var(--color-muted)] uppercase tracking-wide">
                Supervisor routing ({routingHistory.length} steps)
              </summary>
              <ol className="mt-4 space-y-2 text-sm">
                {routingHistory.map((step, index) => (
                  <li key={index} className="rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)] px-3 py-2">
                    <span className="font-medium text-cyan-400">{agentLabel(step.next_agent)}</span>
                    {step.reasoning && (
                      <span className="text-[var(--color-muted)]"> — {step.reasoning}</span>
                    )}
                  </li>
                ))}
              </ol>
            </details>
          )}
        </div>
      )}

      {workflow.final_output && (
        <div className="mt-6 rounded-xl border border-[var(--color-border)] bg-[var(--color-surface-raised)] p-5">
          <h2 className="text-sm font-medium text-[var(--color-muted)] uppercase tracking-wide">
            {hasExpertSkillDetails || hasMultiAgentDetails ? tr('workflowFinalSummary') : tr('workflowFinalOutput')}
          </h2>
          <div className="workflow-output-block mt-3">
            <ExpertStepOutput output={workflow.final_output} />
          </div>
        </div>
      )}

      {/* Summary at the END - Easy to find without scrolling inside text boxes */}
      {(workflow.final_output || allImportantLinks.length > 0) && (
        <div className="mt-8 rounded-3xl border border-[var(--color-sage)]/70 bg-gradient-to-br from-[var(--color-surface-overlay)] to-white p-6">
          <h2 className="text-lg font-semibold text-[var(--color-text)] mb-2 flex items-center gap-2">
            {locale === 'th' ? '📋 สรุปผลลัพธ์ (หาง่าย)' : '📋 Results Summary (Easy Access)'}
          </h2>
          <p className="text-sm text-readable-muted mb-4">
            {locale === 'th' 
              ? 'สรุปสำคัญจาก agent flow นี้ วางไว้ด้านนอกกล่องเพื่อให้ไม่ต้องเลื่อนหา' 
              : 'Key takeaways and links from this agent flow are summarized here outside the boxes.'}
          </p>

          {workflow.final_output && (
            <div className="bg-white border rounded-2xl p-4 mb-4 text-sm">
              <div className="font-medium mb-1 text-[var(--color-text-soft)]">Final Output Summary</div>
              <div className="line-clamp-4 text-readable-muted">
                {workflow.final_output.slice(0, 450)}{workflow.final_output.length > 450 ? '…' : ''}
              </div>
            </div>
          )}

          {allImportantLinks.length > 0 && (
            <div>
              <div className="font-medium text-sm mb-2 text-[var(--color-text-soft)]">Important Links</div>
              <div className="flex flex-wrap gap-2">
                {allImportantLinks.slice(0, 5).map((link, i) => (
                  <a key={i} href={link} target="_blank" rel="noreferrer" className="text-xs bg-white border px-3 py-1.5 rounded-xl hover:bg-emerald-50 text-emerald-700 font-medium">
                    {link.length > 40 ? link.slice(0,37)+'…' : link}
                  </a>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {canPublishCaseStudy && workflow.status === 'completed' && (
        <div className="mt-6 rounded-xl border border-emerald-500/30 bg-emerald-500/5 p-5">
          <h2 className="font-semibold text-emerald-400">Publish verified case study</h2>
          <p className="mt-1 text-sm text-[var(--color-muted)]">
            Turn this completed run into a public showcase — linked to workflow{' '}
            <span className="font-mono text-xs">{workflow.workflow_id.slice(0, 8)}…</span> for trust.
          </p>
          {publishedShowcaseId ? (
            <p className="mt-3 text-sm text-emerald-700">
              {caseStudyMessage}{' '}
              <Link to={`/showcases/${publishedShowcaseId}`} className="underline hover:text-emerald-200">
                View case study →
              </Link>
            </p>
          ) : (
            <form onSubmit={handlePublishCaseStudy} className="mt-4 space-y-3">
              <input
                value={caseStudyTitle}
                onChange={(e) => setCaseStudyTitle(e.target.value)}
                placeholder="Case study title (optional)"
                className="w-full rounded-lg border border-[var(--color-border)] bg-white px-3 py-2 text-sm text-[var(--color-text)] focus:border-emerald-500/50 focus:outline-none"
              />
              {caseStudyError && <p className="text-sm text-red-400">{caseStudyError}</p>}
              <button
                type="submit"
                disabled={publishingCaseStudy}
                className="rounded-lg bg-emerald-500 px-4 py-2 text-sm font-bold text-slate-900 hover:bg-emerald-400 disabled:opacity-50"
              >
                {publishingCaseStudy ? 'Publishing…' : 'Publish case study'}
              </button>
            </form>
          )}
        </div>
      )}

      {canPinToPortfolio && (
        <div className="mt-6 rounded-xl border border-cyan-500/30 bg-cyan-500/5 p-5">
          <h2 className="font-semibold text-cyan-400">Add to agent portfolio</h2>
          <p className="mt-1 text-sm text-[var(--color-muted)]">
            Showcase this completed run on your agent profile before others hire you.
          </p>
          <form onSubmit={handlePinPortfolio} className="mt-4 space-y-3">
            <div className="grid gap-3 sm:grid-cols-2">
              <div>
                <label className="mb-1 block text-xs text-[var(--color-muted)]">Agent</label>
                <select
                  required
                  value={pinAgentId || myOwnedAgentsInWorkflow[0]?.id || ''}
                  onChange={(e) => setPinAgentId(e.target.value)}
                  className="w-full rounded-lg border border-[var(--color-border)] bg-white px-3 py-2 text-sm text-[var(--color-text)] focus:border-cyan-500/50 focus:outline-none"
                >
                  {myOwnedAgentsInWorkflow.map((agent) => (
                    <option key={agent.id} value={agent.id}>
                      {agent.name}
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <label className="mb-1 block text-xs text-[var(--color-muted)]">Title (optional)</label>
                <input
                  value={pinTitle}
                  onChange={(e) => setPinTitle(e.target.value)}
                  placeholder="e.g. SEO audit for successcasting.com"
                  className="w-full rounded-lg border border-[var(--color-border)] bg-white px-3 py-2 text-sm text-[var(--color-text)] focus:border-cyan-500/50 focus:outline-none"
                />
              </div>
            </div>
            {pinError && <p className="text-sm text-red-400">{pinError}</p>}
            {pinMessage && <p className="text-sm text-emerald-400">{pinMessage}</p>}
            <button
              type="submit"
              disabled={pinning}
              className="rounded-lg border border-cyan-500/40 px-4 py-2 text-sm text-cyan-400 hover:bg-cyan-500/10 disabled:opacity-50"
            >
              {pinning ? 'Saving…' : 'Add to portfolio'}
            </button>
          </form>
        </div>
      )}

      {workflow.status === 'waiting_human' && (
        <div className="mt-6 rounded-xl border border-[var(--color-border)] bg-[var(--color-surface-raised)] p-5">
          <h2 className="font-semibold text-[var(--color-text)]">Your feedback</h2>
          <form onSubmit={(e) => handleResume(e, false)} className="mt-4 space-y-3">
            <textarea
              rows={3}
              value={feedback}
              onChange={(e) => setFeedback(e.target.value)}
              placeholder="Request changes, or click Approve below"
              className="w-full rounded-lg border border-[var(--color-border)] bg-white px-3 py-2 text-sm text-[var(--color-text)] focus:border-cyan-500/50 focus:outline-none resize-y"
            />
            {error && <p className="text-sm text-red-400">{error}</p>}
            <div className="flex gap-3">
              <button
                type="submit"
                disabled={submitting || !feedback.trim()}
                className="rounded-lg border border-[var(--color-border)] px-4 py-2 text-sm text-[var(--color-text-soft)] hover:border-cyan-500/50 disabled:opacity-50"
              >
                Send revision
              </button>
              <button
                type="button"
                disabled={submitting}
                onClick={(e) => handleResume(e, true)}
                className="rounded-lg bg-emerald-500 px-4 py-2 text-sm font-medium text-slate-900 hover:bg-emerald-400 disabled:opacity-50"
              >
                Approve
              </button>
            </div>
          </form>
        </div>
      )}

      {workflow.billing?.charged && (
        <div className="mt-6 rounded-xl border border-emerald-500/30 bg-emerald-500/5 p-5">
          <h2 className="font-semibold text-emerald-400">Billing</h2>
          {(workflow.billing.platform_notice || workflow.billing.platform_tested) && (
            <p className="mt-2 rounded-lg border border-violet-500/30 bg-violet-500/10 px-3 py-2 text-sm text-violet-950">
              {workflow.billing.platform_notice ??
                'ทดสอบโดยทีมแพลตฟอร์ม OBOLLA (Platform tested) — เจ้าของ agent ไม่ได้รับเงินจริง'}
            </p>
          )}
          {(workflow.billing.trial_notice ||
            (workflow.billing.trial_amount_usd != null &&
              Number(workflow.billing.trial_amount_usd) > 0 &&
              !workflow.billing.platform_tested)) && (
            <p className="mt-2 rounded-lg border border-amber-500/30 bg-amber-500/10 px-3 py-2 text-sm text-amber-950">
              {workflow.billing.trial_notice ??
                'การทดลองใช้ — เจ้าของ agent ไม่ได้รับเงินจริง'}
              {workflow.billing.trial_amount_usd != null &&
                Number(workflow.billing.trial_amount_usd) > 0 && (
                  <span className="mt-1 block font-mono text-xs text-amber-900/80">
                    Trial portion: ${Number(workflow.billing.trial_amount_usd).toFixed(4)}
                    {workflow.billing.paid_amount_usd != null &&
                      Number(workflow.billing.paid_amount_usd) > 0 &&
                      ` · Paid portion: $${Number(workflow.billing.paid_amount_usd).toFixed(4)}`}
                  </span>
                )}
            </p>
          )}
          {(deliveryQuality === 'degraded' || deliveryQuality === 'failed') && (
            <p className="mt-2 text-sm font-medium text-amber-950">
              {deliveryQuality === 'failed'
                ? workflow.billing.marketplace_waived_usd != null
                  ? 'Marketplace fee waived — expert skill deliverables could not be produced. Only LLM usage was charged.'
                  : 'Deliverables could not be produced (LLM providers unavailable). This run was billed before partial-delivery pricing.'
                : workflow.billing.marketplace_fee_multiplier != null
                  ? `Partial delivery (${Math.round(workflow.billing.marketplace_fee_multiplier * 100)}% marketplace fee).`
                  : 'Partial delivery — some pipeline steps failed. This run was billed before partial-delivery pricing.'}
              {workflow.billing.marketplace_waived_usd != null &&
                Number(workflow.billing.marketplace_waived_usd) > 0 && (
                  <span className="block mt-1 font-mono text-xs text-amber-300/80">
                    Waived: ${Number(workflow.billing.marketplace_waived_usd).toFixed(4)}
                  </span>
                )}
            </p>
          )}
          <dl className="mt-3 grid gap-2 text-sm sm:grid-cols-3">
            <div>
              <dt className="text-[var(--color-muted)]">Agent fees</dt>
              <dd className="font-mono font-semibold text-[var(--color-text)]">${Number(workflow.billing.marketplace_cost_usd).toFixed(4)}</dd>
            </div>
            <div>
              <dt className="text-[var(--color-muted)]">LLM cost</dt>
              <dd className="font-mono font-semibold text-[var(--color-text)]">${Number(workflow.billing.llm_cost_usd).toFixed(6)}</dd>
            </div>
            <div>
              <dt className="text-[var(--color-muted)]">Total charged</dt>
              <dd className="font-mono text-emerald-400">${Number(workflow.billing.total_charged_usd).toFixed(4)}</dd>
            </div>
          </dl>
          {workflow.billing.balance_after_usd != null && (
            <p className="mt-2 text-xs text-[var(--color-muted)]">
              Balance after: ${Number(workflow.billing.balance_after_usd).toFixed(2)}
            </p>
          )}
          {workflow.billing.creator_payouts && workflow.billing.creator_payouts.length > 0 && (
            <div className="mt-4 border-t border-emerald-500/20 pt-3">
              <p className="text-xs font-medium text-[var(--color-muted)]">Creator payouts</p>
              <ul className="mt-2 space-y-1 text-xs">
                {workflow.billing.creator_payouts.map((payout) => (
                  <li key={payout.id} className="flex justify-between text-[var(--color-muted)]">
                    <span>Agent {payout.agent_id.slice(0, 8)}…</span>
                    <span className="font-mono text-emerald-400">
                      +${Number(payout.net_amount_usd).toFixed(4)}
                    </span>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}

      {workflow.status === 'waiting_human' && !workflow.billing?.charged && (
        <p className="mt-6 text-sm text-amber-400/80">
          Billing pending — charges apply when the workflow completes.
        </p>
      )}

      {workflow.status === 'running' && (
        <p className="mt-6 text-sm text-[var(--color-muted)] animate-pulse">
          {tr('workflowRunningAudit')}{' '}
          {hasExpertSkillDetails
            ? trf('workflowRunningSteps', { count: String(Object.keys(expertSteps).length) })
            : tr('workflowRunningRefresh')}
        </p>
      )}

      {showBuyerReview && workflowId && token && (
        <BuyerReviewPanel token={token} workflowId={workflowId} />
      )}
    </div>
  )
}