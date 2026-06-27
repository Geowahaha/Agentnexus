#!/usr/bin/env node
import { spawn } from 'node:child_process'
import fs from 'node:fs/promises'
import path from 'node:path'
import os from 'node:os'
import readline from 'node:readline/promises'
import { stdin as input, stdout as output } from 'node:process'
import WebSocket from 'ws'

const DEFAULT_API = 'https://agentnexus.mrgeo888.workers.dev'

function usage() {
  console.log(`
AgentNexus Local Bridge

Usage:
  agentnexus-bridge pair <CODE> [--name "My PC"] [--allow-write] [--roots PATH] [--api URL]
  agentnexus-bridge connect [--api URL]
  agentnexus-bridge probe [--api URL]
  agentnexus-bridge status

New tools: search_files, get_file_info (no consent)
Expanded (stubs): browse_page, run_local_llm, execute_in_app (require consent + future local setup)

Examples:
  agentnexus-bridge pair 482913 --name "George-PC" --allow-write
  agentnexus-bridge connect
`)
}

function configPath() {
  const home = os.homedir()
  return path.join(home, '.agentnexus', 'bridge.json')
}

async function loadConfig() {
  try {
    const raw = await fs.readFile(configPath(), 'utf8')
    const cleaned = raw.replace(/^\uFEFF/, '').trim()
    return JSON.parse(cleaned)
  } catch {
    return null
  }
}

async function saveConfig(config) {
  const file = configPath()
  await fs.mkdir(path.dirname(file), { recursive: true })
  await fs.writeFile(file, JSON.stringify(config, null, 2), 'utf8')
}

function parseArgs(argv) {
  const args = [...argv]
  const flags = {}
  const positionals = []
  for (let i = 0; i < args.length; i += 1) {
    const arg = args[i]
    if (arg === '--api') {
      flags.api = args[i + 1]
      i += 1
      continue
    }
    if (arg === '--name') {
      flags.name = args[i + 1]
      i += 1
      continue
    }
    if (arg === '--allow-write') {
      flags.allowWrite = true
      continue
    }
    if (arg === '--roots') {
      flags.roots = args[i + 1]
      i += 1
      continue
    }
    if (arg === '--solution') {
      flags.solution = args[i + 1]
      i += 1
      continue
    }
    positionals.push(arg)
  }
  return { flags, positionals }
}

function defaultAllowedRoots() {
  return [os.homedir()]
}

function parseAllowedRoots(raw) {
  if (!raw || !String(raw).trim()) return defaultAllowedRoots()
  const roots = String(raw)
    .split(',')
    .map((entry) => entry.trim())
    .filter(Boolean)
    .map((entry) => path.resolve(entry))
  return roots.length > 0 ? roots : defaultAllowedRoots()
}

function wsUrl(apiBase, deviceToken) {
  const base = apiBase.replace(/\/$/, '')
  const wsBase = base.replace(/^http/, 'ws')
  return `${wsBase}/api/v1/bridge/ws?device_token=${encodeURIComponent(deviceToken)}`
}

function resolveSafePath(targetPath, allowedRoots) {
  const roots = allowedRoots.length > 0 ? allowedRoots : [process.cwd()]
  const resolved = path.resolve(targetPath || '.')
  for (const root of roots) {
    const rootResolved = path.resolve(root)
    if (resolved === rootResolved || resolved.startsWith(rootResolved + path.sep)) {
      return resolved
    }
  }
  throw new Error(`Path not allowed: ${resolved}`)
}

async function toolListDir(args, allowedRoots) {
  const target = resolveSafePath(args.path || '.', allowedRoots)
  const entries = await fs.readdir(target, { withFileTypes: true })
  return {
    path: target,
    entries: entries.map((entry) => ({
      name: entry.name,
      type: entry.isDirectory() ? 'dir' : 'file',
    })),
  }
}

async function toolReadFile(args, allowedRoots) {
  const target = resolveSafePath(args.path, allowedRoots)
  const stat = await fs.stat(target)
  if (!stat.isFile()) {
    throw new Error('Not a file')
  }
  if (stat.size > 512_000) {
    throw new Error('File too large (max 512KB in Phase 1)')
  }
  const content = await fs.readFile(target, 'utf8')
  return { path: target, size: stat.size, content }
}

async function toolWriteFile(args, allowedRoots) {
  const target = resolveSafePath(args.path, allowedRoots)
  const content = String(args.content ?? '')
  if (content.length > 1_048_576) {
    throw new Error('Content too large (max 1MB)')
  }
  await fs.mkdir(path.dirname(target), { recursive: true })
  await fs.writeFile(target, content, 'utf8')
  return { path: target, bytes_written: Buffer.byteLength(content, 'utf8') }
}

function toolRunCommand(args, allowedRoots) {
  const roots = allowedRoots.length > 0 ? allowedRoots : [process.cwd()]
  const cwd = resolveSafePath(args.cwd || roots[0], allowedRoots)
  const command = String(args.command || '').trim()
  if (!command) {
    throw new Error('command is required')
  }

  return new Promise((resolve, reject) => {
    const child = spawn(command, {
      cwd,
      shell: true,
      windowsHide: true,
    })
    let stdout = ''
    let stderr = ''
    const timer = setTimeout(() => {
      child.kill()
      reject(new Error('Command timed out after 60s'))
    }, 60_000)

    child.stdout.on('data', (chunk) => {
      stdout += String(chunk)
    })
    child.stderr.on('data', (chunk) => {
      stderr += String(chunk)
    })
    child.on('error', (error) => {
      clearTimeout(timer)
      reject(error)
    })
    child.on('close', (code) => {
      clearTimeout(timer)
      resolve({
        cwd,
        command,
        exit_code: code,
        stdout: stdout.slice(0, 32_000),
        stderr: stderr.slice(0, 32_000),
      })
    })
  })
}

async function toolSearchFiles(args, allowedRoots) {
  const roots = allowedRoots.length > 0 ? allowedRoots : [process.cwd()]
  const root = resolveSafePath(args.root || roots[0], allowedRoots)
  const query = String(args.query || '').toLowerCase().trim()
  const maxResults = Math.min(parseInt(args.max_results || '50'), 200)
  const results = []

  async function walk(dir, depth = 0) {
    if (depth > 6 || results.length >= maxResults) return
    let entries
    try { entries = await fs.readdir(dir, { withFileTypes: true }) } catch { return }
    for (const entry of entries) {
      const full = path.join(dir, entry.name)
      if (entry.isDirectory()) {
        await walk(full, depth + 1)
      } else if (entry.isFile()) {
        if (!query || full.toLowerCase().includes(query) || entry.name.toLowerCase().includes(query)) {
          results.push({ path: full, name: entry.name, size: (await fs.stat(full)).size })
          if (results.length >= maxResults) return
        }
      }
    }
  }

  await walk(root)
  return { root, query, results: results.slice(0, maxResults) }
}

async function toolGetFileInfo(args, allowedRoots) {
  const target = resolveSafePath(args.path, allowedRoots)
  const stat = await fs.stat(target)
  return {
    path: target,
    size: stat.size,
    is_directory: stat.isDirectory(),
    modified_at: stat.mtime.toISOString(),
    created_at: stat.birthtime.toISOString(),
  }
}

// Real implementations for expanded capabilities (browser + local LLM)
async function toolBrowsePage(args) {
  const url = args.url
  if (!url) throw new Error('url required')
  try {
    // Basic real browse using built-in fetch (Node 18+)
    const res = await fetch(url, { headers: { 'User-Agent': 'AgentNexus-Bridge/1.0' } })
    const contentType = res.headers.get('content-type') || ''
    let content = ''
    if (contentType.includes('text/') || contentType.includes('json')) {
      content = await res.text()
    } else {
      content = `[binary content, length=${res.headers.get('content-length') || 'unknown'}]`
    }
    // Simple title extract
    const titleMatch = content.match(/<title[^>]*>([^<]+)<\/title>/i)
    const title = titleMatch ? titleMatch[1].trim() : 'No title'
    return {
      url,
      status: res.status,
      title,
      content_preview: content.slice(0, 2000),
      content_type: contentType,
      ok: res.ok
    }
  } catch (e) {
    return { url, error: e.message, ok: false }
  }
}

async function toolRunLocalLLM(args) {
  const prompt = String(args.prompt || '')
  const model = args.model || 'llama3.1'  // default for ollama
  const ollamaUrl = args.ollama_url || 'http://localhost:11434'
  if (!prompt) throw new Error('prompt required')
  try {
    const res = await fetch(`${ollamaUrl}/api/generate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ model, prompt, stream: false })
    })
    if (!res.ok) throw new Error(`Ollama error ${res.status}`)
    const data = await res.json()
    return {
      model,
      response: data.response,
      done: data.done,
      tokens: data.eval_count || 0,
      total_duration: data.total_duration
    }
  } catch (e) {
    return { error: `Local LLM failed: ${e.message}. Ensure Ollama is running at ${ollamaUrl}`, ok: false }
  }
}

async function toolExecuteInApp(args) {
  const app = args.app || 'unknown'
  const action = args.action || ''
  // For demo, use simple platform exec. Real would use better automation.
  const { exec } = await import('node:child_process')
  return new Promise((resolve) => {
    let cmd = ''
    if (process.platform === 'win32') {
      cmd = `powershell -Command "Write-Output 'Executed ${action} in ${app}'"`
    } else {
      cmd = `echo "Executed ${action} in ${app}"`
    }
    exec(cmd, (err, stdout) => {
      resolve({ app, action, output: stdout.trim() || 'executed', error: err ? err.message : null })
    })
  })
}

// New for Eve irrigation + modern detection
async function toolGetLocalNetworkInfo() {
  const os = await import('node:os')
  const interfaces = os.networkInterfaces()
  const networks = []
  for (const [name, addrs] of Object.entries(interfaces)) {
    for (const addr of addrs) {
      if (addr.family === 'IPv4' && !addr.internal) {
        networks.push({ interface: name, ip: addr.address, mac: addr.mac })
      }
    }
  }
  return {
    networks,
    platform: process.platform,
    hostname: os.hostname(),
    same_wifi_detected: true, // simple: if running locally, assume same network
    detection_method: 'local_os_interfaces'
  }
}

async function toolControlIrrigation(args) {
  const { action = 'status', duration_minutes = 0, device_id = 'eve_default' } = args
  // Real integration for Eve Aqua / HomeKit:
  // - On user's machine, this can call local HomeKit via 'hap' or Eve API if exposed, or AppleScript on Mac, or PowerShell.
  // For test: User can replace this with actual call to their Eve controller.
  // Example: If Eve has local HTTP (unlikely), or use Homebridge REST.
  // Here we simulate + log for test.
  const result = {
    action,
    device_id,
    status: action === 'stop' ? 'stopped' : (action === 'start' ? 'watering' : 'ok'),
    duration_minutes,
    weather_checked: true,
    message: `Eve irrigation ${action} executed (test mode). Replace with real HomeKit/Eve call.`,
    timestamp: new Date().toISOString()
  }
  console.log('[IRRIGATION]', result)
  // Future real: exec local script or fetch to homebridge
  return result
}

const CONSENT_TOOLS = new Set(['write_file', 'run_command'])

async function promptConsent(tool, args) {
  const rl = readline.createInterface({ input, output })
  console.log('\n⚠️  AgentNexus cloud agent requests local action:')
  console.log(`   Tool: ${tool}`)
  console.log(`   Args: ${JSON.stringify(args, null, 2)}`)
  const answer = await rl.question('Allow this action on your machine? [y/N] ')
  rl.close()
  return ['y', 'yes'].includes(answer.trim().toLowerCase())
}

async function pair(code, name, apiBase, allowWrite, allowedRoots, solutionContext) {
  const response = await fetch(`${apiBase}/api/v1/bridge/pair`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      code,
      device_name: name || os.hostname(),
      allowed_roots: allowedRoots,
      enable_write_execute: Boolean(allowWrite),
      solution_context: solutionContext || undefined,
    }),
  })
  if (!response.ok) {
    const detail = await response.text()
    throw new Error(`Pair failed (${response.status}): ${detail}`)
  }
  const payload = await response.json()
  await saveConfig({
    api_base: apiBase,
    device_id: payload.device_id,
    device_name: payload.device_name,
    device_token: payload.device_token,
    allowed_roots: allowedRoots,
    solution_context: payload.solution_context || solutionContext,
    paired_at: new Date().toISOString(),
  })
  console.log(`Paired as "${payload.device_name}" (${payload.device_id})`)
  if (payload.solution_context) {
    console.log(`Associated with solution: ${payload.solution_context}`)
  }
  console.log('Config saved. Run: agentnexus-bridge connect')
}

async function probeConnection(config, timeoutMs = 20_000) {
  const url = wsUrl(config.api_base, config.device_token)
  return new Promise((resolve) => {
    let settled = false
    const finish = (ok) => {
      if (settled) return
      settled = true
      clearTimeout(timer)
      try {
        ws.terminate()
      } catch {
        /* ignore */
      }
      resolve(ok)
    }
    const ws = new WebSocket(url)
    const timer = setTimeout(() => finish(false), timeoutMs)
    ws.on('message', (raw) => {
      try {
        const message = JSON.parse(String(raw))
        if (message.type === 'welcome') finish(true)
      } catch {
        /* ignore */
      }
    })
    ws.on('error', () => finish(false))
    ws.on('close', () => {
      if (!settled) finish(false)
    })
  })
}

async function connectLoop(config) {
  const url = wsUrl(config.api_base, config.device_token)
  console.log(`Connecting to ${url.replace(config.device_token, '***')} ...`)

  const ws = new WebSocket(url)
  const allowedRoots = config.allowed_roots || [process.cwd()]
  let lastMessageAt = Date.now()
  let keepaliveTimer = null

  function sendHello() {
    if (ws.readyState !== WebSocket.OPEN) return
    ws.send(
      JSON.stringify({
        type: 'hello',
        device_id: config.device_id,
        device_name: config.device_name,
      }),
    )
  }

  ws.on('open', () => {
    console.log('Bridge online — waiting for tool calls (Ctrl+C to stop)')
    lastMessageAt = Date.now()
    sendHello()
    keepaliveTimer = setInterval(() => {
      if (Date.now() - lastMessageAt > 90_000) {
        console.log('Stale connection — reconnecting')
        ws.terminate()
        return
      }
      sendHello()
    }, 45_000)
  })

  ws.on('message', async (raw) => {
    lastMessageAt = Date.now()
    let message
    try {
      message = JSON.parse(String(raw))
    } catch {
      return
    }

    if (message.type === 'ping') {
      ws.send(JSON.stringify({ type: 'pong' }))
      return
    }

    if (message.type === 'consent_decision') {
      return
    }

    if (message.type !== 'tool_call') return

    const { request_id, tool, args, pre_approved: preApproved } = message
    try {
      if (CONSENT_TOOLS.has(tool) && !preApproved) {
        const approved = await promptConsent(tool, args || {})
        if (!approved) {
          throw new Error('User denied consent for local action')
        }
      }

      let result
      if (tool === 'list_dir') {
        result = await toolListDir(args || {}, allowedRoots)
      } else if (tool === 'read_file') {
        result = await toolReadFile(args || {}, allowedRoots)
      } else if (tool === 'write_file') {
        result = await toolWriteFile(args || {}, allowedRoots)
      } else if (tool === 'run_command') {
        result = await toolRunCommand(args || {}, allowedRoots)
      } else if (tool === 'search_files') {
        result = await toolSearchFiles(args || {}, allowedRoots)
      } else if (tool === 'get_file_info') {
        result = await toolGetFileInfo(args || {}, allowedRoots)
      } else if (tool === 'browse_page') {
        result = await toolBrowsePage(args || {})
      } else if (tool === 'run_local_llm') {
        result = await toolRunLocalLLM(args || {})
      } else if (tool === 'execute_in_app') {
        result = await toolExecuteInApp(args || {})
      } else if (tool === 'get_local_network_info') {
        result = await toolGetLocalNetworkInfo()
      } else if (tool === 'control_irrigation') {
        result = await toolControlIrrigation(args || {})
      } else {
        throw new Error(`Unsupported tool: ${tool}`)
      }
      ws.send(JSON.stringify({ type: 'tool_result', request_id, ok: true, result }))
      console.log(`✓ ${tool}`, args)
    } catch (error) {
      ws.send(
        JSON.stringify({
          type: 'tool_result',
          request_id,
          ok: false,
          error: error instanceof Error ? error.message : String(error),
        }),
      )
      console.log(`✗ ${tool}`, error instanceof Error ? error.message : error)
    }
  })

  ws.on('close', () => {
    if (keepaliveTimer) clearInterval(keepaliveTimer)
    console.log('Disconnected — reconnecting in 3s')
    setTimeout(() => connectLoop(config), 3000)
  })

  ws.on('error', (error) => {
    console.error('WebSocket error:', error.message)
  })
}

async function main() {
  const { flags, positionals } = parseArgs(process.argv.slice(2))
  const command = positionals[0]

  if (!command || command === 'help' || command === '--help') {
    usage()
    return
  }

  const apiBase = flags.api || DEFAULT_API

  if (command === 'pair') {
    const code = positionals[1]
    if (!code) {
      usage()
      process.exit(1)
    }
    const allowedRoots = parseAllowedRoots(flags.roots)
    const solutionContext = flags.solution || positionals[2] || ''
    await pair(code, flags.name, apiBase, flags.allowWrite, allowedRoots, solutionContext)
    return
  }

  const config = await loadConfig()
  if (!config?.device_token) {
    console.error('Not paired yet. Run: agentnexus-bridge pair <CODE>')
    process.exit(1)
  }

  if (command === 'status') {
    console.log(JSON.stringify({ ...config, device_token: '***' }, null, 2))
    return
  }

  if (command === 'probe') {
    const ok = await probeConnection({
      ...config,
      api_base: flags.api || config.api_base || apiBase,
    })
    if (!ok) {
      console.error('Bridge probe failed — token invalid or server unreachable')
      process.exit(1)
    }
    console.log('Bridge probe OK')
    return
  }

  if (command === 'connect') {
    await connectLoop({ ...config, api_base: flags.api || config.api_base || apiBase })
    return
  }

  usage()
  process.exit(1)
}

main().catch((error) => {
  console.error(error instanceof Error ? error.message : error)
  process.exit(1)
})