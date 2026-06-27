import { useEffect, useState, type FormEvent } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../api/client'
import { AgentCard } from '../components/AgentCard'
import { LocalBridgeSelector } from '../components/LocalBridgeSelector'
import { useAuth } from '../context/AuthContext'
import { useLocalBridge } from '../hooks/useLocalBridge'
import { LLM_PROVIDERS, resolveProvider, type LlmProvider } from '../lib/llmProviders'
import type { Agent } from '../types'

type AgentFormState = {
  name: string
  description: string
  role: string
  llmProvider: LlmProvider
  llmModel: string
  category: string
  price: string
}

const emptyForm = (): AgentFormState => ({
  name: '',
  description: '',
  role: '',
  llmProvider: 'gemini',
  llmModel: 'gemini-2.5-flash',
  category: '',
  price: '0',
})

function formFromAgent(agent: Agent): AgentFormState {
  const provider = resolveProvider(agent.llm_model)
  const knownModel = LLM_PROVIDERS[provider].models.some((m) => m.id === agent.llm_model)
  return {
    name: agent.name,
    description: agent.description,
    role: agent.role,
    llmProvider: provider,
    llmModel: knownModel ? agent.llm_model : LLM_PROVIDERS[provider].models[0].id,
    category: agent.category ?? '',
    price: agent.price_usd_per_run,
  }
}

export function Dashboard() {
  const { user, token } = useAuth()
  const [myAgents, setMyAgents] = useState<Agent[]>([])
  const [allAgents, setAllAgents] = useState<Agent[]>([])
  const [showCreate, setShowCreate] = useState(false)
  const [editingAgent, setEditingAgent] = useState<Agent | null>(null)
  const [form, setForm] = useState<AgentFormState>(emptyForm())
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [saving, setSaving] = useState(false)

  const showForm = showCreate || editingAgent !== null

  function loadAgents() {
    if (!token) return
    api.listAgents(token)
      .then((all) => {
        setAllAgents(all)
        setMyAgents(all.filter((a) => a.owner_id === user?.id))
      })
      .catch((err) => setError(err instanceof Error ? err.message : 'Failed to load'))
      .finally(() => setLoading(false))
  }

  useEffect(() => {
    loadAgents()
  }, [token, user?.id])

  function openCreate() {
    setEditingAgent(null)
    setForm(emptyForm())
    setShowCreate(true)
    setError('')
  }

  function openEdit(agent: Agent) {
    setShowCreate(false)
    setEditingAgent(agent)
    setForm(formFromAgent(agent))
    setError('')
  }

  function closeForm() {
    setShowCreate(false)
    setEditingAgent(null)
    setForm(emptyForm())
  }

  async function handleSubmit(e: FormEvent) {
    e.preventDefault()
    if (!token) return
    setSaving(true)
    setError('')
    const payload = {
      name: form.name,
      description: form.description,
      role: form.role,
      llm_model: form.llmModel,
      category: form.category || null,
      price_usd_per_run: form.price,
      tools: [],
      capabilities: [],
    }
    try {
      if (editingAgent) {
        await api.updateAgent(token, editingAgent.id, payload)
      } else {
        await api.createAgent(token, payload)
      }
      closeForm()
      loadAgents()
    } catch (err) {
      setError(err instanceof Error ? err.message : editingAgent ? 'Failed to update agent' : 'Failed to create agent')
    } finally {
      setSaving(false)
    }
  }

  async function handleDelete(agent: Agent) {
    if (!token || !confirm(`Delete "${agent.name}"? This cannot be undone.`)) return
    setError('')
    try {
      await api.deleteAgent(token, agent.id)
      if (editingAgent?.id === agent.id) {
        closeForm()
      }
      loadAgents()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to delete agent')
    }
  }

  return (
    <div className="mx-auto max-w-6xl px-4 py-10 sm:px-6">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold text-[var(--color-text)]">Dashboard</h1>
          <p className="mt-1 text-[var(--color-muted)]">
            Welcome, {user?.full_name}. Manage your agents and workflows.
          </p>
        </div>
        <button
          type="button"
          onClick={() => (showForm && !editingAgent ? closeForm() : openCreate())}
          className="rounded-lg bg-cyan-500 px-4 py-2 text-sm font-semibold text-slate-900 hover:bg-cyan-400 transition-colors"
        >
          {showForm && !editingAgent ? 'Cancel' : 'Create agent'}
        </button>
      </div>

      {showForm && (
        <AgentForm
          title={editingAgent ? `Edit agent — ${editingAgent.name}` : 'New agent'}
          form={form}
          setForm={setForm}
          onSubmit={handleSubmit}
          onCancel={closeForm}
          saving={saving}
          submitLabel={editingAgent ? 'Save changes' : 'Create agent'}
        />
      )}

      {error && (
        <p className="mt-4 rounded-lg border border-red-500/30 bg-red-500/10 px-4 py-3 text-sm text-red-400">
          {error}
        </p>
      )}

      <section className="mt-10">
        <h2 className="text-lg font-semibold text-[var(--color-text)]">Your agents ({myAgents.length})</h2>
        {loading ? (
          <p className="mt-4 text-[var(--color-muted)]">Loading…</p>
        ) : myAgents.length === 0 ? (
          <p className="mt-4 text-sm text-[var(--color-muted)]">
            You haven&apos;t created any agents yet.
          </p>
        ) : (
          <div className="mt-4 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {myAgents.map((agent) => (
              <AgentCard
                key={agent.id}
                agent={agent}
                href={null}
                actions={
                  <AgentActions
                    agent={agent}
                    onEdit={() => openEdit(agent)}
                    onDelete={() => handleDelete(agent)}
                  />
                }
              />
            ))}
          </div>
        )}
      </section>

      <section className="mt-12">
        <h2 className="text-lg font-semibold text-[var(--color-text)]">Quick run — Multi-agent crew</h2>
        <p className="mt-1 text-sm text-[var(--color-muted)]">
          {myAgents.length > 0
            ? 'Run your agents in sequence on a task (uses your models — Gemini, Claude, Grok, etc.).'
            : 'Run the default Researcher → Writer → Reviewer pipeline on a task.'}
        </p>
        <MultiAgentRunner
          agents={
            myAgents.length > 0
              ? myAgents.filter((a) => a.is_active).slice(0, 3)
              : allAgents.filter((a) => a.is_active).slice(0, 3)
          }
        />
      </section>
    </div>
  )
}

function AgentActions({
  agent,
  onEdit,
  onDelete,
}: {
  agent: Agent
  onEdit: () => void
  onDelete: () => void
}) {
  return (
    <>
      <Link
        to={`/agents/${agent.id}`}
        className="rounded-md border border-cyan-500/30 px-3 py-1.5 text-xs font-medium text-cyan-400 hover:bg-cyan-500/10"
      >
        Open
      </Link>
      <button
        type="button"
        onClick={onEdit}
        className="rounded-md border border-[var(--color-border)] px-3 py-1.5 text-xs font-medium text-[var(--color-text)] hover:bg-[var(--color-surface)]"
      >
        Edit
      </button>
      <button
        type="button"
        onClick={onDelete}
        className="rounded-md border border-red-500/30 px-3 py-1.5 text-xs font-medium text-red-400 hover:bg-red-500/10"
      >
        Delete
      </button>
    </>
  )
}

function AgentForm({
  title,
  form,
  setForm,
  onSubmit,
  onCancel,
  saving,
  submitLabel,
}: {
  title: string
  form: AgentFormState
  setForm: (next: AgentFormState) => void
  onSubmit: (e: FormEvent) => void
  onCancel: () => void
  saving: boolean
  submitLabel: string
}) {
  return (
    <form
      onSubmit={onSubmit}
      className="mt-8 rounded-2xl border border-[var(--color-border)] bg-[var(--color-surface-raised)] p-6 space-y-4"
    >
      <div className="flex items-center justify-between gap-3">
        <h2 className="font-semibold text-[var(--color-text)]">{title}</h2>
        <button
          type="button"
          onClick={onCancel}
          className="text-sm text-[var(--color-muted)] hover:text-[var(--color-text)]"
        >
          Cancel
        </button>
      </div>
      <div className="grid gap-4 sm:grid-cols-2">
        <input
          required
          placeholder="Name"
          value={form.name}
          onChange={(e) => setForm({ ...form, name: e.target.value })}
          className="rounded-lg border border-[var(--color-border)] bg-white px-3 py-2 text-sm text-[var(--color-text)] focus:border-cyan-500/50 focus:outline-none"
        />
        <input
          placeholder="Category (e.g. research)"
          value={form.category}
          onChange={(e) => setForm({ ...form, category: e.target.value })}
          className="rounded-lg border border-[var(--color-border)] bg-white px-3 py-2 text-sm text-[var(--color-text)] focus:border-cyan-500/50 focus:outline-none"
        />
      </div>
      <textarea
        required
        placeholder="Description"
        rows={2}
        value={form.description}
        onChange={(e) => setForm({ ...form, description: e.target.value })}
        className="w-full rounded-lg border border-[var(--color-border)] bg-white px-3 py-2 text-sm text-[var(--color-text)] focus:border-cyan-500/50 focus:outline-none resize-y"
      />
      <textarea
        required
        placeholder="Role / system prompt"
        rows={3}
        value={form.role}
        onChange={(e) => setForm({ ...form, role: e.target.value })}
        className="w-full rounded-lg border border-[var(--color-border)] bg-white px-3 py-2 text-sm text-[var(--color-text)] focus:border-cyan-500/50 focus:outline-none resize-y"
      />
      <div className="grid gap-4 sm:grid-cols-3">
        <div>
          <label className="mb-1 block text-xs text-[var(--color-muted)]">AI provider</label>
          <select
            value={form.llmProvider}
            onChange={(e) => {
              const provider = e.target.value as LlmProvider
              setForm({
                ...form,
                llmProvider: provider,
                llmModel: LLM_PROVIDERS[provider].models[0].id,
              })
            }}
            className="w-full rounded-lg border border-[var(--color-border)] bg-white px-3 py-2 text-sm text-[var(--color-text)] focus:border-cyan-500/50 focus:outline-none"
          >
            {(Object.entries(LLM_PROVIDERS) as [LlmProvider, (typeof LLM_PROVIDERS)[LlmProvider]][]).map(
              ([id, cfg]) => (
                <option key={id} value={id}>
                  {cfg.label}
                </option>
              ),
            )}
          </select>
        </div>
        <div>
          <label className="mb-1 block text-xs text-[var(--color-muted)]">Model</label>
          <select
            required
            value={form.llmModel}
            onChange={(e) => setForm({ ...form, llmModel: e.target.value })}
            className="w-full rounded-lg border border-[var(--color-border)] bg-white px-3 py-2 text-sm text-[var(--color-text)] focus:border-cyan-500/50 focus:outline-none"
          >
            {LLM_PROVIDERS[form.llmProvider].models.map((model) => (
              <option key={model.id} value={model.id}>
                {model.label}
              </option>
            ))}
          </select>
        </div>
        <input
          type="number"
          step="0.001"
          min="0"
          placeholder="Price per run (USD)"
          value={form.price}
          onChange={(e) => setForm({ ...form, price: e.target.value })}
          className="rounded-lg border border-[var(--color-border)] bg-white px-3 py-2 text-sm text-[var(--color-text)] focus:border-cyan-500/50 focus:outline-none"
        />
      </div>
      <button
        type="submit"
        disabled={saving}
        className="rounded-lg bg-cyan-500 px-4 py-2 text-sm font-semibold text-slate-900 hover:bg-cyan-400 disabled:opacity-50"
      >
        {saving ? 'Saving…' : submitLabel}
      </button>
    </form>
  )
}

function MultiAgentRunner({ agents }: { agents: Agent[] }) {
  const { token } = useAuth()
  const [task, setTask] = useState('')
  const [running, setRunning] = useState(false)
  const [error, setError] = useState('')
  const {
    devices: bridgeDevices,
    enabled: bridgeEnabled,
    setEnabled: setBridgeEnabled,
    deviceId: bridgeDeviceId,
    setDeviceId: setBridgeDeviceId,
    bridgeDeviceId: selectedBridgeDeviceId,
  } = useLocalBridge(token)

  if (agents.length < 1) return null

  async function handleRun(e: FormEvent) {
    e.preventDefault()
    if (!token) return
    setRunning(true)
    setError('')
    try {
      const result = await api.runWorkflow(token, {
        task_description: task,
        workflow_type: 'multi_agent',
        agents: agents.map((a) => a.id),
        bridge_device_id: selectedBridgeDeviceId,
      })
      window.location.href = `/workflows/${result.workflow_id}`
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to run')
    } finally {
      setRunning(false)
    }
  }

  return (
    <form onSubmit={handleRun} className="mt-4 rounded-xl border border-[var(--color-border)] bg-[var(--color-surface-raised)] p-5 space-y-3">
      <p className="text-xs text-[var(--color-muted)]">
        Crew: {agents.map((a) => a.name).join(' → ')}
      </p>
      <textarea
        required
        rows={2}
        value={task}
        onChange={(e) => setTask(e.target.value)}
        placeholder="Task for the multi-agent crew…"
        className="w-full rounded-lg border border-[var(--color-border)] bg-white px-3 py-2 text-sm text-[var(--color-text)] focus:border-cyan-500/50 focus:outline-none resize-y"
      />
      <LocalBridgeSelector
        devices={bridgeDevices}
        enabled={bridgeEnabled}
        onEnabledChange={setBridgeEnabled}
        deviceId={bridgeDeviceId}
        onDeviceIdChange={setBridgeDeviceId}
        hint="Each agent in the crew can use bridge.* tools on the selected device when relevant."
      />
      {error && <p className="text-sm text-red-400">{error}</p>}
      <button
        type="submit"
        disabled={running}
        className="rounded-lg border border-cyan-500/40 px-4 py-2 text-sm text-cyan-400 hover:bg-cyan-500/10 disabled:opacity-50"
      >
        {running ? 'Running…' : 'Run multi-agent workflow'}
      </button>
    </form>
  )
}