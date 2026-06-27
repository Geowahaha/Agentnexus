#!/usr/bin/env node
/**
 * Production reproduction test: consent timeout must broadcast consent_expired,
 * clear pending map, and return deterministic error (not silent null).
 *
 * Usage:
 *   node backend/scripts/test_consent_timeout_production.mjs
 *
 * Env (optional):
 *   AGENTNEXUS_API_BASE   default https://obolla.com
 *   AGENTNEXUS_BRIDGE_SECRET
 *   AGENTNEXUS_USER_ID
 *   AGENTNEXUS_DEVICE_ID
 *   AGENTNEXUS_ACCESS_TOKEN  JWT for consent WebSocket watcher
 */

import { spawn } from 'node:child_process'
import fs from 'node:fs/promises'
import path from 'node:path'
import { fileURLToPath } from 'node:url'
import WebSocket from 'ws'

const __dirname = path.dirname(fileURLToPath(import.meta.url))
const ROOT = path.resolve(__dirname, '../..')
const BRIDGE_CLI = path.join(ROOT, 'packages/bridge/index.mjs')

const API_BASE = (process.env.AGENTNEXUS_API_BASE || 'https://obolla.com').replace(/\/$/, '')
const BRIDGE_SECRET = process.env.AGENTNEXUS_BRIDGE_SECRET || ''
const USER_ID = process.env.AGENTNEXUS_USER_ID || '32587456-b3ff-44a5-9374-28e5de217043'
const DEVICE_ID = process.env.AGENTNEXUS_DEVICE_ID || '3452affa-358b-40bd-8937-fcb2fa8bbac3'
const ACCESS_TOKEN = process.env.AGENTNEXUS_ACCESS_TOKEN || ''

const CONSENT_WAIT_MS = 120_000
const POLL_MS = 2_000

function log(step, message) {
  const ts = new Date().toISOString().slice(11, 19)
  console.log(`[${ts}] ${step}: ${message}`)
}

async function loadSecret() {
  if (BRIDGE_SECRET) return BRIDGE_SECRET
  try {
    const env = await fs.readFile(path.join(ROOT, 'backend/.env'), 'utf8')
    const match = env.match(/^INTERNAL_NOTIFY_SECRET=(.+)$/m)
    if (match) return match[1].trim()
  } catch {
    // ignore
  }
  throw new Error('Set AGENTNEXUS_BRIDGE_SECRET or backend/.env INTERNAL_NOTIFY_SECRET')
}

async function deviceOnline() {
  const response = await fetch(
    `${API_BASE}/api/v1/bridge/devices/${DEVICE_ID}/online`,
    { headers: { Authorization: `Bearer ${ACCESS_TOKEN}` } },
  )
  if (!response.ok) return false
  const payload = await response.json()
  return Boolean(payload.online)
}

function startBridgeConnect() {
  const proc = spawn('node', [BRIDGE_CLI, 'connect', '--api', API_BASE], {
    cwd: ROOT,
    stdio: ['ignore', 'pipe', 'pipe'],
  })
  proc.stdout.on('data', (chunk) => {
    const line = String(chunk).trim()
    if (line) log('bridge', line)
  })
  proc.stderr.on('data', (chunk) => {
    const line = String(chunk).trim()
    if (line) log('bridge-err', line)
  })
  return proc
}

async function waitForDeviceOnline(maxMs = 30_000) {
  const deadline = Date.now() + maxMs
  while (Date.now() < deadline) {
    if (await deviceOnline()) return true
    await new Promise((r) => setTimeout(r, 1_000))
  }
  return false
}

function consentWsUrl() {
  const wsBase = API_BASE.replace(/^http/, 'ws')
  return `${wsBase}/api/v1/bridge/consent/ws?token=${encodeURIComponent(ACCESS_TOKEN)}`
}

async function listPending() {
  const response = await fetch(`${API_BASE}/api/v1/bridge/consent/pending`, {
    headers: { Authorization: `Bearer ${ACCESS_TOKEN}` },
  })
  if (!response.ok) throw new Error(`pending HTTP ${response.status}`)
  const payload = await response.json()
  return payload.items || []
}

async function dispatchWriteFile(secret) {
  const response = await fetch(`${API_BASE}/internal/bridge/dispatch`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-Bridge-Secret': secret,
    },
    body: JSON.stringify({
      user_id: USER_ID,
      device_id: DEVICE_ID,
      tool: 'write_file',
      args: {
        path: 'consent-timeout-test.txt',
        content: `timeout-repro-${Date.now()}`,
      },
      timeout_ms: CONSENT_WAIT_MS + 15_000,
    }),
  })
  return { status: response.status, body: await response.json() }
}

async function main() {
  if (!ACCESS_TOKEN) {
    throw new Error('Set AGENTNEXUS_ACCESS_TOKEN (JWT for consent watcher user)')
  }

  const secret = await loadSecret()
  log('setup', `API=${API_BASE} user=${USER_ID} device=${DEVICE_ID}`)

  let bridgeProc = null
  if (!(await deviceOnline())) {
    log('setup', 'device offline — starting local bridge connect')
    bridgeProc = startBridgeConnect()
    const online = await waitForDeviceOnline()
    if (!online) {
      bridgeProc?.kill()
      throw new Error('Bridge device did not come online within 30s')
    }
  }
  log('setup', 'device online')

  const events = []
  let consentRequestId = null

  await new Promise((resolve, reject) => {
    const ws = new WebSocket(consentWsUrl())
    const started = Date.now()

    ws.on('open', () => log('ws', 'consent watcher connected'))

    ws.on('message', (raw) => {
      let message
      try {
        message = JSON.parse(String(raw))
      } catch {
        return
      }
      events.push({ at: Date.now() - started, type: message.type, request_id: message.request_id })
      log('ws', `${message.type}${message.request_id ? ` ${message.request_id}` : ''}`)
      if (message.type === 'consent_request' && message.request_id) {
        consentRequestId = message.request_id
      }
      if (message.type === 'consent_expired') {
        resolve()
      }
    })

    ws.on('error', (err) => reject(err))

    ;(async () => {
      await new Promise((r) => setTimeout(r, 1_500))
      log('test', 'triggering write_file (no approve/deny)')
      const dispatchPromise = dispatchWriteFile(secret)

      const pendingAfterRequest = await listPending()
      log('test', `pending after trigger: ${pendingAfterRequest.length}`)

      const dispatch = await dispatchPromise
      log('test', `dispatch HTTP ${dispatch.status} -> ${JSON.stringify(dispatch.body)}`)

      const pendingAfterTimeout = await listPending()
      log('test', `pending after timeout: ${pendingAfterTimeout.length}`)

      const expiredSeen = events.some((e) => e.type === 'consent_expired')
      const errors = []
      if (!consentRequestId) errors.push('never received consent_request')
      if (!expiredSeen) errors.push('never received consent_expired on WebSocket')
      if (dispatch.body?.error !== 'consent_expired') {
        errors.push(`dispatch error expected consent_expired, got ${dispatch.body?.error}`)
      }
      if (pendingAfterTimeout.length > 0) {
        errors.push(`pending list not empty after timeout (${pendingAfterTimeout.length})`)
      }

      ws.close()
      bridgeProc?.kill()

      console.log('\n=== Reproduction test results ===')
      console.log(JSON.stringify({ events, dispatch: dispatch.body, pendingAfterTimeout }, null, 2))

      if (errors.length) {
        console.error('\nFAIL:', errors.join('; '))
        process.exit(1)
      }
      console.log('\nPASS: consent timeout reproduction on production')
      resolve()
    })().catch((err) => {
      ws.close()
      bridgeProc?.kill()
      reject(err)
    })
  })
}

main().catch((err) => {
  console.error(err instanceof Error ? err.message : err)
  process.exit(1)
})