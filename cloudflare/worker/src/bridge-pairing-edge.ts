import type { BridgeEnv } from './bridge-types'

const CODE_TTL_MS = 30 * 60 * 1000

type PairingEnv = BridgeEnv & { NOTIFICATIONS_DB: D1Database }

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

function bridgeSecret(env: PairingEnv): string {
  return env.INTERNAL_BRIDGE_SECRET || (env as { INTERNAL_NOTIFY_SECRET?: string }).INTERNAL_NOTIFY_SECRET || ''
}

async function resolveUserId(request: Request, env: PairingEnv): Promise<string | null> {
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

function generatePairingCode(): string {
  return String(Math.floor(100000 + Math.random() * 900000))
}

async function allocatePairingCode(db: D1Database): Promise<string> {
  for (let attempt = 0; attempt < 8; attempt += 1) {
    const code = generatePairingCode()
    const existing = await db
      .prepare('SELECT code FROM bridge_pairing_codes WHERE code = ?')
      .bind(code)
      .first()
    if (!existing) return code
  }
  throw new Error('Could not allocate pairing code')
}

export async function handleBridgePairingEdge(
  request: Request,
  env: PairingEnv,
): Promise<Response | null> {
  const url = new URL(request.url)
  const origin = request.headers.get('Origin')

  if (url.pathname === '/api/v1/bridge/pairing-codes' && request.method === 'POST') {
    const userId = await resolveUserId(request, env)
    if (!userId) {
      return Response.json({ detail: 'Unauthorized' }, { status: 401, headers: corsHeaders(origin) })
    }

    const now = Date.now()
    const expiresAt = now + CODE_TTL_MS
    const code = await allocatePairingCode(env.NOTIFICATIONS_DB)
    await env.NOTIFICATIONS_DB.prepare(
      'INSERT INTO bridge_pairing_codes (code, user_id, expires_at, used_at, created_at) VALUES (?, ?, ?, NULL, ?)',
    )
      .bind(code, userId, expiresAt, now)
      .run()

    return Response.json(
      {
        code,
        expires_at: new Date(expiresAt).toISOString(),
        expires_in_seconds: Math.floor(CODE_TTL_MS / 1000),
      },
      { headers: { ...corsHeaders(origin), 'Content-Type': 'application/json' } },
    )
  }

  if (url.pathname === '/api/v1/bridge/pair' && request.method === 'POST') {
    let body: {
      code?: string
      device_name?: string
      allowed_roots?: string[] | null
      enable_write_execute?: boolean
    }
    try {
      body = (await request.json()) as typeof body
    } catch {
      return Response.json({ detail: 'Invalid JSON body' }, { status: 400, headers: corsHeaders(origin) })
    }

    const code = String(body.code ?? '').trim()
    const deviceName = String(body.device_name ?? '').trim() || 'My device'
    if (code.length !== 6) {
      return Response.json({ detail: 'Invalid pairing code' }, { status: 404, headers: corsHeaders(origin) })
    }

    const now = Date.now()
    const row = await env.NOTIFICATIONS_DB.prepare(
      'SELECT code, user_id, expires_at, used_at FROM bridge_pairing_codes WHERE code = ?',
    )
      .bind(code)
      .first<{ code: string; user_id: string; expires_at: number; used_at: number | null }>()

    if (!row) {
      return Response.json(
        {
          detail:
            'Invalid pairing code. Generate a fresh code on the agent /bridge page and run install immediately.',
        },
        { status: 404, headers: corsHeaders(origin) },
      )
    }
    if (row.used_at != null) {
      return Response.json(
        { detail: 'Pairing code already used. Generate a NEW code on the agent /bridge page.' },
        { status: 400, headers: corsHeaders(origin) },
      )
    }
    if (row.expires_at < now) {
      return Response.json(
        {
          detail:
            'Pairing code expired. Generate a NEW code on the agent /bridge page and run install within 30 minutes.',
        },
        { status: 400, headers: corsHeaders(origin) },
      )
    }

    const secret = bridgeSecret(env)
    if (!secret) {
      return Response.json({ detail: 'Bridge pairing not configured' }, { status: 503, headers: corsHeaders(origin) })
    }

    const backendBase = (env.BACKEND_URL || 'http://127.0.0.1:8000').replace(/\/$/, '')
    const internalResponse = await fetch(`${backendBase}/api/v1/bridge/internal/pair`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-Bridge-Secret': secret,
      },
      body: JSON.stringify({
        user_id: row.user_id,
        device_name: deviceName,
        allowed_roots: body.allowed_roots ?? [],
        enable_write_execute: Boolean(body.enable_write_execute),
      }),
    })

    const responseText = await internalResponse.text()
    if (!internalResponse.ok) {
      return new Response(responseText, {
        status: internalResponse.status,
        headers: { ...corsHeaders(origin), 'Content-Type': 'application/json' },
      })
    }

    await env.NOTIFICATIONS_DB.prepare('UPDATE bridge_pairing_codes SET used_at = ? WHERE code = ?')
      .bind(now, code)
      .run()

    return new Response(responseText, {
      status: 200,
      headers: { ...corsHeaders(origin), 'Content-Type': 'application/json' },
    })
  }

  return null
}