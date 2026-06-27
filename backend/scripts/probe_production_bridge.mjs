#!/usr/bin/env node
/**
 * Probe production bridge: device-session lookup + internal dispatch.
 * Usage: node probe_production_bridge.mjs [device_token]
 */
import fs from 'node:fs/promises'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const __dirname = path.dirname(fileURLToPath(import.meta.url))
const ROOT = path.resolve(__dirname, '../..')

const API_BASES = ['https://obolla.com', 'https://agentnexus-api.obolla.com']
const USER_ID = '32587456-b3ff-44a5-9374-28e5de217043'
const DEVICE_ID = 'fe135ab6-8393-4e72-be06-45881cc07a01'

async function loadSecret() {
  const env = await fs.readFile(path.join(ROOT, 'backend/.env'), 'utf8')
  const match = env.match(/^INTERNAL_NOTIFY_SECRET=(.+)$/m)
  if (!match) throw new Error('INTERNAL_NOTIFY_SECRET missing')
  return match[1].trim()
}

async function probeDeviceSession(secret, apiBase, deviceToken) {
  const res = await fetch(`${apiBase}/api/v1/bridge/device-session`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-Bridge-Secret': secret,
    },
    body: JSON.stringify({ device_token: deviceToken }),
  })
  const text = await res.text()
  return { status: res.status, body: text }
}

async function probeDispatch(secret, base) {
  const res = await fetch(`${base}/internal/bridge/dispatch`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-Bridge-Secret': secret,
    },
    body: JSON.stringify({
      user_id: USER_ID,
      device_id: DEVICE_ID,
      tool: 'list_dir',
      args: { path: '.' },
      timeout_ms: 10_000,
    }),
  })
  const text = await res.text()
  return { status: res.status, body: text }
}

async function main() {
  const secret = await loadSecret()
  const deviceToken = process.argv[2] || ''

  console.log('=== device-session (if token provided) ===')
  if (deviceToken) {
    for (const apiBase of API_BASES) {
      const result = await probeDeviceSession(secret, apiBase, deviceToken)
      console.log(`${apiBase} -> ${result.status}: ${result.body.slice(0, 300)}`)
    }
  } else {
    console.log('(pass device_token as argv[2] to validate HP_AL01 token against prod DB)')
  }

  console.log('\n=== dispatch HP_AL01 ===')
  for (const base of ['https://obolla.com', 'https://agentnexus.mrgeo888.workers.dev']) {
    const result = await probeDispatch(secret, base)
    console.log(`${base} -> ${result.status}`)
    try {
      console.log(JSON.stringify(JSON.parse(result.body), null, 2))
    } catch {
      console.log(result.body.slice(0, 400))
    }
  }
}

main().catch((err) => {
  console.error(err)
  process.exit(1)
})