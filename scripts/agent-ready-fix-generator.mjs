#!/usr/bin/env node
/**
 * Agent-ready fix pack generator — isitagentready scan → deployable templates.
 *
 * Usage:
 *   node scripts/agent-ready-fix-generator.mjs https://example.com
 *   node scripts/agent-ready-fix-generator.mjs https://example.com --json
 */
import { writeFileSync } from 'node:fs'
import { resolve, dirname } from 'node:path'
import { fileURLToPath } from 'node:url'

const __dirname = dirname(fileURLToPath(import.meta.url))

const rawUrl = process.argv[2]
const jsonOut = process.argv.includes('--json')
const outDir = process.argv.includes('--out')
  ? process.argv[process.argv.indexOf('--out') + 1]
  : null

if (!rawUrl) {
  console.error('Usage: node scripts/agent-ready-fix-generator.mjs <url> [--json] [--out dir]')
  process.exit(1)
}

const site = rawUrl.replace(/\/+$/, '')
const host = new URL(site).hostname
const www = host.startsWith('www.') ? site : `https://www.${host}`

const AI_BOTS = [
  'GPTBot',
  'OAI-SearchBot',
  'ChatGPT-User',
  'ClaudeBot',
  'Claude-Web',
  'PerplexityBot',
  'Google-Extended',
  'Applebot-Extended',
  'Applebot',
]

function robotsTxt() {
  const bots = AI_BOTS.map((b) => `User-agent: ${b}\nAllow: /`).join('\n\n')
  return `# ${host} — agent-ready robots.txt
User-agent: *
Allow: /
Content-Signal: ai-train=no, search=yes, ai-input=yes

${bots}

Sitemap: ${www}/sitemap.xml
`
}

function llmsTxt() {
  return `# ${host}

> Machine-readable site map for LLM agents. Policy: ai-train=no, search=yes, ai-input=yes.

- [Home](${www}/)
- [Products](${www}/products)
- [Contact](${www}/#contact)
- [llms.txt](${www}/llms.txt)
- [agents.txt](${www}/agents.txt)
- [ai.txt](${www}/ai.txt)
- [API catalog](${www}/.well-known/api-catalog)
`
}

function agentsTxt() {
  return `# agents.txt — ${host}
contact: ${www}/#contact
policy: ${www}/ai.txt
allowed-paths: /, /products, /blog
catalog: ${www}/products
rfq: ${www}/api/ai/quote
`
}

function aiTxt() {
  return `# ai.txt — ${host}
ai-train: no
search: yes
ai-input: yes
agents: ${www}/agents.txt
llms: ${www}/llms.txt
`
}

function linkHeaderSnippet() {
  return `// next.config.ts — headers() snippet
{
  key: "Link",
  value: '</.well-known/api-catalog>; rel="api-catalog", </llms.txt>; rel="service-doc", </ai.txt>; rel="describedby", </sitemap.xml>; rel="sitemap"',
},
{
  key: "Content-Signal",
  value: "ai-train=no, search=yes, ai-input=yes",
},
`
}

function apiCatalog() {
  return JSON.stringify(
    {
      linkset: [
        {
          anchor: `${www}/api`,
          item: [
            { rel: 'service-desc', href: `${www}/openapi.json`, type: 'application/json' },
            { rel: 'service-doc', href: `${www}/auth.md`, type: 'text/markdown' },
            { rel: 'status', href: `${www}/api/health`, type: 'application/json' },
          ],
        },
      ],
    },
    null,
    2,
  )
}

function x402RouteTs() {
  return `// app/api/v1/route.ts — x402 v2 discovery (customize payTo + SITE_URL)
import { NextRequest, NextResponse } from "next/server";

const SITE = "${www}";
const PAYMENT_JSON = {
  x402Version: 2,
  error: "Payment required to access this resource",
  resource: { url: \`\${SITE}/api/v1\`, description: "Agent API", mimeType: "application/json" },
  accepts: [{
    scheme: "exact",
    network: "eip155:84532",
    amount: "10000",
    asset: "0x036CbD53842c5426634e7929541eC2318f3dCF7e",
    payTo: "0xYOUR_WALLET",
    maxTimeoutSeconds: 60,
    extra: { name: "USDC", version: "2" },
  }],
  extensions: {},
};

export async function GET(request: NextRequest) {
  if (!request.headers.has("payment-signature") && !request.headers.has("PAYMENT-SIGNATURE")) {
    const header = Buffer.from(JSON.stringify(PAYMENT_JSON)).toString("base64");
    return new NextResponse(JSON.stringify({ x402Version: 2, error: PAYMENT_JSON.error }), {
      status: 402,
      headers: { "Content-Type": "application/json", "PAYMENT-REQUIRED": header },
    });
  }
  return NextResponse.json({ ok: true, service: "${host}-agent-api" });
}
`
}

async function fetchScan() {
  const res = await fetch('https://isitagentready.com/api/scan', {
    method: 'POST',
    headers: { 'content-type': 'application/json' },
    body: JSON.stringify({ url: www }),
  })
  if (!res.ok) return null
  return res.json()
}

function gapsFromScan(scan) {
  if (!scan?.checks) return []
  const gaps = []
  for (const [cat, group] of Object.entries(scan.checks)) {
    for (const [id, result] of Object.entries(group || {})) {
      if (result?.status === 'fail') gaps.push({ category: cat, id, message: result.message })
    }
  }
  return gaps
}

const files = {
  'robots.txt': robotsTxt(),
  'llms.txt': llmsTxt(),
  'agents.txt': agentsTxt(),
  'ai.txt': aiTxt(),
  'link-header-snippet.ts': linkHeaderSnippet(),
  'api-catalog.json': apiCatalog(),
  'api-v1-x402-route.ts': x402RouteTs(),
}

const scan = await fetchScan()
const gaps = gapsFromScan(scan)
const report = {
  site: www,
  scanned_at: scan?.scannedAt ?? new Date().toISOString(),
  level: scan?.level,
  level_name: scan?.levelName,
  is_commerce: Boolean(scan?.isCommerce),
  gaps,
  files: Object.keys(files),
  verify: 'POST https://isitagentready.com/api/scan',
  reference: 'https://www.successcasting.com (100% Level 5)',
}

if (outDir) {
  for (const [name, content] of Object.entries(files)) {
    writeFileSync(resolve(outDir, name), content, 'utf8')
  }
  writeFileSync(resolve(outDir, 'scan-report.json'), JSON.stringify(report, null, 2), 'utf8')
  console.log(`Wrote ${Object.keys(files).length + 1} files to ${outDir}`)
}

if (jsonOut) {
  console.log(JSON.stringify({ ...report, file_contents: files }, null, 2))
} else {
  console.log(`# Agent-Ready Fix Pack — ${www}`)
  console.log(`Level: ${report.level ?? '?'} ${report.level_name ?? ''}`)
  console.log(`Gaps: ${gaps.length}`)
  if (gaps.length) {
    for (const g of gaps) console.log(`  - ${g.category}.${g.id}: ${g.message}`)
  }
  console.log('\n## Files generated\n')
  for (const [name, content] of Object.entries(files)) {
    console.log(`### ${name}\n\`\`\`\n${content.trimEnd()}\n\`\`\`\n`)
  }
  console.log('Re-verify: POST https://isitagentready.com/api/scan', JSON.stringify({ url: www }))
}