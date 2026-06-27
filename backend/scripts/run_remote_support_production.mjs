#!/usr/bin/env node
/**
 * Run a single-agent remote support workflow on HP_AL01 (production).
 *
 * Get your JWT: DevTools → Application → localStorage → auth token on obolla.com
 * Or Network tab → any /api/v1 request → Authorization header.
 *
 *   set AGENTNEXUS_ACCESS_TOKEN=eyJ...
 *   node backend/scripts/run_remote_support_production.mjs
 *
 * Optional:
 *   AGENTNEXUS_TASK="List the customer Desktop and summarize what apps/projects you see"
 */
import fs from 'node:fs/promises'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const __dirname = path.dirname(fileURLToPath(import.meta.url))

const API_BASE = (process.env.AGENTNEXUS_API_BASE || 'https://obolla.com').replace(/\/$/, '')
const TOKEN = process.env.AGENTNEXUS_ACCESS_TOKEN || ''
const DEVICE_ID = process.env.AGENTNEXUS_DEVICE_ID || 'fe135ab6-8393-4e72-be06-45881cc07a01'
const TASK =
  process.env.AGENTNEXUS_TASK ||
  'Remote support on the customer PC: use bridge.list_dir on path "C:\\\\Users\\\\Admin\\\\Desktop" then bridge.list_dir on "C:\\\\Users\\\\Admin". Summarize what you find in plain language for the support technician.'

function headers() {
  if (!TOKEN) throw new Error('Set AGENTNEXUS_ACCESS_TOKEN (JWT from obolla.com while logged in)')
  return { Authorization: `Bearer ${TOKEN}`, 'Content-Type': 'application/json' }
}

async function main() {
  const onlineRes = await fetch(`${API_BASE}/api/v1/bridge/devices/${DEVICE_ID}/online`, {
    headers: headers(),
  })
  const online = await onlineRes.json()
  console.log('HP_AL01 online:', online.online)
  if (!online.online) {
    throw new Error('HP_AL01 offline — customer bridge must be running')
  }

  const agentsRes = await fetch(`${API_BASE}/api/v1/agents`, { headers: headers() })
  if (!agentsRes.ok) throw new Error(`agents ${agentsRes.status}: ${await agentsRes.text()}`)
  const agents = await agentsRes.json()
  const agent = agents.find((a) => a.is_active !== false) || agents[0]
  if (!agent) throw new Error('No agents in marketplace')
  console.log('agent:', agent.name, agent.id)

  const runRes = await fetch(`${API_BASE}/api/v1/workflows/run`, {
    method: 'POST',
    headers: headers(),
    body: JSON.stringify({
      task_description: TASK,
      workflow_type: 'single_agent',
      agent_id: agent.id,
      bridge_device_id: DEVICE_ID,
    }),
  })
  const runText = await runRes.text()
  if (!runRes.ok) throw new Error(`workflow run ${runRes.status}: ${runText}`)
  const { workflow_id: workflowId } = JSON.parse(runText)
  console.log('workflow:', `${API_BASE}/workflows/${workflowId}`)

  for (let i = 0; i < 45; i++) {
    await new Promise((r) => setTimeout(r, 2000))
    const statusRes = await fetch(`${API_BASE}/api/v1/workflows/${workflowId}`, { headers: headers() })
    const data = await statusRes.json()
    const status = data.status
    const tools = data.intermediate_results?.tool_calls || []
    process.stdout.write(`\rstatus: ${status}  tools: ${tools.length}  `)
    if (status === 'completed' || status === 'failed') {
      console.log('\n')
      console.log('tools:', JSON.stringify(tools, null, 2).slice(0, 2000))
      console.log('\noutput:', String(data.final_output || '').slice(0, 1500))
      if (status === 'completed' && tools.some((t) => String(t.output).includes('"ok": true'))) {
        console.log('\nREMOTE SUPPORT: PASS')
        await fs.writeFile(
          path.join(__dirname, '../../.production/remote-support-result.json'),
          JSON.stringify({ workflowId, status, tools, final_output: data.final_output }, null, 2),
        )
        return
      }
      throw new Error(`REMOTE SUPPORT: ${status}`)
    }
  }
  throw new Error('timed out')
}

main().catch((err) => {
  console.error(err.message || err)
  process.exit(1)
})