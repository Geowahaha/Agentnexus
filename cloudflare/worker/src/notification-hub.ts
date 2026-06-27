import { DurableObject } from 'cloudflare:workers'
import type { NotificationRecord, WsServerMessage } from './notification-types'

export class NotificationHub extends DurableObject {
  async fetch(request: Request): Promise<Response> {
    const url = new URL(request.url)

    if (url.pathname === '/broadcast' && request.method === 'POST') {
      const notification = (await request.json()) as NotificationRecord
      await this.pushToClients(notification)
      return Response.json({ ok: true })
    }

    if (request.headers.get('Upgrade') !== 'websocket') {
      return new Response('Expected WebSocket', { status: 426 })
    }

    const pair = new WebSocketPair()
    const [client, server] = Object.values(pair)
    this.ctx.acceptWebSocket(server)

    const welcome: WsServerMessage = { type: 'connected' }
    server.send(JSON.stringify(welcome))

    return new Response(null, { status: 101, webSocket: client })
  }

  async webSocketClose(ws: WebSocket): Promise<void> {
    ws.close(1000, 'closed')
  }

  async pushToClients(notification: NotificationRecord): Promise<void> {
    const message: WsServerMessage = { type: 'notification', notification }
    const payload = JSON.stringify(message)
    for (const ws of this.ctx.getWebSockets()) {
      try {
        ws.send(payload)
      } catch {
        ws.close(1011, 'send failed')
      }
    }
  }

  async pushBadge(unreadCount: number): Promise<void> {
    const message: WsServerMessage = { type: 'badge', unread_count: unreadCount }
    const payload = JSON.stringify(message)
    for (const ws of this.ctx.getWebSockets()) {
      try {
        ws.send(payload)
      } catch {
        ws.close(1011, 'send failed')
      }
    }
  }
}