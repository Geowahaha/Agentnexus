import { useCallback, useEffect, useRef, useState } from 'react'
import { api, ApiError } from '../api/client'
import { useAuth } from '../context/AuthContext'
import type { BridgeConsentRequest } from '../types'

function consentWsUrl(token: string): string {
  const apiBase = import.meta.env.VITE_API_BASE ?? '/api/v1'
  if (apiBase.startsWith('http')) {
    const url = new URL(apiBase)
    url.protocol = url.protocol === 'https:' ? 'wss:' : 'ws:'
    url.pathname = '/api/v1/bridge/consent/ws'
    return url.toString()
  }
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
  return `${protocol}//${window.location.host}/api/v1/bridge/consent/ws?token=${encodeURIComponent(token)}`
}

export function BridgeConsentQueue() {
  const { token, user, loading, logout } = useAuth()
  const [items, setItems] = useState<BridgeConsentRequest[]>([])
  const [busyId, setBusyId] = useState<string | null>(null)
  const [error, setError] = useState('')
  const sessionActive = Boolean(token && user && !loading)

  const refresh = useCallback(async () => {
    if (!sessionActive || !token) {
      setItems([])
      return false
    }
    try {
      const pending = await api.listBridgeConsentPending(token)
      setItems(pending.items)
      return true
    } catch (err) {
      setItems([])
      if (err instanceof ApiError && (err.status === 401 || err.status === 403)) {
        logout()
        return false
      }
      return true
    }
  }, [sessionActive, token, logout])

  const refreshRef = useRef(refresh)
  refreshRef.current = refresh

  useEffect(() => {
    if (!sessionActive) {
      setItems([])
      return
    }
    let cancelled = false
    let timer: ReturnType<typeof setInterval> | undefined

    void refreshRef.current().then((keepPolling) => {
      if (cancelled || !keepPolling) return
      timer = setInterval(() => {
        void refreshRef.current().then((ok) => {
          if (!ok && timer) clearInterval(timer)
        })
      }, 5000)
    })

    return () => {
      cancelled = true
      if (timer) clearInterval(timer)
    }
  }, [sessionActive])

  useEffect(() => {
    if (!sessionActive || !token) return
    const ws = new WebSocket(consentWsUrl(token))
    ws.onmessage = (event) => {
      try {
        const message = JSON.parse(String(event.data)) as {
          type: string
          items?: BridgeConsentRequest[]
          request_id?: string
          device_id?: string
          tool?: string
          args?: Record<string, unknown>
          created_at?: string
          approved?: boolean
        }
        if (message.type === 'consent_sync' && message.items) {
          setItems(message.items)
          return
        }
        if (message.type === 'consent_request' && message.request_id && message.tool) {
          setItems((prev) => {
            if (prev.some((item) => item.request_id === message.request_id)) return prev
            return [
              ...prev,
              {
                request_id: message.request_id!,
                device_id: message.device_id ?? '',
                tool: message.tool!,
                args: message.args ?? {},
                created_at: message.created_at ?? new Date().toISOString(),
              },
            ]
          })
          return
        }
        if (message.type === 'consent_resolved' && message.request_id) {
          setItems((prev) => prev.filter((item) => item.request_id !== message.request_id))
          return
        }
        if (message.type === 'consent_expired' && message.request_id) {
          setItems((prev) => prev.filter((item) => item.request_id !== message.request_id))
          setError('Consent request expired — retry the action if needed.')
        }
      } catch {
        // ignore malformed events
      }
    }
    return () => ws.close()
  }, [sessionActive, token])

  async function respond(requestId: string, approved: boolean) {
    if (!token) return
    setBusyId(requestId)
    setError('')
    try {
      await api.respondBridgeConsent(token, requestId, approved)
      setItems((prev) => prev.filter((item) => item.request_id !== requestId))
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to respond')
    } finally {
      setBusyId(null)
    }
  }

  if (!sessionActive || items.length === 0) return null

  return (
    <div className="fixed bottom-4 right-4 z-[60] flex max-w-md flex-col gap-3">
      {items.map((item) => (
        <div
          key={item.request_id}
          className="rounded-2xl border border-amber-500/40 bg-slate-900/95 p-4 shadow-2xl shadow-amber-500/10 backdrop-blur"
        >
          <p className="text-xs font-semibold uppercase tracking-wide text-amber-300">
            Local action approval
          </p>
          <p className="mt-2 text-sm text-white">
            Agent requests <code className="text-amber-200">{item.tool}</code> on your machine
          </p>
          <pre className="mt-2 max-h-28 overflow-auto rounded-lg border border-slate-700 bg-slate-950 p-2 text-[11px] text-[var(--color-text-soft)]">
            {JSON.stringify(item.args, null, 2)}
          </pre>
          <div className="mt-3 flex gap-2">
            <button
              type="button"
              disabled={busyId === item.request_id}
              onClick={() => respond(item.request_id, true)}
              className="rounded-lg bg-emerald-500 px-3 py-1.5 text-xs font-semibold text-slate-900 hover:bg-emerald-400 disabled:opacity-50"
            >
              Approve
            </button>
            <button
              type="button"
              disabled={busyId === item.request_id}
              onClick={() => respond(item.request_id, false)}
              className="rounded-lg border border-red-500/40 px-3 py-1.5 text-xs text-red-300 hover:bg-red-500/10 disabled:opacity-50"
            >
              Deny
            </button>
          </div>
        </div>
      ))}
      {error && <p className="text-xs text-red-400">{error}</p>}
    </div>
  )
}