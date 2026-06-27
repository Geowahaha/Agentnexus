import { DurableObject } from 'cloudflare:workers'
import {
  BRIDGE_CONSENT_TOOLS,
  type BridgeClientMessage,
  type BridgeConsentRequest,
  type BridgeDispatchResponse,
  type BridgeServerMessage,
  type BridgeToolName,
} from './bridge-types'

type PendingCall = {
  resolve: (value: BridgeDispatchResponse) => void
  reject: (error: Error) => void
  timer: ReturnType<typeof setTimeout>
}

type ConsentPending = {
  request_id: string
  device_id: string
  tool: BridgeToolName
  args: Record<string, unknown>
  created_at: number
  settle: (approved: boolean) => void
  reject: (reason: Error) => void
  timer: ReturnType<typeof setTimeout>
}

const CONSENT_WAIT_MS = 120_000
const DEVICE_PING_MS = 45_000

export class BridgeHub extends DurableObject {
  private deviceSockets = new Map<string, WebSocket>()
  private pending = new Map<string, PendingCall>()
  private consentWatchers = new Set<WebSocket>()
  private consentPending = new Map<string, ConsentPending>()

  async fetch(request: Request): Promise<Response> {
    const url = new URL(request.url)

    if (url.pathname === '/dispatch' && request.method === 'POST') {
      const body = (await request.json()) as {
        device_id: string
        tool: BridgeToolName
        args: Record<string, unknown>
        timeout_ms?: number
      }
      const result = await this.dispatchToolCall(
        body.device_id,
        body.tool,
        body.args,
        body.timeout_ms ?? 30_000,
      )
      return Response.json(result)
    }

    if (url.pathname === '/status' && request.method === 'GET') {
      const deviceId = url.searchParams.get('device_id')
      if (!deviceId) {
        return Response.json({ online: false }, { status: 400 })
      }
      const ws = this.deviceSockets.get(deviceId)
      return Response.json({ online: Boolean(ws && ws.readyState === WebSocket.OPEN) })
    }

    if (url.pathname === '/consent/pending' && request.method === 'GET') {
      const userId = url.searchParams.get('user_id')
      if (!userId) {
        return Response.json({ items: [] }, { status: 400 })
      }
      return Response.json({ items: this.listConsentPending() })
    }

    if (url.pathname === '/consent/respond' && request.method === 'POST') {
      const body = (await request.json()) as {
        user_id: string
        request_id: string
        approved: boolean
      }
      const settled = this.respondConsent(body.request_id, body.approved)
      if (!settled) {
        return Response.json({ detail: 'Consent request not found' }, { status: 404 })
      }
      return Response.json({ ok: true })
    }

    if (url.pathname === '/consent/ws') {
      if (request.headers.get('Upgrade') !== 'websocket') {
        return new Response('Expected WebSocket', { status: 426 })
      }
      const pair = new WebSocketPair()
      const [client, server] = Object.values(pair)
      this.ctx.acceptWebSocket(server)
      this.consentWatchers.add(server)
      server.send(JSON.stringify({ type: 'consent_sync', items: this.listConsentPending() }))
      return new Response(null, { status: 101, webSocket: client })
    }

    if (request.headers.get('Upgrade') !== 'websocket') {
      return new Response('Expected WebSocket', { status: 426 })
    }

    const deviceId = url.searchParams.get('device_id')
    if (!deviceId) {
      return new Response('device_id required', { status: 400 })
    }

    const pair = new WebSocketPair()
    const [client, server] = Object.values(pair)
    this.ctx.acceptWebSocket(server)
    this.deviceSockets.set(deviceId, server)

    const welcome: BridgeServerMessage = { type: 'welcome', device_id: deviceId }
    server.send(JSON.stringify(welcome))
    this.scheduleDevicePing(server)

    return new Response(null, { status: 101, webSocket: client })
  }

  async webSocketClose(ws: WebSocket): Promise<void> {
    this.consentWatchers.delete(ws)
    for (const [deviceId, socket] of this.deviceSockets.entries()) {
      if (socket === ws) {
        this.deviceSockets.delete(deviceId)
      }
    }
    ws.close(1000, 'closed')
  }

  async webSocketMessage(ws: WebSocket, message: string | ArrayBuffer): Promise<void> {
    const text = typeof message === 'string' ? message : new TextDecoder().decode(message)
    let parsed: BridgeClientMessage
    try {
      parsed = JSON.parse(text) as BridgeClientMessage
    } catch {
      return
    }

    if (parsed.type === 'tool_result') {
      const pending = this.pending.get(parsed.request_id)
      if (!pending) return
      clearTimeout(pending.timer)
      this.pending.delete(parsed.request_id)
      pending.resolve({
        ok: parsed.ok,
        result: parsed.result,
        error: parsed.error,
      })
      return
    }

    if (parsed.type === 'hello') {
      this.deviceSockets.set(parsed.device_id, ws)
    }
  }

  private listConsentPending(): BridgeConsentRequest[] {
    return [...this.consentPending.values()].map((item) => ({
      request_id: item.request_id,
      device_id: item.device_id,
      tool: item.tool,
      args: item.args,
      created_at: new Date(item.created_at).toISOString(),
    }))
  }

  private scheduleDevicePing(ws: WebSocket) {
    const timer = setInterval(() => {
      if (ws.readyState !== WebSocket.OPEN) {
        clearInterval(timer)
        return
      }
      try {
        const ping: BridgeServerMessage = { type: 'ping' }
        ws.send(JSON.stringify(ping))
      } catch {
        clearInterval(timer)
      }
    }, DEVICE_PING_MS)
  }

  private broadcastConsent(event: Record<string, unknown>) {
    const payload = JSON.stringify(event)
    for (const watcher of this.consentWatchers) {
      if (watcher.readyState === WebSocket.OPEN) {
        try {
          watcher.send(payload)
        } catch {
          this.consentWatchers.delete(watcher)
        }
      }
    }
  }

  private respondConsent(requestId: string, approved: boolean): boolean {
    const pending = this.consentPending.get(requestId)
    if (!pending) return false
    clearTimeout(pending.timer)
    this.consentPending.delete(requestId)
    pending.settle(approved)
    this.broadcastConsent({ type: 'consent_resolved', request_id: requestId, approved })
    return true
  }

  private waitForWebConsent(
    requestId: string,
    deviceId: string,
    tool: BridgeToolName,
    args: Record<string, unknown>,
  ): Promise<boolean> {
    return new Promise((resolve, reject) => {
      const timer = setTimeout(() => {
        const pending = this.consentPending.get(requestId)
        if (!pending) return
        this.consentPending.delete(requestId)
        this.broadcastConsent({
          type: 'consent_expired',
          request_id: requestId,
          device_id: deviceId,
          tool,
          created_at: new Date().toISOString(),
        })
        pending.reject(new Error('consent_expired'))
      }, CONSENT_WAIT_MS)

      this.consentPending.set(requestId, {
        request_id: requestId,
        device_id: deviceId,
        tool,
        args,
        created_at: Date.now(),
        timer,
        settle: resolve,
        reject,
      })

      this.broadcastConsent({
        type: 'consent_request',
        request_id: requestId,
        device_id: deviceId,
        tool,
        args,
        created_at: new Date().toISOString(),
      })
    })
  }

  private async dispatchToolCall(
    deviceId: string,
    tool: BridgeToolName,
    args: Record<string, unknown>,
    timeoutMs: number,
  ): Promise<BridgeDispatchResponse> {
    const ws = this.deviceSockets.get(deviceId)
    if (!ws || ws.readyState !== WebSocket.OPEN) {
      return { ok: false, error: 'device_offline' }
    }

    const requestId = crypto.randomUUID()
    let preApproved = false

    if (BRIDGE_CONSENT_TOOLS.has(tool) && this.consentWatchers.size > 0) {
      try {
        const decision = await this.waitForWebConsent(requestId, deviceId, tool, args)
        if (!decision) {
          return { ok: false, error: 'consent_denied' }
        }
        preApproved = true
      } catch (err) {
        const message = err instanceof Error ? err.message : 'consent_failed'
        if (message === 'consent_expired') {
          return { ok: false, error: 'consent_expired' }
        }
        return { ok: false, error: 'consent_failed' }
      }
    }

    const payload: BridgeServerMessage = {
      type: 'tool_call',
      request_id: requestId,
      tool,
      args,
      ...(preApproved ? { pre_approved: true } : {}),
    }

    return new Promise((resolve) => {
      const timer = setTimeout(() => {
        this.pending.delete(requestId)
        resolve({ ok: false, error: 'bridge_timeout' })
      }, timeoutMs)

      this.pending.set(requestId, {
        resolve,
        reject: () => undefined,
        timer,
      })

      try {
        ws.send(JSON.stringify(payload))
      } catch {
        clearTimeout(timer)
        this.pending.delete(requestId)
        resolve({ ok: false, error: 'bridge_send_failed' })
      }
    })
  }
}