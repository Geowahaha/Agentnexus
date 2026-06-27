import { useCallback, useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../api/client'
import { useAuth } from '../context/AuthContext'
import type { BridgeDevice, BridgePairingCode } from '../types'

const PUBLIC_ORIGIN =
  typeof window !== 'undefined' ? window.location.origin : 'https://obolla.com'

export function BridgeDevices() {
  const { token, user } = useAuth()
  const [devices, setDevices] = useState<BridgeDevice[]>([])
  const [pairing, setPairing] = useState<BridgePairingCode | null>(null)
  const [loading, setLoading] = useState(true)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const [testPath, setTestPath] = useState('.')
  const [testFilePath, setTestFilePath] = useState('README.md')
  const [testOutput, setTestOutput] = useState('')
  const [selectedDeviceId, setSelectedDeviceId] = useState('')
  const [onlineMap, setOnlineMap] = useState<Record<string, boolean>>({})
  const [copied, setCopied] = useState('')

  const refresh = useCallback(async () => {
    if (!token) return
    const list = await api.listBridgeDevices(token)
    setDevices(list)
    setSelectedDeviceId((current) => {
      if (current && list.some((device) => device.id === current)) return current
      return list[0]?.id ?? ''
    })
  }, [token])

  useEffect(() => {
    if (!token) return
    refresh()
      .catch((err) => setError(err instanceof Error ? err.message : 'Failed to load devices'))
      .finally(() => setLoading(false))
  }, [token, refresh])

  useEffect(() => {
    if (!token || devices.length === 0) return
    let cancelled = false
    async function pollOnline() {
      const entries = await Promise.all(
        devices.map(async (device) => {
          try {
            const status = await api.getBridgeDeviceOnline(token!, device.id)
            return [device.id, status.online] as const
          } catch {
            return [device.id, false] as const
          }
        }),
      )
      if (!cancelled) {
        setOnlineMap(Object.fromEntries(entries))
      }
    }
    pollOnline()
    const timer = setInterval(pollOnline, 10000)
    return () => {
      cancelled = true
      clearInterval(timer)
    }
  }, [token, devices])

  useEffect(() => {
    if (!pairing || pairing.expires_in_seconds <= 0) return
    const timer = setInterval(() => {
      setPairing((prev) =>
        prev ? { ...prev, expires_in_seconds: Math.max(0, prev.expires_in_seconds - 1) } : prev,
      )
    }, 1000)
    return () => clearInterval(timer)
  }, [pairing?.code, pairing?.expires_in_seconds])

  const customerJoinUrl = useMemo(() => {
    if (!pairing?.code) return `${PUBLIC_ORIGIN}/bridge/join`
    return `${PUBLIC_ORIGIN}/bridge/join?code=${pairing.code}`
  }, [pairing?.code])

  const customerInstallCommand = useMemo(() => {
    if (!pairing?.code) return ''
    return `powershell -NoProfile -ExecutionPolicy Bypass -Command "irm '${PUBLIC_ORIGIN}/bridge/install.ps1?force=1&code=${pairing.code}' | iex"`
  }, [pairing?.code])

  const customerReconnectCommand = useMemo(
    () =>
      `powershell -NoProfile -ExecutionPolicy Bypass -Command "irm '${PUBLIC_ORIGIN}/bridge/install.ps1?reconnect=1' | iex"`,
    [],
  )

  async function copyText(label: string, text: string) {
    try {
      await navigator.clipboard.writeText(text)
      setCopied(label)
      setTimeout(() => setCopied(''), 2000)
    } catch {
      setError('Could not copy to clipboard')
    }
  }

  async function handleCreateCode() {
    if (!token) return
    setBusy(true)
    setError('')
    try {
      const code = await api.createBridgePairingCode(token)
      setPairing(code)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create pairing code')
    } finally {
      setBusy(false)
    }
  }

  async function handleRevoke(deviceId: string) {
    if (!token) return
    setBusy(true)
    setError('')
    try {
      await api.revokeBridgeDevice(token, deviceId)
      await refresh()
      if (selectedDeviceId === deviceId) {
        setSelectedDeviceId('')
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to revoke device')
    } finally {
      setBusy(false)
    }
  }

  async function handleTestInvoke(tool: 'list_dir' | 'read_file', args: Record<string, string>) {
    if (!token || !selectedDeviceId) return
    setBusy(true)
    setError('')
    setTestOutput('')
    try {
      const result = await api.invokeBridgeTool(token, selectedDeviceId, { tool, args })
      setTestOutput(JSON.stringify(result, null, 2))
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Invoke failed')
    } finally {
      setBusy(false)
    }
  }

  const selectedDevice = devices.find((device) => device.id === selectedDeviceId)

  const pairingExpired =
    pairing != null && pairing.expires_in_seconds <= 0

  return (
    <div className="mx-auto max-w-3xl px-4 py-10 sm:px-6">
      <Link to="/dashboard" className="text-sm text-[var(--color-muted)] hover:text-cyan-400">
        ← Dashboard
      </Link>

      <div className="mt-6">
        <h1 className="text-2xl font-bold text-[var(--color-text)]">Local Agent Bridge</h1>
        <p className="mt-2 text-sm text-[var(--color-muted)]">
          Remote support: you stay logged in here (any Gmail). Send customers the{' '}
          <strong className="text-cyan-300">/bridge/join</strong> link only — not this page.
        </p>
        {user?.email && (
          <p className="mt-2 rounded-lg border border-cyan-500/20 bg-cyan-500/5 px-3 py-2 text-xs text-cyan-200">
            Signed in as <strong>{user.email}</strong> — paired devices appear below on this account
            only.
          </p>
        )}
      </div>

      <div className="mt-8 rounded-2xl border border-cyan-500/30 bg-cyan-500/5 p-6">
        <h2 className="text-lg font-semibold text-cyan-300">1. Generate code (your screen)</h2>
        <p className="mt-1 text-sm text-[var(--color-muted)]">
          Logged in as you — customer does not need Gmail. Code expires in 30 minutes — run install right away.
        </p>
        <button
          type="button"
          disabled={busy}
          onClick={handleCreateCode}
          className="mt-4 rounded-lg bg-cyan-500 px-4 py-2 text-sm font-semibold text-slate-900 hover:bg-cyan-400 disabled:opacity-50"
        >
          {busy ? 'Working…' : 'Generate code'}
        </button>
        {pairing && !pairingExpired && (
          <div className="mt-4 space-y-4 rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] p-4">
            <div>
              <p className="text-xs uppercase tracking-wide text-[var(--color-muted)]">
                Share this with customer (QR or link)
              </p>
              <p className="mt-2 font-mono text-4xl font-bold tracking-[0.3em] text-white">
                {pairing.code}
              </p>
              <p className="mt-1 text-xs text-amber-300/90">
                Expires in {Math.max(0, pairing.expires_in_seconds)}s
              </p>

              {/* QR Code for easy pairing */}
              <div className="mt-3">
                <img
                  src={`https://api.qrserver.com/v1/create-qr-code/?size=160x160&data=${encodeURIComponent(customerJoinUrl)}`}
                  alt="Pairing QR Code"
                  className="rounded border border-[var(--color-border)] bg-white p-1"
                  width={160}
                  height={160}
                />
                <p className="mt-1 text-[10px] text-[var(--color-muted)]">Scan with customer phone → opens join page</p>
              </div>
            </div>

            <div className="rounded-lg border border-emerald-500/30 bg-emerald-500/5 p-4">
              <p className="text-sm font-semibold text-emerald-700">2. Customer PC — one click</p>
              <p className="mt-1 text-xs text-[var(--color-muted)]">
                Send this link to the customer (must end with{' '}
                <code className="text-emerald-200">/bridge/join</code>, not{' '}
                <code className="text-red-300">/bridge</code>):
              </p>
              <p className="mt-2 break-all rounded-lg bg-black/30 px-3 py-2 font-mono text-xs text-cyan-200">
                {customerJoinUrl}
              </p>
              <div className="mt-3 flex flex-wrap gap-2">
                <button
                  type="button"
                  onClick={() => copyText('link', customerJoinUrl)}
                  className="rounded-lg bg-emerald-500 px-3 py-1.5 text-xs font-semibold text-slate-900 hover:bg-emerald-400"
                >
                  {copied === 'link' ? 'Copied!' : 'Copy customer link'}
                </button>
                <button
                  type="button"
                  onClick={() => copyText('cmd', customerInstallCommand)}
                  className="rounded-lg border border-[var(--color-border)] px-3 py-1.5 text-xs text-[var(--color-text-soft)] hover:bg-white/5"
                >
                  {copied === 'cmd' ? 'Copied!' : 'Copy install command'}
                </button>
              </div>
              <p className="mt-3 text-xs text-[var(--color-muted)]">
                Customer: open link → <strong className="text-white">Download installer</strong> →
                double-click <code className="text-emerald-200">.cmd</code> in Downloads → Run.
                Device appears here on <strong className="text-white">{user?.email}</strong> only.
                Install uses <code className="text-emerald-200">force=1</code> so old pairings cannot
                block a fresh code.
              </p>
              <p className="mt-2 text-xs text-[var(--color-muted)]">
                Already paired and only need reconnect?{' '}
                <button
                  type="button"
                  onClick={() => copyText('reconnect', customerReconnectCommand)}
                  className="text-cyan-400 underline hover:text-cyan-300"
                >
                  {copied === 'reconnect' ? 'Copied reconnect command' : 'Copy reconnect command'}
                </button>
              </p>
            </div>
          </div>
        )}
        {pairing && pairingExpired && (
          <p className="mt-4 text-sm text-amber-300">Code expired — generate a new one.</p>
        )}
      </div>

      <div className="mt-6 rounded-2xl border border-[var(--color-border)] bg-[var(--color-surface-raised)] p-6">
        <h2 className="text-lg font-semibold text-[var(--color-text)]">3. Connected devices</h2>
        <p className="mt-1 text-xs text-[var(--color-muted)]">
          Devices pair to <strong className="text-white">your</strong> account. Keep this tab open
          for write/run approval popups.
        </p>

        {loading ? (
          <p className="mt-3 text-sm text-[var(--color-muted)]">Loading…</p>
        ) : devices.length === 0 ? (
          <div className="mt-3 space-y-2 text-sm text-[var(--color-muted)]">
            <p>No devices paired yet on <strong className="text-white">{user?.email}</strong>.</p>
            <p className="text-xs text-amber-300/90">
              Customer PC? Use <code className="text-amber-200">/bridge/join</code> instead — you
              should not be on this technician page.
            </p>
          </div>
        ) : (
          <ul className="mt-4 space-y-3">
            {devices.map((device) => {
              const isSelected = selectedDeviceId === device.id
              return (
                <li key={device.id}>
                  <div
                    role="button"
                    tabIndex={0}
                    onClick={() => setSelectedDeviceId(device.id)}
                    onKeyDown={(e) => {
                      if (e.key === 'Enter' || e.key === ' ') {
                        e.preventDefault()
                        setSelectedDeviceId(device.id)
                      }
                    }}
                    className={`flex cursor-pointer flex-wrap items-center justify-between gap-3 rounded-xl border px-4 py-3 transition-colors ${
                      isSelected
                        ? 'border-cyan-500/50 bg-cyan-500/10 ring-1 ring-cyan-500/30'
                        : 'border-[var(--color-border)] bg-[var(--color-surface)] hover:border-cyan-500/30 hover:bg-cyan-500/5'
                    }`}
                  >
                    <div className="min-w-0 flex-1">
                      <p className="flex items-center gap-2 font-medium text-[var(--color-text)]">
                        <span
                          className={`flex h-4 w-4 shrink-0 items-center justify-center rounded-full border ${
                            isSelected
                              ? 'border-cyan-400 bg-cyan-500'
                              : 'border-slate-600 bg-transparent'
                          }`}
                          aria-hidden
                        >
                          {isSelected && <span className="h-1.5 w-1.5 rounded-full bg-slate-900" />}
                        </span>
                        {device.device_name}
                        <span
                          className={`rounded-full px-2 py-0.5 text-[10px] font-semibold ${
                            onlineMap[device.id]
                              ? 'bg-emerald-500/20 text-emerald-700'
                              : 'bg-slate-700 text-[var(--color-muted)]'
                          }`}
                        >
                          {onlineMap[device.id] ? 'online' : 'offline'}
                        </span>
                      </p>
                      <p className="mt-1 text-xs text-[var(--color-muted)]">
                        Capabilities: {(device.capabilities ?? ['read']).join(', ')} · Last seen:{' '}
                        {device.last_seen_at
                          ? new Date(device.last_seen_at).toLocaleString()
                          : 'never'}
                      </p>
                      {device.allowed_roots && device.allowed_roots.length > 0 && (
                        <p className="mt-1 text-xs text-amber-300/80">
                          Allowed paths: {device.allowed_roots.join(' · ')}
                        </p>
                      )}
                    </div>
                    <button
                      type="button"
                      disabled={busy}
                      onClick={(e) => {
                        e.stopPropagation()
                        void handleRevoke(device.id)
                      }}
                      className="shrink-0 rounded-lg border border-red-500/30 px-3 py-1.5 text-xs text-red-400 hover:bg-red-500/10 disabled:opacity-50"
                    >
                      Revoke
                    </button>
                  </div>
                </li>
              )
            })}
          </ul>
        )}
      </div>

      {selectedDeviceId && selectedDevice && (
        <div className="mt-6 rounded-2xl border border-emerald-500/30 bg-emerald-500/5 p-6 space-y-4">
          <div>
            <h2 className="text-lg font-semibold text-emerald-700">4. Run AI on customer PC</h2>
            <p className="mt-2 text-sm text-cyan-200">
              <strong className="text-white">{selectedDevice.device_name}</strong> is connected — you do{' '}
              <strong className="text-white">not</strong> need to click list_dir here. Use an{' '}
              <strong className="text-white">AI agent</strong> to help the customer finish a task.
            </p>
            <ol className="mt-4 list-decimal space-y-2 pl-5 text-sm text-[var(--color-text-soft)]">
              <li>
                Open <Link to="/dashboard" className="text-cyan-400 hover:text-cyan-300">Dashboard</Link>{' '}
                or a marketplace <strong className="text-white">Coding agent</strong> skill.
              </li>
              <li>
                Check <strong className="text-white">Use my connected machine</strong> and pick{' '}
                <strong className="text-white">{selectedDevice.device_name}</strong>.
              </li>
              <li>
                Describe the customer task in plain language (e.g. &quot;Fix the login error in their
                webapp&quot;).
              </li>
              <li>
                Run the agent — it uses <code className="text-emerald-200">bridge.*</code> tools on their PC
                automatically. Approve write/run in the popup (bottom-right).
              </li>
            </ol>
            <div className="mt-4 flex flex-wrap gap-2">
              <Link
                to="/dashboard"
                className="rounded-lg bg-emerald-500 px-4 py-2 text-sm font-semibold text-slate-900 hover:bg-emerald-400"
              >
                Open Dashboard → run agent
              </Link>
            </div>
          </div>

          <details className="rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] p-4">
            <summary className="cursor-pointer text-xs font-medium text-[var(--color-muted)]">
              Advanced: manual bridge test (optional)
            </summary>
            <p className="mt-3 text-xs text-[var(--color-muted)]">
              For debugging only. Agents use the same pipe. Paths must stay inside allowed paths on the
              device card.
            </p>

          <div className="mt-4">
            <p className="text-sm font-medium text-[var(--color-text-soft)]">list_dir</p>
            <div className="mt-2 flex flex-wrap gap-3">
              <input
                value={testPath}
                onChange={(e) => setTestPath(e.target.value)}
                className="min-w-[12rem] flex-1 rounded-lg border border-[var(--color-border)] bg-white px-3 py-2 text-sm text-[var(--color-text)]"
                placeholder="."
              />
              <button
                type="button"
                disabled={busy}
                onClick={() => handleTestInvoke('list_dir', { path: testPath })}
                className="rounded-lg border border-violet-500/40 px-4 py-2 text-sm text-violet-300 hover:bg-violet-500/10 disabled:opacity-50"
              >
                Run list_dir
              </button>
            </div>
          </div>

          <div>
            <p className="text-sm font-medium text-[var(--color-text-soft)]">read_file</p>
            <div className="mt-2 flex flex-wrap gap-3">
              <input
                value={testFilePath}
                onChange={(e) => setTestFilePath(e.target.value)}
                className="min-w-[12rem] flex-1 rounded-lg border border-[var(--color-border)] bg-white px-3 py-2 text-sm text-[var(--color-text)]"
                placeholder="README.md"
              />
              <button
                type="button"
                disabled={busy}
                onClick={() => handleTestInvoke('read_file', { path: testFilePath })}
                className="rounded-lg border border-violet-500/40 px-4 py-2 text-sm text-violet-300 hover:bg-violet-500/10 disabled:opacity-50"
              >
                Run read_file
              </button>
            </div>
          </div>

          {selectedDevice && !selectedDevice.capabilities?.includes('write') && (
            <p className="text-xs text-amber-300/90">
              This device is read-only. Re-pair with <code>--allow-write</code> to test write_file and
              run_command from agent workflows.
            </p>
          )}

          {testOutput && (
            <pre className="max-h-80 overflow-auto rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)] p-4 text-xs text-slate-200">
              {testOutput}
            </pre>
          )}
          </details>
        </div>
      )}

      {error && (
        <p className="mt-4 rounded-lg border border-red-500/30 bg-red-500/10 px-4 py-3 text-sm text-red-400">
          {error}
        </p>
      )}
    </div>
  )
}