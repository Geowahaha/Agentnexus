#!/usr/bin/env node
import fs from 'node:fs/promises'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const __dirname = path.dirname(fileURLToPath(import.meta.url))
const ROOT = path.resolve(__dirname, '../..')

async function loadSecret() {
  const env = await fs.readFile(path.join(ROOT, 'backend/.env'), 'utf8')
  const match = env.match(/^INTERNAL_NOTIFY_SECRET=(.+)$/m)
  return match?.[1]?.trim() || ''
}

async function session(apiBase, secret, token, label) {
  const res = await fetch(`${apiBase}/api/v1/bridge/device-session`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-Bridge-Secret': secret,
    },
    body: JSON.stringify({ device_token: token }),
  })
  const text = await res.text()
  console.log(`\n${label} @ ${apiBase} -> ${res.status}`)
  console.log(text.slice(0, 500))
}

async function main() {
  const secret = await loadSecret()
  const george = JSON.parse(
    await fs.readFile(path.join(process.env.USERPROFILE, '.agentnexus', 'bridge.json'), 'utf8'),
  )
  const bases = ['https://obolla.com', 'https://agentnexus-api.obolla.com', 'https://agentnexus.mrgeo888.workers.dev']
  for (const base of bases) {
    await session(base, secret, george.device_token, `George-PC (${george.device_id})`)
  }
}

main().catch(console.error)