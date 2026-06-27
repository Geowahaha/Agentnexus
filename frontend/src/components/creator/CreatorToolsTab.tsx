import { useCallback, useEffect, useState, type FormEvent } from 'react'
import { api } from '../../api/client'
import type { CustomTool, MCPServer, MCPTool } from '../../types'

type CustomToolForm = {
  name: string
  description: string
  url: string
  method: string
  argMapping: 'body' | 'query'
  headersJson: string
  inputSchemaJson: string
}

type McpForm = {
  name: string
  description: string
  transport: 'http' | 'sse' | 'stdio'
  url: string
  headersJson: string
  command: string
  argsText: string
  envJson: string
}

const emptyCustomToolForm = (): CustomToolForm => ({
  name: '',
  description: '',
  url: '',
  method: 'POST',
  argMapping: 'body',
  headersJson: '',
  inputSchemaJson: '',
})

const emptyMcpForm = (): McpForm => ({
  name: '',
  description: '',
  transport: 'http',
  url: '',
  headersJson: '',
  command: '',
  argsText: '',
  envJson: '',
})

function toSnakeName(label: string) {
  return label
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '_')
    .replace(/^_+|_+$/g, '')
    .replace(/_+/g, '_')
}

function toMcpName(label: string) {
  return label
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-+|-+$/g, '')
    .replace(/-+/g, '-')
}

function parseOptionalJson(text: string, field: string): Record<string, unknown> | undefined {
  const trimmed = text.trim()
  if (!trimmed) return undefined
  try {
    const parsed = JSON.parse(trimmed) as unknown
    if (typeof parsed !== 'object' || parsed === null || Array.isArray(parsed)) {
      throw new Error(`${field} must be a JSON object`)
    }
    return parsed as Record<string, unknown>
  } catch (err) {
    throw new Error(err instanceof Error ? err.message : `Invalid ${field} JSON`)
  }
}

function parseOptionalSchema(text: string): Record<string, unknown> | undefined {
  const trimmed = text.trim()
  if (!trimmed) return undefined
  const parsed = parseOptionalJson(trimmed, 'Input schema')
  return parsed
}

function inputClassName() {
  return 'mt-1 w-full rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)] px-3 py-2 text-white placeholder:text-[var(--color-muted)]'
}

function labelClassName() {
  return 'block text-sm text-[var(--color-muted)]'
}

function McpToolsList({
  tools,
  loading,
}: {
  tools: MCPTool[]
  loading: boolean
}) {
  if (loading) {
    return (
      <p className="mt-3 text-xs text-[var(--color-muted)]">Loading synced tools…</p>
    )
  }

  if (tools.length === 0) {
    return (
      <div className="mt-3 rounded-lg border border-dashed border-[var(--color-border)] px-3 py-2.5">
        <p className="text-xs text-[var(--color-muted)]">No tools synced yet. Run Sync Tools to discover capabilities.</p>
      </div>
    )
  }

  return (
    <div className="mt-3">
      <p className="mb-2 text-xs font-medium uppercase tracking-wider text-[var(--color-muted)]">
        Synced tools ({tools.length})
      </p>
      <ul className="max-h-48 space-y-2 overflow-y-auto rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)]/60 p-2">
        {tools.map((tool) => (
          <li
            key={tool.id}
            className="rounded-md border border-[var(--color-border)]/60 bg-[var(--color-surface-raised)] px-3 py-2"
          >
            <div className="flex items-start justify-between gap-2">
              <code className="text-xs font-medium text-indigo-300">{tool.qualified_name}</code>
              <span className={`shrink-0 text-[10px] ${tool.is_active ? 'text-emerald-400' : 'text-amber-400'}`}>
                {tool.is_active ? 'active' : 'inactive'}
              </span>
            </div>
            {tool.description && (
              <p className="mt-1 text-xs leading-relaxed text-[var(--color-muted)] line-clamp-2">
                {tool.description}
              </p>
            )}
          </li>
        ))}
      </ul>
    </div>
  )
}

type CreatorToolsTabProps = {
  token: string | null
}

export function CreatorToolsTab({ token }: CreatorToolsTabProps) {
  const [tools, setTools] = useState<CustomTool[]>([])
  const [mcpServers, setMcpServers] = useState<MCPServer[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [notice, setNotice] = useState('')

  const [showToolForm, setShowToolForm] = useState(false)
  const [showMcpForm, setShowMcpForm] = useState(false)
  const [toolForm, setToolForm] = useState<CustomToolForm>(emptyCustomToolForm())
  const [mcpForm, setMcpForm] = useState<McpForm>(emptyMcpForm())
  const [savingTool, setSavingTool] = useState(false)
  const [savingMcp, setSavingMcp] = useState(false)
  const [syncingId, setSyncingId] = useState<string | null>(null)
  const [mcpToolsByServer, setMcpToolsByServer] = useState<Record<string, MCPTool[]>>({})
  const [loadingMcpTools, setLoadingMcpTools] = useState<Record<string, boolean>>({})

  const loadMcpTools = useCallback(
    async (servers: MCPServer[]) => {
      if (!token || servers.length === 0) {
        setMcpToolsByServer({})
        return
      }

      const loadingState = Object.fromEntries(servers.map((s) => [s.id, true]))
      setLoadingMcpTools(loadingState)

      try {
        const entries = await Promise.all(
          servers.map(async (server) => {
            const synced = await api.listMcpServerTools(token, server.id)
            return [server.id, synced] as const
          }),
        )
        setMcpToolsByServer(Object.fromEntries(entries))
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load MCP tools')
      } finally {
        setLoadingMcpTools({})
      }
    },
    [token],
  )

  const setServerMcpTools = useCallback((serverId: string, synced: MCPTool[]) => {
    setMcpToolsByServer((prev) => ({ ...prev, [serverId]: synced }))
  }, [])

  const load = useCallback(async () => {
    if (!token) return
    setLoading(true)
    setError('')
    try {
      const [toolList, serverList] = await Promise.all([
        api.getCreatorTools(token),
        api.getCreatorMcpServers(token),
      ])
      setTools(toolList)
      setMcpServers(serverList)
      await loadMcpTools(serverList)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load tools')
    } finally {
      setLoading(false)
    }
  }, [token, loadMcpTools])

  useEffect(() => {
    load()
  }, [load])

  function buildCustomToolConfig(form: CustomToolForm): Record<string, unknown> {
    const config: Record<string, unknown> = {
      url: form.url.trim(),
      method: form.method,
      arg_mapping: form.argMapping,
    }
    const headers = parseOptionalJson(form.headersJson, 'Headers')
    if (headers) config.headers = headers
    const inputSchema = parseOptionalSchema(form.inputSchemaJson)
    if (inputSchema) config.input_schema = inputSchema
    return config
  }

  function buildMcpConfig(form: McpForm): Record<string, unknown> {
    if (form.transport === 'stdio') {
      const config: Record<string, unknown> = {
        command: form.command.trim(),
        args: form.argsText
          .split(/[\n,]/)
          .map((s) => s.trim())
          .filter(Boolean),
      }
      const env = parseOptionalJson(form.envJson, 'Environment')
      if (env) config.env = env
      return config
    }

    const config: Record<string, unknown> = { url: form.url.trim() }
    const headers = parseOptionalJson(form.headersJson, 'Headers')
    if (headers) config.headers = headers
    return config
  }

  async function handleCreateTool(e: FormEvent) {
    e.preventDefault()
    if (!token) return
    setSavingTool(true)
    setError('')
    setNotice('')
    try {
      const name = toolForm.name.trim() || toSnakeName(toolForm.description)
      if (!/^[a-z][a-z0-9_]*$/.test(name)) {
        throw new Error('Tool name must be lowercase letters, numbers, and underscores (start with a letter).')
      }
      await api.createCustomTool(token, {
        name,
        description: toolForm.description.trim(),
        tool_type: 'http',
        config: buildCustomToolConfig(toolForm),
        is_active: true,
      })
      setShowToolForm(false)
      setToolForm(emptyCustomToolForm())
      setNotice(`Custom tool "${name}" created.`)
      await load()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create tool')
    } finally {
      setSavingTool(false)
    }
  }

  async function handleCreateMcp(e: FormEvent) {
    e.preventDefault()
    if (!token) return
    setSavingMcp(true)
    setError('')
    setNotice('')
    try {
      const name = mcpForm.name.trim() || toMcpName(mcpForm.description)
      if (!/^[a-z][a-z0-9_-]*$/.test(name)) {
        throw new Error('Server name must be lowercase letters, numbers, hyphens, and underscores.')
      }
      if (mcpForm.transport === 'stdio' && !mcpForm.command.trim()) {
        throw new Error('Command is required for stdio transport.')
      }
      if (mcpForm.transport !== 'stdio' && !mcpForm.url.trim()) {
        throw new Error('URL is required for HTTP/SSE transport.')
      }

      const server = await api.createMcpServer(token, {
        name,
        description: mcpForm.description.trim(),
        transport: mcpForm.transport,
        config: buildMcpConfig(mcpForm),
        is_active: true,
      })
      setShowMcpForm(false)
      setMcpForm(emptyMcpForm())
      setNotice(`MCP server "${name}" connected. Sync tools to discover capabilities.`)
      await load()

      setSyncingId(server.id)
      try {
        const synced = await api.syncMcpServerTools(token, server.id)
        setServerMcpTools(server.id, synced)
        setNotice(`MCP server "${name}" connected — ${synced.length} tool(s) synced.`)
      } catch {
        setNotice(`MCP server "${name}" connected. Sync tools manually when the endpoint is reachable.`)
      } finally {
        setSyncingId(null)
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to connect MCP server')
    } finally {
      setSavingMcp(false)
    }
  }

  async function toggleTool(tool: CustomTool) {
    if (!token) return
    try {
      await api.updateCustomTool(token, tool.id, { is_active: !tool.is_active })
      setNotice(tool.is_active ? 'Tool deactivated.' : 'Tool activated.')
      await load()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to update tool')
    }
  }

  async function deleteTool(tool: CustomTool) {
    if (!token) return
    if (!window.confirm(`Delete custom tool "${tool.name}"?`)) return
    try {
      await api.deleteCustomTool(token, tool.id)
      setNotice('Custom tool deleted.')
      await load()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to delete tool')
    }
  }

  async function toggleMcpServer(server: MCPServer) {
    if (!token) return
    try {
      await api.updateMcpServer(token, server.id, { is_active: !server.is_active })
      setNotice(server.is_active ? 'MCP server deactivated.' : 'MCP server activated.')
      await load()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to update MCP server')
    }
  }

  async function syncMcp(server: MCPServer) {
    if (!token) return
    setSyncingId(server.id)
    setError('')
    setNotice('')
    try {
      const synced = await api.syncMcpServerTools(token, server.id)
      setServerMcpTools(server.id, synced)
      setNotice(`Synced ${synced.length} tool(s) from "${server.name}".`)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'MCP sync failed')
    } finally {
      setSyncingId(null)
    }
  }

  async function deleteMcp(server: MCPServer) {
    if (!token) return
    if (!window.confirm(`Disconnect MCP server "${server.name}"?`)) return
    try {
      await api.deleteMcpServer(token, server.id)
      setMcpServers((prev) => prev.filter((s) => s.id !== server.id))
      setMcpToolsByServer((prev) => {
        const next = { ...prev }
        delete next[server.id]
        return next
      })
      setNotice('MCP server removed.')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to delete MCP server')
    }
  }

  if (loading) {
    return <p className="text-sm text-[var(--color-muted)]">Loading tools & integrations…</p>
  }

  return (
    <div className="space-y-8">
      {error && (
        <div className="rounded-lg border border-red-500/40 bg-red-500/10 px-4 py-3 text-sm text-red-300">
          {error}
        </div>
      )}
      {notice && (
        <div className="rounded-lg border border-emerald-500/40 bg-emerald-500/10 px-4 py-3 text-sm text-emerald-700">
          {notice}
        </div>
      )}

      <section>
        <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
          <div>
            <h2 className="text-lg font-semibold text-[var(--color-text)]">Custom Tools</h2>
            <p className="text-sm text-[var(--color-muted)]">HTTP endpoints your agents and skills can call.</p>
          </div>
          <button
            type="button"
            onClick={() => {
              setShowToolForm((v) => !v)
              setShowMcpForm(false)
            }}
            className="rounded-lg border border-cyan-500/40 bg-cyan-500/10 px-4 py-2 text-sm font-medium text-cyan-300 hover:bg-cyan-500/20"
          >
            {showToolForm ? 'Cancel' : '+ Add Custom Tool'}
          </button>
        </div>

        {showToolForm && (
          <form
            onSubmit={handleCreateTool}
            className="mb-6 rounded-xl border border-cyan-500/30 bg-[var(--color-surface-raised)] p-6"
          >
            <h3 className="font-semibold text-[var(--color-text)]">New HTTP Tool</h3>
            <p className="mt-1 text-xs text-[var(--color-muted)]">
              Name is used as the tool identifier in pipelines (e.g. <code className="text-cyan-400">my_scanner</code>).
            </p>
            <div className="mt-4 grid gap-4 sm:grid-cols-2">
              <label className={labelClassName()}>
                Name
                <input
                  value={toolForm.name}
                  onChange={(e) => setToolForm((f) => ({ ...f, name: e.target.value }))}
                  placeholder="my_api_tool"
                  pattern="^[a-z][a-z0-9_]*$"
                  className={`${inputClassName()} font-mono`}
                />
              </label>
              <label className={labelClassName()}>
                HTTP Method
                <select
                  value={toolForm.method}
                  onChange={(e) => setToolForm((f) => ({ ...f, method: e.target.value }))}
                  className={inputClassName()}
                >
                  <option value="POST">POST</option>
                  <option value="GET">GET</option>
                  <option value="PUT">PUT</option>
                  <option value="PATCH">PATCH</option>
                </select>
              </label>
              <label className={`${labelClassName()} sm:col-span-2`}>
                Description
                <textarea
                  required
                  rows={2}
                  value={toolForm.description}
                  onChange={(e) =>
                    setToolForm((f) => ({
                      ...f,
                      description: e.target.value,
                      name: f.name || toSnakeName(e.target.value),
                    }))
                  }
                  placeholder="What does this tool do?"
                  className={inputClassName()}
                />
              </label>
              <label className={`${labelClassName()} sm:col-span-2`}>
                Endpoint URL
                <input
                  required
                  type="url"
                  value={toolForm.url}
                  onChange={(e) => setToolForm((f) => ({ ...f, url: e.target.value }))}
                  placeholder="https://api.example.com/v1/run"
                  className={inputClassName()}
                />
              </label>
              <label className={labelClassName()}>
                Send args as
                <select
                  value={toolForm.argMapping}
                  onChange={(e) =>
                    setToolForm((f) => ({ ...f, argMapping: e.target.value as 'body' | 'query' }))
                  }
                  className={inputClassName()}
                >
                  <option value="body">JSON body</option>
                  <option value="query">Query string</option>
                </select>
              </label>
              <label className={labelClassName()}>
                Headers (JSON, optional)
                <input
                  value={toolForm.headersJson}
                  onChange={(e) => setToolForm((f) => ({ ...f, headersJson: e.target.value }))}
                  placeholder='{"Authorization": "Bearer ..."}'
                  className={`${inputClassName()} font-mono text-xs`}
                />
              </label>
              <label className={`${labelClassName()} sm:col-span-2`}>
                Input schema (JSON, optional)
                <textarea
                  rows={3}
                  value={toolForm.inputSchemaJson}
                  onChange={(e) => setToolForm((f) => ({ ...f, inputSchemaJson: e.target.value }))}
                  placeholder='{"type":"object","properties":{"url":{"type":"string"}},"required":["url"]}'
                  className={`${inputClassName()} font-mono text-xs`}
                />
              </label>
            </div>
            <button
              type="submit"
              disabled={savingTool}
              className="mt-4 rounded-lg bg-cyan-500 px-4 py-2 text-sm font-semibold text-slate-900 disabled:opacity-50"
            >
              {savingTool ? 'Saving…' : 'Save Tool'}
            </button>
          </form>
        )}

        {tools.length === 0 ? (
          <p className="rounded-xl border border-dashed border-[var(--color-border)] p-8 text-center text-sm text-[var(--color-muted)]">
            No custom tools yet. Add an HTTP endpoint your pipelines can invoke.
          </p>
        ) : (
          <div className="grid gap-3 sm:grid-cols-2">
            {tools.map((tool) => (
              <div
                key={tool.id}
                className="rounded-xl border border-[var(--color-border)] bg-[var(--color-surface-raised)] p-4"
              >
                <div className="flex items-start justify-between gap-2">
                  <p className="font-mono text-sm font-medium text-cyan-300">{tool.name}</p>
                  <span className={`shrink-0 text-xs ${tool.is_active ? 'text-emerald-400' : 'text-amber-400'}`}>
                    {tool.is_active ? 'Active' : 'Inactive'}
                  </span>
                </div>
                <p className="mt-2 text-sm text-[var(--color-muted)] line-clamp-2">{tool.description}</p>
                <p className="mt-2 truncate font-mono text-xs text-[var(--color-muted)]">
                  {String(tool.config.url ?? '—')}
                </p>
                <div className="mt-3 flex flex-wrap gap-2">
                  <button
                    type="button"
                    onClick={() => toggleTool(tool)}
                    className="rounded border border-[var(--color-border)] px-2 py-1 text-xs text-[var(--color-text-soft)] hover:border-cyan-500/50"
                  >
                    {tool.is_active ? 'Deactivate' : 'Activate'}
                  </button>
                  <button
                    type="button"
                    onClick={() => deleteTool(tool)}
                    className="rounded border border-red-500/30 px-2 py-1 text-xs text-red-400 hover:bg-red-500/10"
                  >
                    Delete
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </section>

      <section>
        <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
          <div>
            <h2 className="text-lg font-semibold text-[var(--color-text)]">MCP Servers</h2>
            <p className="text-sm text-[var(--color-muted)]">
              Connect Model Context Protocol servers to expose tools like{' '}
              <code className="text-indigo-300">mcp.server_name.tool</code>.
            </p>
          </div>
          <button
            type="button"
            onClick={() => {
              setShowMcpForm((v) => !v)
              setShowToolForm(false)
            }}
            className="rounded-lg border border-indigo-500/40 bg-indigo-500/10 px-4 py-2 text-sm font-medium text-indigo-300 hover:bg-indigo-500/20"
          >
            {showMcpForm ? 'Cancel' : '+ Connect MCP Server'}
          </button>
        </div>

        {showMcpForm && (
          <form
            onSubmit={handleCreateMcp}
            className="mb-6 rounded-xl border border-indigo-500/30 bg-[var(--color-surface-raised)] p-6"
          >
            <h3 className="font-semibold text-[var(--color-text)]">Connect MCP Server</h3>
            <p className="mt-1 text-xs text-[var(--color-muted)]">
              HTTP is recommended for remote servers (e.g. AIBotAuth). Tools sync automatically after connect.
            </p>
            <div className="mt-4 grid gap-4 sm:grid-cols-2">
              <label className={labelClassName()}>
                Server name
                <input
                  value={mcpForm.name}
                  onChange={(e) => setMcpForm((f) => ({ ...f, name: e.target.value }))}
                  placeholder="my-mcp-server"
                  pattern="^[a-z][a-z0-9_-]*$"
                  className={`${inputClassName()} font-mono`}
                />
              </label>
              <label className={labelClassName()}>
                Transport
                <select
                  value={mcpForm.transport}
                  onChange={(e) =>
                    setMcpForm((f) => ({ ...f, transport: e.target.value as McpForm['transport'] }))
                  }
                  className={inputClassName()}
                >
                  <option value="http">HTTP (remote API)</option>
                  <option value="sse">SSE (streaming)</option>
                  <option value="stdio">Stdio (local process)</option>
                </select>
              </label>
              <label className={`${labelClassName()} sm:col-span-2`}>
                Description
                <textarea
                  required
                  rows={2}
                  value={mcpForm.description}
                  onChange={(e) =>
                    setMcpForm((f) => ({
                      ...f,
                      description: e.target.value,
                      name: f.name || toMcpName(e.target.value),
                    }))
                  }
                  placeholder="What tools does this server provide?"
                  className={inputClassName()}
                />
              </label>

              {mcpForm.transport === 'stdio' ? (
                <>
                  <label className={labelClassName()}>
                    Command
                    <input
                      required
                      value={mcpForm.command}
                      onChange={(e) => setMcpForm((f) => ({ ...f, command: e.target.value }))}
                      placeholder="npx"
                      className={`${inputClassName()} font-mono`}
                    />
                  </label>
                  <label className={labelClassName()}>
                    Arguments (comma or newline separated)
                    <input
                      value={mcpForm.argsText}
                      onChange={(e) => setMcpForm((f) => ({ ...f, argsText: e.target.value }))}
                      placeholder="-y, @modelcontextprotocol/server-filesystem, /path"
                      className={`${inputClassName()} font-mono text-xs`}
                    />
                  </label>
                  <label className={`${labelClassName()} sm:col-span-2`}>
                    Environment (JSON, optional)
                    <input
                      value={mcpForm.envJson}
                      onChange={(e) => setMcpForm((f) => ({ ...f, envJson: e.target.value }))}
                      placeholder='{"API_KEY": "..."}'
                      className={`${inputClassName()} font-mono text-xs`}
                    />
                  </label>
                </>
              ) : (
                <>
                  <label className={`${labelClassName()} sm:col-span-2`}>
                    Server URL
                    <input
                      required
                      type="url"
                      value={mcpForm.url}
                      onChange={(e) => setMcpForm((f) => ({ ...f, url: e.target.value }))}
                      placeholder="https://example.com/api/mcp"
                      className={inputClassName()}
                    />
                  </label>
                  <label className={`${labelClassName()} sm:col-span-2`}>
                    Headers (JSON, optional)
                    <input
                      value={mcpForm.headersJson}
                      onChange={(e) => setMcpForm((f) => ({ ...f, headersJson: e.target.value }))}
                      placeholder='{"Authorization": "Bearer ..."}'
                      className={`${inputClassName()} font-mono text-xs`}
                    />
                  </label>
                </>
              )}
            </div>
            <button
              type="submit"
              disabled={savingMcp}
              className="mt-4 rounded-lg bg-indigo-500 px-4 py-2 text-sm font-semibold text-[var(--color-text)] disabled:opacity-50 hover:bg-indigo-400"
            >
              {savingMcp ? 'Connecting…' : 'Connect & Sync Tools'}
            </button>
          </form>
        )}

        {mcpServers.length === 0 ? (
          <p className="rounded-xl border border-dashed border-[var(--color-border)] p-8 text-center text-sm text-[var(--color-muted)]">
            No MCP servers connected. Add a remote HTTP endpoint or local stdio process.
          </p>
        ) : (
          <div className="space-y-3">
            {mcpServers.map((server) => (
              <div
                key={server.id}
                className="rounded-xl border border-[var(--color-border)] bg-[var(--color-surface-raised)] p-4"
              >
                <div className="flex items-start justify-between gap-2">
                  <p className="font-mono text-sm font-medium text-indigo-300">{server.name}</p>
                  <span className={`shrink-0 text-xs ${server.is_active ? 'text-emerald-400' : 'text-amber-400'}`}>
                    {server.is_active ? 'Connected' : 'Inactive'}
                  </span>
                </div>
                <p className="mt-2 text-sm text-[var(--color-muted)] line-clamp-2">{server.description}</p>
                <p className="mt-2 text-xs text-[var(--color-muted)]">
                  Transport: {server.transport}
                  {server.config.url != null && (
                    <span className="mt-1 block truncate font-mono text-[var(--color-muted)]">
                      {String(server.config.url)}
                    </span>
                  )}
                  {server.config.command != null && (
                    <span className="mt-1 block truncate font-mono text-[var(--color-muted)]">
                      {String(server.config.command)}
                    </span>
                  )}
                </p>
                <div className="mt-3 flex flex-wrap gap-2">
                  <button
                    type="button"
                    disabled={syncingId === server.id}
                    onClick={() => syncMcp(server)}
                    className="rounded border border-indigo-500/40 px-2 py-1 text-xs text-indigo-300 hover:bg-indigo-500/10 disabled:opacity-50"
                  >
                    {syncingId === server.id ? 'Syncing…' : 'Sync Tools'}
                  </button>
                  <button
                    type="button"
                    onClick={() => toggleMcpServer(server)}
                    className="rounded border border-[var(--color-border)] px-2 py-1 text-xs text-[var(--color-text-soft)] hover:border-cyan-500/50"
                  >
                    {server.is_active ? 'Deactivate' : 'Activate'}
                  </button>
                  <button
                    type="button"
                    onClick={() => deleteMcp(server)}
                    className="rounded border border-red-500/30 px-2 py-1 text-xs text-red-400 hover:bg-red-500/10"
                  >
                    Remove
                  </button>
                </div>
                <McpToolsList
                  tools={mcpToolsByServer[server.id] ?? []}
                  loading={loadingMcpTools[server.id] === true}
                />
              </div>
            ))}
          </div>
        )}
      </section>
    </div>
  )
}