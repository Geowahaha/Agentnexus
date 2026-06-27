import { Link } from 'react-router-dom'
import { LLM_PROVIDERS, resolveProvider } from '../lib/llmProviders'
import { AgentThumbnail } from './AgentThumbnail'
import type { Agent } from '../types'
import type { ReactNode } from 'react'

const PROVIDER_COLORS: Record<string, string> = {
  gemini: 'bg-blue-500/15 text-blue-300',
  claude: 'bg-orange-500/15 text-orange-300',
  grok: 'bg-violet-500/15 text-violet-300',
  openai: 'bg-emerald-500/15 text-emerald-700',
}

interface AgentCardProps {
  agent: Agent
  showOwner?: boolean
  href?: string | null
  actions?: ReactNode
}

export function AgentCard({ agent, showOwner = false, href, actions }: AgentCardProps) {
  const price = Number(agent.price_usd_per_run)
  const provider = resolveProvider(agent.llm_model)
  const providerLabel = LLM_PROVIDERS[provider].label

  const cardClass =
    'group flex flex-col overflow-hidden rounded-xl border border-[var(--color-border)] bg-[var(--color-surface-raised)] transition-all hover:border-cyan-500/40 hover:shadow-lg hover:shadow-cyan-500/5'
  const destination = href === undefined ? `/agents/${agent.id}` : href

  const body = (
    <>
      <AgentThumbnail
        slug={agent.name.toLowerCase().replace(/[^a-z0-9]+/g, '-').slice(0, 48) || agent.id}
        id={agent.id}
        name={agent.name}
        category={agent.category}
        className="rounded-none"
      />
      <div className="flex flex-1 flex-col p-5">
        <div className="flex items-start justify-between gap-3">
          <div>
            <h3 className="font-semibold text-[var(--color-text)] group-hover:text-cyan-300 transition-colors">
              {agent.name}
            </h3>
            {agent.category && (
              <span className="mt-1 inline-block rounded-full bg-cyan-500/10 px-2 py-0.5 text-[11px] font-medium text-cyan-400">
                {agent.category}
              </span>
            )}
          </div>
          <div className="shrink-0 text-right">
            <span className="rounded-lg bg-[var(--color-surface-overlay)] px-2.5 py-1 font-mono text-xs text-cyan-400">
              ${price.toFixed(2)}
            </span>
            <p className="mt-0.5 text-[10px] text-[var(--color-muted)]">+ AI usage</p>
          </div>
        </div>

        <p className="mt-3 flex-1 text-sm leading-relaxed text-[var(--color-muted)] line-clamp-3">
          {agent.description}
        </p>

        <div className="mt-4 flex flex-wrap gap-1.5">
          {agent.capabilities.slice(0, 4).map((cap) => (
            <span
              key={cap}
              className="rounded-md bg-emerald-50 px-2 py-0.5 text-[11px] text-[var(--color-muted)]"
            >
              {cap}
            </span>
          ))}
        </div>

        <div className="mt-4 flex items-center justify-between border-t border-[var(--color-border)] pt-3 text-xs text-[var(--color-muted)]">
          <div className="flex items-center gap-2 min-w-0">
            <span className={`shrink-0 rounded-md px-2 py-0.5 text-[10px] font-semibold uppercase ${PROVIDER_COLORS[provider]}`}>
              {providerLabel}
            </span>
            <span className="truncate font-mono">{agent.llm_model}</span>
          </div>
          {agent.tools.length > 0 && (
            <span>{agent.tools.length} tool{agent.tools.length !== 1 ? 's' : ''}</span>
          )}
          {showOwner && <span className="truncate max-w-[120px]">owner: {agent.owner_id.slice(0, 8)}…</span>}
        </div>
        {actions && <div className="mt-4 flex flex-wrap gap-2 border-t border-[var(--color-border)] pt-3">{actions}</div>}
      </div>
    </>
  )

  if (destination) {
    return (
      <Link to={destination} className={cardClass}>
        {body}
      </Link>
    )
  }

  return <div className={cardClass}>{body}</div>
}