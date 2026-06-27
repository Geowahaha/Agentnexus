import { useEffect, useRef, useState, type FormEvent } from 'react'
import { Link, useLocation, useNavigate, useParams } from 'react-router-dom'
import { api } from '../api/client'
import { LocalBridgeSelector } from '../components/LocalBridgeSelector'
import { useLocalBridge } from '../hooks/useLocalBridge'
import { LLM_PROVIDERS, resolveProvider } from '../lib/llmProviders'
import { useAuth } from '../context/AuthContext'
import type { Agent, AgentProfile, CostEstimate } from '../types'

const ONE_RUN_BOX = [
  { icon: '💬', title: 'Your task', desc: 'Tell the agent what you need in plain language' },
  { icon: '🤖', title: 'AI output', desc: 'Get a focused response from one specialist model' },
  { icon: '✅', title: 'Optional review', desc: 'Approve or request changes before it finishes' },
]

export function AgentDetail() {
  const { id } = useParams<{ id: string }>()
  const { token, user } = useAuth()
  const location = useLocation()
  const navigate = useNavigate()
  const runSectionRef = useRef<HTMLDivElement>(null)
  const [agent, setAgent] = useState<Agent | null>(null)
  const [profile, setProfile] = useState<AgentProfile | null>(null)
  const [task, setTask] = useState('')
  const [humanReview, setHumanReview] = useState(false)
  const [loading, setLoading] = useState(true)
  const [running, setRunning] = useState(false)
  const [error, setError] = useState('')
  const [estimate, setEstimate] = useState<CostEstimate | null>(null)
  const [portfolioError, setPortfolioError] = useState('')
  const {
    devices: bridgeDevices,
    enabled: bridgeEnabled,
    setEnabled: setBridgeEnabled,
    deviceId: bridgeDeviceId,
    setDeviceId: setBridgeDeviceId,
    bridgeDeviceId: selectedBridgeDeviceId,
  } = useLocalBridge(token)

  useEffect(() => {
    if (!id) return
    api
      .getAgent(id)
      .then(setAgent)
      .catch((err) => setError(err instanceof Error ? err.message : 'Agent not found'))
      .finally(() => setLoading(false))
  }, [id])

  useEffect(() => {
    if (!id || !agent) return
    const includePrivate = Boolean(user && agent.owner_id === user.id)
    api
      .getAgentProfile(id, token, includePrivate)
      .then(setProfile)
      .catch(() => setProfile(null))
  }, [id, token, agent, user?.id])

  const isOwner = Boolean(user && agent && agent.owner_id === user.id)

  function loadProfile(agentId: string) {
    const includePrivate = Boolean(user && agent && agent.owner_id === user.id)
    return api
      .getAgentProfile(agentId, token, includePrivate)
      .then(setProfile)
      .catch(() => setProfile(null))
  }

  useEffect(() => {
    if (!token || !id) return
    api
      .estimateCost(token, { workflow_type: 'single_agent', agent_id: id })
      .then(setEstimate)
      .catch(() => setEstimate(null))
  }, [token, id])

  function scrollToRun() {
    runSectionRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' })
  }

  async function handleRun(e: FormEvent) {
    e.preventDefault()
    if (!token || !agent) return
    setRunning(true)
    setError('')
    try {
      const result = await api.runWorkflow(token, {
        task_description: task,
        workflow_type: 'single_agent',
        agent_id: agent.id,
        require_human_approval: humanReview,
        bridge_device_id: selectedBridgeDeviceId,
      })
      navigate(`/workflows/${result.workflow_id}`)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to run workflow')
    } finally {
      setRunning(false)
    }
  }

  async function handleRemovePortfolio(itemId: string) {
    if (!token || !agent || !confirm('Remove this work sample from the portfolio?')) return
    setPortfolioError('')
    try {
      await api.deletePortfolioItem(token, agent.id, itemId)
      await loadProfile(agent.id)
    } catch (err) {
      setPortfolioError(err instanceof Error ? err.message : 'Failed to remove portfolio item')
    }
  }

  if (loading) {
    return <div className="mx-auto max-w-4xl px-4 py-16 text-[var(--color-muted)]">Loading agent…</div>
  }

  if (!agent) {
    return (
      <div className="mx-auto max-w-4xl px-4 py-16">
        <p className="text-red-400">{error || 'Agent not found'}</p>
        <Link to="/?tab=agents" className="mt-4 inline-block text-cyan-400 hover:text-cyan-300">
          Back to Raw Agents
        </Link>
      </div>
    )
  }

  const price = Number(agent.price_usd_per_run)
  const estLlm = estimate ? Number(estimate.estimated_llm_cost_usd) : 0.03
  const estTotal = price + estLlm
  const balance = estimate ? Number(estimate.current_balance_usd) : null
  const canAfford = estimate?.sufficient_balance ?? true
  const stats = profile?.stats
  const portfolio = profile?.portfolio ?? []
  const provider = resolveProvider(agent.llm_model)
  const providerLabel = LLM_PROVIDERS[provider].label

  return (
    <div className="mx-auto max-w-4xl px-4 py-10 sm:px-6">
      <Link to="/?tab=agents" className="text-sm text-[var(--color-muted)] hover:text-cyan-400">
        ← Raw Agents
      </Link>

      {/* Product header */}
      <div className="mt-6 rounded-2xl border border-cyan-500/30 bg-cyan-500/5 p-6 sm:p-8">
        <div className="flex flex-col gap-6 lg:flex-row lg:items-start lg:justify-between">
          <div className="flex-1">
            <span className="rounded-full bg-cyan-500/20 px-2.5 py-0.5 text-xs font-semibold text-cyan-300">
              Raw Agent
            </span>
            <h1 className="mt-2 text-2xl sm:text-3xl font-bold text-[var(--color-text)]">{agent.name}</h1>
            <p className="mt-1 text-sm text-cyan-200/80">{agent.role}</p>
            <p className="mt-3 text-[var(--color-muted)] leading-relaxed max-w-2xl">{agent.description}</p>
            <div className="mt-4 flex flex-wrap gap-2 text-xs">
              {agent.category && (
                <span className="rounded-full bg-cyan-500/10 px-2.5 py-1 text-cyan-400 capitalize">
                  {agent.category}
                </span>
              )}
              {agent.owner_name && (
                <span className="rounded-full bg-emerald-50 px-2.5 py-1 text-[var(--color-muted)]">
                  By {agent.owner_name}
                </span>
              )}
              {stats && stats.total_hires > 0 && (
                <span className="rounded-full bg-emerald-500/10 px-2.5 py-1 text-emerald-400">
                  Hired {stats.total_hires}×
                </span>
              )}
            </div>
          </div>

          <div className="shrink-0 rounded-xl border border-cyan-500/30 bg-[var(--color-surface)] p-5 min-w-[200px]">
            <p className="text-xs text-[var(--color-muted)] uppercase tracking-wide">Price per run</p>
            <p className="mt-1 text-3xl font-bold text-cyan-400">${price.toFixed(2)}</p>
            <p className="text-xs text-[var(--color-muted)]">+ ~${estLlm.toFixed(2)} AI usage</p>
            <p className="mt-2 font-mono text-sm text-cyan-300">≈ ${estTotal.toFixed(2)} total</p>
            {user ? (
              <button
                type="button"
                onClick={scrollToRun}
                className="mt-4 w-full rounded-lg bg-cyan-500 px-4 py-2.5 text-sm font-bold text-slate-900 hover:bg-cyan-400"
              >
                Hire This Agent
              </button>
            ) : (
              <Link
                to="/register"
                state={{ from: location }}
                className="mt-4 block w-full rounded-lg bg-cyan-500 px-4 py-2.5 text-center text-sm font-bold text-slate-900 hover:bg-cyan-400"
              >
                Hire This Agent
              </Link>
            )}
          </div>
        </div>
      </div>

      {/* What 1 run includes */}
      <div className="mt-6 rounded-2xl border border-[var(--color-border)] bg-[var(--color-surface-raised)] p-6">
        <h2 className="text-sm font-semibold uppercase tracking-wide text-[var(--color-muted)]">
          1 run = all of this
        </h2>
        <div className="mt-4 grid gap-3 sm:grid-cols-3">
          {ONE_RUN_BOX.map((item) => (
            <div
              key={item.title}
              className="rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] p-4"
            >
              <span className="text-xl">{item.icon}</span>
              <p className="mt-2 font-medium text-[var(--color-text)]">{item.title}</p>
              <p className="mt-1 text-sm text-[var(--color-muted)]">{item.desc}</p>
            </div>
          ))}
        </div>
      </div>

      <div className="mt-6 grid gap-6 lg:grid-cols-2">
        {/* Model & tools */}
        <div className="rounded-2xl border border-[var(--color-border)] bg-[var(--color-surface-raised)] p-6">
          <h2 className="text-sm font-semibold uppercase tracking-wide text-[var(--color-muted)]">
            AI model & tools
          </h2>
          <div className="mt-4 space-y-3">
            <div className="rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)] px-4 py-3">
              <p className="text-xs text-[var(--color-muted)]">Provider</p>
              <p className="mt-1 font-medium text-[var(--color-text)]">{providerLabel}</p>
              <p className="mt-0.5 font-mono text-xs text-[var(--color-muted)]">{agent.llm_model}</p>
            </div>
            <div className="rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)] px-4 py-3">
              <p className="text-xs text-[var(--color-muted)]">Tools</p>
              {agent.tools.length > 0 ? (
                <ul className="mt-2 space-y-1">
                  {agent.tools.map((tool) => (
                    <li key={tool} className="text-sm text-[var(--color-text-soft)] font-mono">
                      {tool}
                    </li>
                  ))}
                </ul>
              ) : (
                <p className="mt-1 text-sm text-[var(--color-muted)]">No extra tools — LLM only</p>
              )}
            </div>
          </div>
        </div>

        {/* Capabilities */}
        <div className="rounded-2xl border border-[var(--color-border)] bg-[var(--color-surface-raised)] p-6">
          <h2 className="text-sm font-semibold uppercase tracking-wide text-[var(--color-muted)]">Capabilities</h2>
          <div className="mt-4 flex flex-wrap gap-2">
            {agent.capabilities.length > 0 ? (
              agent.capabilities.map((cap) => (
                <span key={cap} className="rounded-lg bg-emerald-50 px-3 py-1.5 text-sm text-[var(--color-text-soft)]">
                  {cap}
                </span>
              ))
            ) : (
              <p className="text-sm text-[var(--color-muted)]">General-purpose agent</p>
            )}
          </div>
          {stats && (
            <div className="mt-5 flex gap-3">
              <div className="rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)] px-3 py-2">
                <p className="text-[10px] uppercase text-[var(--color-muted)]">Portfolio</p>
                <p className="font-mono text-sm text-white">{stats.portfolio_count}</p>
              </div>
              <div className="rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)] px-3 py-2">
                <p className="text-[10px] uppercase text-[var(--color-muted)]">Times hired</p>
                <p className="font-mono text-sm text-white">{stats.total_hires}</p>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Portfolio */}
      <div className="mt-6 rounded-2xl border border-[var(--color-border)] bg-[var(--color-surface-raised)] p-6 sm:p-8">
        <h2 className="text-lg font-semibold text-[var(--color-text)]">Work samples</h2>
        <p className="mt-1 text-sm text-[var(--color-muted)]">
          See what this agent produced before you hire them.
        </p>
        {portfolioError && (
          <p className="mt-3 rounded-lg border border-red-500/30 bg-red-500/10 px-3 py-2 text-sm text-red-400">
            {portfolioError}
          </p>
        )}
        {portfolio.length === 0 ? (
          <p className="mt-4 text-sm text-[var(--color-muted)]">
            {isOwner
              ? 'No samples yet — pin a completed workflow from the results page.'
              : 'No public work samples yet.'}
          </p>
        ) : (
          <div className="mt-4 space-y-4">
            {portfolio.map((item) => (
              <article
                key={item.id}
                className="rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] p-4"
              >
                <div className="flex flex-wrap items-start justify-between gap-3">
                  <h3 className="font-semibold text-[var(--color-text)]">{item.title}</h3>
                  {isOwner && (
                    <button
                      type="button"
                      onClick={() => handleRemovePortfolio(item.id)}
                      className="rounded-md border border-red-500/30 px-2.5 py-1 text-xs text-red-400 hover:bg-red-500/10"
                    >
                      Remove
                    </button>
                  )}
                </div>
                {item.summary && (
                  <p className="mt-1 text-sm text-[var(--color-muted)]">{item.summary}</p>
                )}
                <pre className="mt-3 max-h-48 overflow-y-auto whitespace-pre-wrap text-sm leading-relaxed text-slate-200 font-sans">
                  {item.output_preview}
                </pre>
              </article>
            ))}
          </div>
        )}
      </div>

      {/* Hire / run */}
      <div
        ref={runSectionRef}
        id="run"
        className="mt-8 rounded-2xl border-2 border-cyan-500/30 bg-[var(--color-surface-raised)] p-6 sm:p-8"
      >
        <h2 className="text-xl font-bold text-[var(--color-text)]">Hire This Agent</h2>
        <p className="mt-1 text-sm text-[var(--color-muted)]">
          Describe your task. When done, you go straight to the results page.
        </p>

        {!user ? (
          <div className="mt-5 rounded-lg border border-cyan-500/30 bg-cyan-500/5 p-5">
            <p className="text-sm text-[var(--color-text-soft)]">
              Sign up free — <span className="text-cyan-400">$5 credit included</span> to try your first
              run.
            </p>
            <div className="mt-4 flex flex-wrap gap-3">
              <Link
                to="/register"
                state={{ from: location }}
                className="rounded-lg bg-cyan-500 px-5 py-2.5 text-sm font-bold text-slate-900 hover:bg-cyan-400"
              >
                Hire This Agent
              </Link>
              <Link
                to="/login"
                state={{ from: location }}
                className="rounded-lg border border-[var(--color-border)] px-5 py-2.5 text-sm text-[var(--color-text-soft)]"
              >
                I have an account
              </Link>
            </div>
          </div>
        ) : (
          <form onSubmit={handleRun} className="mt-5 space-y-4">
            {estimate && (
              <div className="rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)] px-4 py-3 text-sm">
                <p className="text-[var(--color-text-soft)]">
                  You pay{' '}
                  <span className="font-mono text-cyan-400">~${estTotal.toFixed(2)}</span> when the run
                  finishes.
                </p>
                <p className="mt-1 text-xs text-[var(--color-muted)]">
                  Your balance: ${balance?.toFixed(2) ?? '—'}
                  {!canAfford && (
                    <span className="text-red-400">
                      {' '}
                      — not enough.{' '}
                      <Link to="/billing" className="underline">
                        Add credits
                      </Link>
                    </span>
                  )}
                </p>
              </div>
            )}
            <div>
              <label className="block text-xs font-medium text-[var(--color-muted)] mb-1.5">What should this agent do?</label>
              <textarea
                required
                rows={4}
                value={task}
                onChange={(e) => setTask(e.target.value)}
                placeholder="e.g. Write 5 SEO titles for my coffee shop landing page…"
                className="w-full rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)] px-3 py-3 text-sm text-white placeholder:text-[var(--color-muted)] focus:border-cyan-500/50 focus:outline-none resize-y"
              />
            </div>
            <label className="flex items-center gap-2 text-sm text-[var(--color-muted)] cursor-pointer">
              <input
                type="checkbox"
                checked={humanReview}
                onChange={(e) => setHumanReview(e.target.checked)}
                className="rounded border-[var(--color-border)] bg-[var(--color-surface)] text-cyan-500"
              />
              Pause for my approval before finishing
            </label>
            <LocalBridgeSelector
              devices={bridgeDevices}
              enabled={bridgeEnabled}
              onEnabledChange={setBridgeEnabled}
              deviceId={bridgeDeviceId}
              onDeviceIdChange={setBridgeDeviceId}
            />
            {error && (
              <p className="rounded-lg bg-red-500/10 border border-red-500/20 px-3 py-2 text-sm text-red-400">
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
              disabled={running || (estimate != null && !canAfford)}
              className="w-full sm:w-auto rounded-lg bg-cyan-500 px-8 py-3 text-sm font-bold text-slate-900 hover:bg-cyan-400 disabled:opacity-50"
            >
              {running ? 'Starting…' : `Hire This Agent — ~$${estTotal.toFixed(2)}`}
            </button>
          </form>
        )}
      </div>
    </div>
  )
}