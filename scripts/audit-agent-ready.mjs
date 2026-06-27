#!/usr/bin/env node
/**
 * Agent-ready audit — prefers isitagentready.com API when available.
 * Falls back to local probes if the API is unreachable.
 *
 * Usage: node scripts/audit-agent-ready.mjs https://www.successcasting.com
 */
const url = (process.argv[2]?.replace(/\/$/, '') || 'https://www.successcasting.com').replace(
  /\/$/,
  '',
)

const BOTS = ['GPTBot', 'ClaudeBot', 'PerplexityBot', 'OAI-SearchBot', 'ChatGPT-User', 'Google-Extended']
const AGENT_LINK_RELS = /api-catalog|service-desc|service-doc|describedby|sitemap/i

async function fetchProbe(target, init = {}) {
  try {
    const res = await fetch(target, { redirect: 'follow', ...init })
    const text = await res.text().catch(() => '')
    return { ok: res.ok, status: res.status, headers: Object.fromEntries(res.headers), text, finalUrl: res.url }
  } catch (e) {
    return { ok: false, status: 0, error: String(e), headers: {}, text: '', finalUrl: target }
  }
}

function pct(pass, total) {
  if (total === 0) return 100
  return Math.round((pass / total) * 100)
}

function flattenIsitagentreadyChecks(scan) {
  const rows = []
  for (const [category, group] of Object.entries(scan.checks || {})) {
    for (const [check, result] of Object.entries(group || {})) {
      if (!result?.status) continue
      rows.push({
        category,
        id: check,
        status: result.status,
        pass: result.status === 'pass',
        message: result.message,
      })
    }
  }
  return rows
}

async function auditViaIsitagentready() {
  const res = await fetch('https://isitagentready.com/api/scan', {
    method: 'POST',
    headers: { 'content-type': 'application/json' },
    body: JSON.stringify({ url }),
  })
  if (!res.ok) return null
  const scan = await res.json()
  const rows = flattenIsitagentreadyChecks(scan)
  const applicable = rows.filter((r) => r.status === 'pass' || r.status === 'fail')
  const pass = applicable.filter((r) => r.pass).length
  const total = applicable.length
  const likelyIssues = applicable.filter((r) => !r.pass).map((r) => `${r.category}:${r.id}`)

  return {
    scanned_at: scan.scannedAt || new Date().toISOString(),
    url: scan.url || url,
    canonical: scan.url || url,
    source: 'isitagentready.com/api/scan',
    overall_percent: pct(pass, total),
    isitagentready: {
      level: scan.level,
      level_name: scan.levelName,
      pass,
      fail: total - pass,
      is_commerce: Boolean(scan.isCommerce),
    },
    checks: rows,
    likely_issues: likelyIssues,
    verify_url: 'https://isitagentready.com/',
  }
}

async function auditLocalFallback() {
  const robots = await fetchProbe(`${url}/robots.txt`)
  const sitemap = await fetchProbe(`${url}/sitemap.xml`)
  const llms = await fetchProbe(`${url}/llms.txt`)
  const ai = await fetchProbe(`${url}/ai.txt`)
  const agents = await fetchProbe(`${url}/agents.txt`)
  const home = await fetchProbe(url)
  const md = await fetchProbe(url, { headers: { Accept: 'text/markdown' } })
  const apiCatalog = await fetchProbe(`${url}/.well-known/api-catalog`, {
    headers: { Accept: 'application/linkset+json, application/json' },
  })
  const agentSkills = await fetchProbe(`${url}/.well-known/agent-skills/index.json`)

  const botResults = []
  for (const ua of BOTS) {
    const r = await fetchProbe(url, { headers: { 'User-Agent': ua } })
    botResults.push({
      bot: ua,
      status: r.status,
      content_signal: r.headers['content-signal'] || null,
      pass: r.ok && Boolean(r.headers['content-signal']),
    })
  }

  const mdLinks = (llms.text.match(/\[[^\]]+\]\([^)]+\)/g) || []).length
  const linkHeader = home.headers.link || ''
  const csHeader = home.headers['content-signal'] || ''
  const csRobots = /Content-Signal:/i.test(robots.text)

  const discoverability = [
    { id: 'robots_txt', pass: robots.ok && /GPTBot/i.test(robots.text) && /Sitemap:/i.test(robots.text) },
    { id: 'sitemap', pass: sitemap.ok },
    {
      id: 'link_headers_rfc',
      pass: AGENT_LINK_RELS.test(linkHeader),
    },
    { id: 'llms_markdown', pass: llms.ok && /^#\s/m.test(llms.text) && mdLinks >= 5 },
  ]

  const content = [
    {
      id: 'markdown_negotiation',
      pass: md.ok && (md.headers['content-type'] || '').includes('text/markdown'),
    },
  ]

  const botAccess = [
    { id: 'ai_bot_rules', pass: /GPTBot/i.test(robots.text) && /ClaudeBot/i.test(robots.text) },
    {
      id: 'content_signal_robots_body',
      pass: csRobots && /search=yes/i.test(robots.text),
    },
    {
      id: 'content_signal_header',
      pass: /search=yes/i.test(csHeader) && /ai-input=yes/i.test(csHeader),
    },
    { id: 'all_bots_200', pass: botResults.every((b) => b.status === 200) },
  ]

  const protocol = [
    { id: 'agents_txt', pass: agents.ok && agents.text.length > 50 },
    { id: 'ai_txt', pass: ai.ok && /search=yes/i.test(ai.text) },
    { id: 'api_catalog', pass: apiCatalog.ok },
    { id: 'agent_skills_index', pass: agentSkills.ok },
  ]

  function scoreCategory(checks) {
    const applicable = checks.filter((c) => !c.na)
    const passCount = applicable.filter((c) => c.pass).length
    return { checks, pass: passCount, total: applicable.length, percent: pct(passCount, applicable.length) }
  }

  const categories = {
    discoverability: scoreCategory(discoverability),
    content: scoreCategory(content),
    bot_access: scoreCategory(botAccess),
    protocol: scoreCategory(protocol),
  }

  const applicableCats = Object.values(categories).filter((c) => c.total > 0)
  const overall = pct(
    applicableCats.reduce((s, c) => s + c.pass, 0),
    applicableCats.reduce((s, c) => s + c.total, 0),
  )

  const likelyIssues = []
  for (const [name, cat] of Object.entries(categories)) {
    for (const ch of cat.checks) {
      if (!ch.na && !ch.pass) likelyIssues.push(`${name}:${ch.id}`)
    }
  }

  return {
    scanned_at: new Date().toISOString(),
    url,
    canonical: home.finalUrl || url,
    source: 'local-fallback (not isitagentready All Checks)',
    overall_percent: overall,
    categories: Object.fromEntries(
      Object.entries(categories).map(([k, v]) => [k, { percent: v.percent, pass: v.pass, total: v.total }]),
    ),
    checks: categories,
    bot_results: botResults,
    likely_issues: likelyIssues,
    verify_url: 'https://isitagentready.com/',
    warning: 'Use isitagentready.com for buyer-facing All Checks score.',
  }
}

async function audit() {
  let out = null
  try {
    out = await auditViaIsitagentready()
  } catch {
    out = null
  }
  if (!out) out = await auditLocalFallback()
  console.log(JSON.stringify(out, null, 2))
}

audit()