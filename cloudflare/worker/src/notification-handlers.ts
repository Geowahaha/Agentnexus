import { getUnreadCount, insertNotification, listNotifications, markNotificationsRead } from './notification-db'
import type { NotificationHub } from './notification-hub'
import type { NotifyQueueMessage } from './notification-types'

export interface NotificationEnv {
  NOTIFICATIONS_DB: D1Database
  NOTIFICATION_HUB: DurableObjectNamespace<NotificationHub>
  NOTIFY_QUEUE: Queue<NotifyQueueMessage>
  BACKEND_URL: string
  INTERNAL_NOTIFY_SECRET: string
}

async function resolveUserId(request: Request, env: NotificationEnv): Promise<string | null> {
  const auth = request.headers.get('Authorization')
  if (!auth?.startsWith('Bearer ')) return null

  const backendBase = (env.BACKEND_URL || 'http://127.0.0.1:8000').replace(/\/$/, '')
  const response = await fetch(`${backendBase}/api/v1/auth/me`, {
    headers: { Authorization: auth },
  })
  if (!response.ok) return null
  const user = (await response.json()) as { id: string }
  return user.id ?? null
}

function corsHeaders(origin: string | null): HeadersInit {
  const headers: Record<string, string> = {
    'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
    'Access-Control-Allow-Headers': 'Authorization, Content-Type',
  }
  if (origin) {
    headers['Access-Control-Allow-Origin'] = origin
    headers['Access-Control-Allow-Credentials'] = 'true'
  }
  return headers
}

export async function handleNotificationRequest(
  request: Request,
  env: NotificationEnv,
): Promise<Response | null> {
  const url = new URL(request.url)
  const origin = request.headers.get('Origin')

  if (!url.pathname.startsWith('/api/v1/notifications')) {
    return null
  }

  if (request.method === 'OPTIONS') {
    return new Response(null, { status: 204, headers: corsHeaders(origin) })
  }

  if (url.pathname === '/api/v1/notifications/ws') {
    const token = url.searchParams.get('token')
    const userId = token
      ? await resolveUserId(
          new Request(request.url, { headers: { Authorization: `Bearer ${token}` } }),
          env,
        )
      : await resolveUserId(request, env)

    if (!userId) {
      return new Response('Unauthorized', { status: 401 })
    }

    const hubId = env.NOTIFICATION_HUB.idFromName(userId)
    const hub = env.NOTIFICATION_HUB.get(hubId)
    return hub.fetch(new Request('https://hub/ws', { headers: request.headers }))
  }

  const userId = await resolveUserId(request, env)
  if (!userId) {
    return Response.json({ detail: 'Unauthorized' }, { status: 401, headers: corsHeaders(origin) })
  }

  if (url.pathname === '/api/v1/notifications/badge' && request.method === 'GET') {
    const unread_count = await getUnreadCount(env.NOTIFICATIONS_DB, userId)
    return Response.json({ unread_count }, { headers: corsHeaders(origin) })
  }

  if (url.pathname === '/api/v1/notifications' && request.method === 'GET') {
    const limit = Number(url.searchParams.get('limit') ?? '30')
    const items = await listNotifications(env.NOTIFICATIONS_DB, userId, limit)
    const unread_count = await getUnreadCount(env.NOTIFICATIONS_DB, userId)
    return Response.json({ items, unread_count }, { headers: corsHeaders(origin) })
  }

  if (url.pathname === '/api/v1/notifications/mark-read' && request.method === 'POST') {
    const body = (await request.json()) as { ids?: string[] }
    const unread_count = await markNotificationsRead(env.NOTIFICATIONS_DB, userId, body.ids ?? [])
    const hub = env.NOTIFICATION_HUB.get(env.NOTIFICATION_HUB.idFromName(userId))
    await hub.pushBadge(unread_count)
    return Response.json({ unread_count }, { headers: corsHeaders(origin) })
  }

  return Response.json({ detail: 'Not found' }, { status: 404, headers: corsHeaders(origin) })
}

export async function handleInternalPublish(
  request: Request,
  env: NotificationEnv,
): Promise<Response> {
  const secret = request.headers.get('X-Notify-Secret')
  if (!secret || secret !== env.INTERNAL_NOTIFY_SECRET) {
    return Response.json({ detail: 'Forbidden' }, { status: 403 })
  }

  const body = (await request.json()) as Omit<NotifyQueueMessage, 'id'> & { id?: string }
  const message: NotifyQueueMessage = {
    id: body.id ?? crypto.randomUUID(),
    user_id: body.user_id,
    event_type: body.event_type,
    title: body.title,
    body: body.body,
    payload: body.payload ?? {},
  }

  await env.NOTIFY_QUEUE.send(message)
  return Response.json({ ok: true, queued: message.id })
}

export async function processNotificationBatch(
  messages: NotifyQueueMessage[],
  env: NotificationEnv,
): Promise<void> {
  for (const message of messages) {
    const record = await insertNotification(env.NOTIFICATIONS_DB, message)
    const hub = env.NOTIFICATION_HUB.get(env.NOTIFICATION_HUB.idFromName(message.user_id))
    await hub.pushToClients(record)
    const unread = await getUnreadCount(env.NOTIFICATIONS_DB, message.user_id)
    await hub.pushBadge(unread)
  }
}