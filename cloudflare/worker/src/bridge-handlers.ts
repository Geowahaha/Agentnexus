import type { BridgeHub } from './bridge-hub'
import type { BridgeDispatchRequest, BridgeEnv, BridgeToolName } from './bridge-types'

const BRIDGE_READ_TOOLS = new Set<BridgeToolName>(['list_dir', 'read_file'])
const BRIDGE_WRITE_TOOLS = new Set<BridgeToolName>(['write_file'])
const BRIDGE_EXEC_TOOLS = new Set<BridgeToolName>(['run_command'])
const BRIDGE_ALLOWED_TOOLS = new Set<BridgeToolName>([
  ...BRIDGE_READ_TOOLS,
  ...BRIDGE_WRITE_TOOLS,
  ...BRIDGE_EXEC_TOOLS,
])

type BridgeDeviceRecord = {
  id: string
  capabilities?: string[]
}

function bridgeCapabilityError(capabilities: string[] | undefined, tool: BridgeToolName): string | null {
  const caps = new Set(capabilities ?? ['read'])
  if (BRIDGE_READ_TOOLS.has(tool) && (caps.has('read') || caps.has('write') || caps.has('execute'))) {
    return null
  }
  if (BRIDGE_WRITE_TOOLS.has(tool) && caps.has('write')) return null
  if (BRIDGE_EXEC_TOOLS.has(tool) && caps.has('execute')) return null
  return `Device does not have permission for '${tool}'`
}

async function resolveUserId(request: Request, env: BridgeEnv): Promise<string | null> {
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

async function validateDeviceToken(
  deviceToken: string,
  env: BridgeEnv,
): Promise<{ device_id: string; user_id: string; device_name: string } | null> {
  const backendBase = (env.BACKEND_URL || 'http://127.0.0.1:8000').replace(/\/$/, '')
  const response = await fetch(`${backendBase}/api/v1/bridge/device-session`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-Bridge-Secret': env.INTERNAL_BRIDGE_SECRET || (env as { INTERNAL_NOTIFY_SECRET?: string }).INTERNAL_NOTIFY_SECRET || '',
    },
    body: JSON.stringify({ device_token: deviceToken }),
  })
  if (!response.ok) return null
  return (await response.json()) as { device_id: string; user_id: string; device_name: string }
}

export async function handleBridgeRequest(
  request: Request,
  env: BridgeEnv,
): Promise<Response | null> {
  const url = new URL(request.url)
  const origin = request.headers.get('Origin')

  if (!url.pathname.startsWith('/api/v1/bridge')) {
    return null
  }

  if (request.method === 'OPTIONS') {
    return new Response(null, { status: 204, headers: corsHeaders(origin) })
  }

  if (url.pathname === '/api/v1/bridge/consent/pending' && request.method === 'GET') {
    const userId = await resolveUserId(request, env)
    if (!userId) {
      return Response.json({ detail: 'Unauthorized' }, { status: 401, headers: corsHeaders(origin) })
    }
    const hubId = env.BRIDGE_HUB.idFromName(userId)
    const hub = env.BRIDGE_HUB.get(hubId)
    const response = await hub.fetch(
      new Request(`https://bridge-hub/consent/pending?user_id=${encodeURIComponent(userId)}`),
    )
    return new Response(response.body, {
      status: response.status,
      headers: { ...corsHeaders(origin), 'Content-Type': 'application/json' },
    })
  }

  if (url.pathname.startsWith('/api/v1/bridge/consent/') && url.pathname.endsWith('/respond')) {
    if (request.method !== 'POST') {
      return new Response('Method not allowed', { status: 405 })
    }
    const userId = await resolveUserId(request, env)
    if (!userId) {
      return Response.json({ detail: 'Unauthorized' }, { status: 401, headers: corsHeaders(origin) })
    }
    const requestId = url.pathname.split('/').at(-2)
    if (!requestId) {
      return Response.json({ detail: 'Invalid request id' }, { status: 400, headers: corsHeaders(origin) })
    }
    const body = (await request.json()) as { approved?: boolean }
    const hubId = env.BRIDGE_HUB.idFromName(userId)
    const hub = env.BRIDGE_HUB.get(hubId)
    const response = await hub.fetch(
      new Request('https://bridge-hub/consent/respond', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          user_id: userId,
          request_id: requestId,
          approved: Boolean(body.approved),
        }),
      }),
    )
    return new Response(response.body, {
      status: response.status,
      headers: { ...corsHeaders(origin), 'Content-Type': 'application/json' },
    })
  }

  if (url.pathname === '/api/v1/bridge/consent/ws') {
    const token = url.searchParams.get('token')
    const authRequest = token
      ? new Request(request.url, { headers: { Authorization: `Bearer ${token}` } })
      : request
    const userId = await resolveUserId(authRequest, env)
    if (!userId) {
      return new Response('Unauthorized', { status: 401 })
    }
    const hubId = env.BRIDGE_HUB.idFromName(userId)
    const hub = env.BRIDGE_HUB.get(hubId)
    return hub.fetch(new Request('https://bridge-hub/consent/ws', { headers: request.headers }))
  }

  const invokeMatch = url.pathname.match(/^\/api\/v1\/bridge\/devices\/([^/]+)\/invoke$/)
  if (invokeMatch && request.method === 'POST') {
    const userId = await resolveUserId(request, env)
    if (!userId) {
      return Response.json({ detail: 'Unauthorized' }, { status: 401, headers: corsHeaders(origin) })
    }

    const deviceId = invokeMatch[1]
    const body = (await request.json()) as { tool?: string; args?: Record<string, unknown> }
    const tool = body.tool as BridgeToolName | undefined
    const args = body.args ?? {}

    if (!tool || !BRIDGE_ALLOWED_TOOLS.has(tool)) {
      return Response.json(
        { detail: tool ? `Unknown bridge tool '${tool}'` : 'tool is required' },
        { status: 400, headers: corsHeaders(origin) },
      )
    }

    const backendBase = (env.BACKEND_URL || 'http://127.0.0.1:8000').replace(/\/$/, '')
    const authHeader = request.headers.get('Authorization') ?? ''
    const devicesResponse = await fetch(`${backendBase}/api/v1/bridge/devices`, {
      headers: { Authorization: authHeader },
    })
    if (!devicesResponse.ok) {
      return Response.json(
        { detail: 'Unauthorized' },
        { status: devicesResponse.status, headers: corsHeaders(origin) },
      )
    }

    const devices = (await devicesResponse.json()) as BridgeDeviceRecord[]
    const device = devices.find((entry) => entry.id === deviceId)
    if (!device) {
      return Response.json({ detail: 'Device not found' }, { status: 404, headers: corsHeaders(origin) })
    }

    const capabilityError = bridgeCapabilityError(device.capabilities, tool)
    if (capabilityError) {
      return Response.json({ detail: capabilityError }, { status: 400, headers: corsHeaders(origin) })
    }

    const timeoutMs =
      BRIDGE_WRITE_TOOLS.has(tool) || BRIDGE_EXEC_TOOLS.has(tool) ? 120_000 : 30_000
    const hubId = env.BRIDGE_HUB.idFromName(userId)
    const hub = env.BRIDGE_HUB.get(hubId)
    const response = await hub.fetch(
      new Request('https://bridge-hub/dispatch', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          device_id: deviceId,
          tool,
          args,
          timeout_ms: timeoutMs,
        }),
      }),
    )
    return new Response(response.body, {
      status: response.status,
      headers: { ...corsHeaders(origin), 'Content-Type': 'application/json' },
    })
  }

  const onlineMatch = url.pathname.match(/^\/api\/v1\/bridge\/devices\/([^/]+)\/online$/)
  if (onlineMatch && request.method === 'GET') {
    const userId = await resolveUserId(request, env)
    if (!userId) {
      return Response.json({ detail: 'Unauthorized' }, { status: 401, headers: corsHeaders(origin) })
    }
    const deviceId = onlineMatch[1]
    const hubId = env.BRIDGE_HUB.idFromName(userId)
    const hub = env.BRIDGE_HUB.get(hubId)
    const response = await hub.fetch(
      new Request(`https://bridge-hub/status?device_id=${encodeURIComponent(deviceId)}`),
    )
    return new Response(response.body, {
      status: response.status,
      headers: { ...corsHeaders(origin), 'Content-Type': 'application/json' },
    })
  }

  if (url.pathname === '/api/v1/bridge/ws') {
    const deviceToken = url.searchParams.get('device_token')
    if (!deviceToken) {
      return new Response('device_token required', { status: 400 })
    }

    const session = await validateDeviceToken(deviceToken, env)
    if (!session) {
      return new Response('Unauthorized', { status: 401 })
    }

    const hubId = env.BRIDGE_HUB.idFromName(session.user_id)
    const hub = env.BRIDGE_HUB.get(hubId)
    const target = new URL('https://bridge-hub/ws')
    target.searchParams.set('device_id', session.device_id)
    return hub.fetch(new Request(target.toString(), { headers: request.headers }))
  }

  return null
}

export async function handleInternalBridgeDispatch(
  request: Request,
  env: BridgeEnv,
): Promise<Response> {
  const secret = request.headers.get('X-Bridge-Secret')
  const expected =
    env.INTERNAL_BRIDGE_SECRET || (env as { INTERNAL_NOTIFY_SECRET?: string }).INTERNAL_NOTIFY_SECRET
  if (!secret || !expected || secret !== expected) {
    return Response.json({ detail: 'Forbidden' }, { status: 403 })
  }

  const body = (await request.json()) as BridgeDispatchRequest
  const hubId = env.BRIDGE_HUB.idFromName(body.user_id)
  const hub = env.BRIDGE_HUB.get(hubId)
  const response = await hub.fetch(
    new Request('https://bridge-hub/dispatch', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        device_id: body.device_id,
        tool: body.tool,
        args: body.args,
        timeout_ms: body.timeout_ms,
      }),
    }),
  )
  return response
}