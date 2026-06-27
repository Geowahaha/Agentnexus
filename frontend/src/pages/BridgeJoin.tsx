import { useMemo, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

function normalizeCode(raw: string): string {
  return raw.replace(/\D/g, '').slice(0, 6)
}

export function BridgeJoin() {
  const { user } = useAuth()
  const [params] = useSearchParams()
  const initialCode = normalizeCode(params.get('code') ?? '')
  const solutionContext = params.get('solution') || params.get('skill') || ''
  const [code, setCode] = useState(initialCode)
  const [copied, setCopied] = useState('')
  const [error, setError] = useState('')
  const [installStep, setInstallStep] = useState(0)

  const origin = typeof window !== 'undefined' ? window.location.origin : 'https://obolla.com'
  const validCode = code.length === 6

  const installCommand = useMemo(() => {
    if (!validCode) return ''
    const sol = solutionContext ? `&solution=${encodeURIComponent(solutionContext)}` : ''
    return `powershell -NoProfile -ExecutionPolicy Bypass -Command "irm '${origin}/bridge/install.ps1?code=${code}${sol}' | iex"`
  }, [origin, code, validCode, solutionContext])

  const cmdDownloadUrl = validCode ? `${origin}/bridge/install.cmd?code=${code}${solutionContext ? `&solution=${encodeURIComponent(solutionContext)}` : ''}` : ''

  async function copyText(label: string, text: string) {
    try {
      await navigator.clipboard.writeText(text)
      setCopied(label)
      setTimeout(() => setCopied(''), 2000)
    } catch {
      setError('Could not copy — select and copy manually.')
    }
  }

  function handleAutoInstall() {
    setError('')
    if (!validCode) {
      setError('Enter the 6-digit code from your support agent.')
      return
    }
    const link = document.createElement('a')
    link.href = cmdDownloadUrl
    link.download = 'Install-AgentNexus-Bridge.cmd'
    link.click()
    setInstallStep(1)
  }

  return (
    <div className="mx-auto max-w-lg px-4 py-10 sm:px-6">
      <div className="text-center">
        <p className="text-xs font-semibold uppercase tracking-widest text-cyan-400">
          Customer setup
        </p>
        <h1 className="mt-3 text-2xl font-bold text-[var(--color-text)]">Connect this PC</h1>
        <p className="mt-2 text-sm text-[var(--color-muted)]">
          <strong className="text-white">No login required.</strong> Enter the code, install, done.
        </p>
        {solutionContext && (
          <p className="mt-2 text-xs text-emerald-400">
            This will connect your machine to the <strong>{solutionContext}</strong> solution immediately.
          </p>
        )}
      </div>

      {user && (
        <div className="mt-6 rounded-xl border border-amber-500/40 bg-amber-500/10 px-4 py-3 text-sm text-amber-200">
          Logged in as <strong>{user.email}</strong> — ignore this. Stay on this page; do not open{' '}
          <code className="text-amber-100">/bridge</code>.
        </div>
      )}

      <div className="mt-8 rounded-2xl border border-cyan-500/30 bg-cyan-500/5 p-6">
        <label className="text-xs font-semibold uppercase tracking-wide text-[var(--color-muted)]">
          Pairing code from your agent
        </label>
        <input
          type="text"
          inputMode="numeric"
          autoComplete="one-time-code"
          maxLength={6}
          value={code}
          onChange={(e) => {
            setCode(normalizeCode(e.target.value))
            setInstallStep(0)
          }}
          placeholder="000000"
          className="mt-3 w-full rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] px-4 py-4 text-center font-mono text-3xl font-bold tracking-[0.35em] text-white"
        />

        <button
          type="button"
          onClick={handleAutoInstall}
          disabled={!validCode}
          className="mt-6 w-full rounded-xl bg-cyan-500 py-4 text-base font-bold text-slate-900 hover:bg-cyan-400 disabled:cursor-not-allowed disabled:opacity-40"
        >
          1. Download installer
        </button>

        {installStep >= 1 && (
          <div className="mt-4 rounded-xl border border-emerald-500/40 bg-emerald-500/10 p-4 text-sm text-emerald-100">
            <p className="font-semibold text-emerald-700">2. Run the installer</p>
            <ol className="mt-2 list-decimal space-y-1 pl-4 text-xs text-emerald-100/90">
              <li>Open your <strong>Downloads</strong> folder</li>
              <li>Double-click <strong>Install-AgentNexus-Bridge.cmd</strong></li>
              <li>If Windows asks, click <strong>Run</strong> / <strong>Yes</strong></li>
              <li>
                <strong>Do not close</strong> the black window — wait for <strong>SUCCESS</strong>{' '}
                (1–3 min first time)
              </li>
              <li>If it fails, send the log path to your agent</li>
            </ol>
            <p className="mt-2 text-[10px] text-[var(--color-muted)]">
              If it fails, your agent can open the log file (not the folder): Win+R → paste{' '}
              <code className="text-[var(--color-text-soft)]">%LOCALAPPDATA%\AgentNexus\bridge-install.log</code>
            </p>
            <p className="mt-3 text-xs text-amber-200">
              Remote support? Your agent can double-click the file for you via AnyDesk.
            </p>
          </div>
        )}

        {validCode && (
          <button
            type="button"
            onClick={() => copyText('command', installCommand)}
            className="mt-4 w-full rounded-lg border border-[var(--color-border)] px-4 py-2 text-xs text-[var(--color-text-soft)] hover:bg-white/5"
          >
            {copied === 'command' ? 'Copied!' : 'Or copy PowerShell command (advanced)'}
          </button>
        )}
      </div>

      <div className="mt-6 rounded-xl border border-[var(--color-border)] bg-[var(--color-surface-raised)] p-4 text-xs text-[var(--color-muted)]">
        <p className="font-medium text-[var(--color-text-soft)]">You will NOT see devices here</p>
        <p className="mt-2">
          The PC pairs to your <strong>agent&apos;s</strong> account. Only they see it on their
          technician screen. Close the browser when install finishes.
        </p>
      </div>

      {error && (
        <p className="mt-4 rounded-lg border border-red-500/30 bg-red-500/10 px-4 py-3 text-sm text-red-400">
          {error}
        </p>
      )}
    </div>
  )
}