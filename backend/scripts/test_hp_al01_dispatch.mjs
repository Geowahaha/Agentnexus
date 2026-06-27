#!/usr/bin/env node
/**
 * Production smoke: dispatch list_dir to HP_AL01 (agent workflow pipe).
 */
import fs from 'node:fs/promises'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const __dirname = path.dirname(fileURLToPath(import.meta.url))
const ROOT = path.resolve(__dirname, '../..')

const API_BASE = 'https://obolla.com'
const USER_ID = '32587456-b3ff-44a5-9374-28e5de217043'
const DEVICE_ID = 'fe135ab6-8393-4e72-be06-45881cc07a01'

async function loadSecret() {
  const env = await fs.readFile(path.join(ROOT, 'backend/.env'), 'utf8')
  const match = env.match(/^INTERNAL_NOTIFY_SECRET=(.+)$/m)
  if (!match) throw new Error('INTERNAL_NOTIFY_SECRET missing in backend/.env')
  return match[1].trim()
}

async function main() {
  const secret = await loadSecret()

  const onlineRes = await fetch(`${API_BASE}/api/v1/bridge/devices/${DEVICE_ID}/online`, {
    headers: { Authorization: `Bearer ${process.env.AGENTNEXUS_ACCESS_TOKEN || ''}` },
  })
  if (process.env.AGENTNEXUS_ACCESS_TOKEN) {
    const online = await onlineRes.json()
    console.log('online:', online)
  } else {
    console.log('online check skipped (set AGENTNEXUS_ACCESS_TOKEN for JWT online probe)')
  }

  for (const base of ['https://obolla.com', 'https://agentnexus.mrgeo888.workers.dev']) {
    const response = await fetch(`${base}/internal/bridge/dispatch`, {
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
        timeout_ms: 30_000,
      }),
    })
    const text = await response.text()
    console.log(`\n${base} -> ${response.status}`)
    try {
      console.log(JSON.stringify(JSON.parse(text), null, 2))
    } catch {
      console.log(text.slice(0, 400))
    }
  }
}

main().catch((err) => {
  console.error(err)
  process.exit(1)
})