#!/usr/bin/env node
/**
 * Phase 3 orchestrator — analyze, generate fix pack, deploy (GitHub PR / CF Pages), verify.
 *
 * Usage:
 *   node scripts/agent-ready-auto-deploy.mjs https://example.com
 *   node scripts/agent-ready-auto-deploy.mjs https://example.com --verify-only
 *   node scripts/agent-ready-auto-deploy.mjs https://example.com --github-pr owner/repo
 *   node scripts/agent-ready-auto-deploy.mjs https://example.com --cf-pages my-project
 *   node scripts/agent-ready-auto-deploy.mjs https://example.com --api https://obolla.com/api/v1
 */
import { spawnSync } from 'node:child_process'
import { mkdirSync, writeFileSync } from 'node:fs'
import { resolve, dirname } from 'node:path'
import { fileURLToPath } from 'node:url'

const __dirname = dirname(fileURLToPath(import.meta.url))
const repoRoot = resolve(__dirname, '..')

const args = process.argv.slice(2)
const verifyOnly = args.includes('--verify-only')
const url = args.find((a) => a.startsWith('http'))
const apiBase = (
  args.includes('--api') ? args[args.indexOf('--api') + 1] : 'https://obolla.com/api/v1'
).replace(/\/+$/, '')

const githubRepo = args.includes('--github-pr')
  ? args[args.indexOf('--github-pr') + 1]
  : null
const cfPagesProject = args.includes('--cf-pages')
  ? args[args.indexOf('--cf-pages') + 1]
  : null
const baseBranch = args.includes('--base-branch')
  ? args[args.indexOf('--base-branch') + 1]
  : 'main'
const cfBranch = args.includes('--cf-branch') ? args[args.indexOf('--cf-branch') + 1] : 'main'

if (!url) {
  console.error(
    'Usage: node scripts/agent-ready-auto-deploy.mjs <url> [--verify-only] [--github-pr owner/repo] [--cf-pages project] [--api base]',
  )
  process.exit(1)
}

async function apiPost(path, body) {
  const res = await fetch(`${apiBase}/agent-ready${path}`, {
    method: 'POST',
    headers: { 'content-type': 'application/json' },
    body: JSON.stringify(body),
  })
  const text = await res.text()
  if (!res.ok) throw new Error(`${path} ${res.status}: ${text}`)
  return JSON.parse(text)
}

async function main() {
  const outDir = resolve(repoRoot, '.agent-ready-out', new URL(url).hostname)
  mkdirSync(outDir, { recursive: true })

  if (!verifyOnly) {
    console.log('==> Analyze (stack + isitagentready)')
    const analysis = await apiPost('/analyze', { url })
    writeFileSync(resolve(outDir, 'analyze.json'), JSON.stringify(analysis, null, 2))
    console.log(
      `Platform: ${analysis.stack.platform} | Score: ${analysis.scan.summary.percent}% | Gaps: ${analysis.scan.summary.fail}`,
    )

    console.log('==> Generate fix pack (local)')
    const gen = spawnSync(
      process.execPath,
      [resolve(repoRoot, 'scripts/agent-ready-fix-generator.mjs'), url, '--out', outDir],
      { encoding: 'utf8', cwd: repoRoot },
    )
    if (gen.status !== 0) {
      console.error(gen.stderr || gen.stdout)
      process.exit(gen.status ?? 1)
    }
    console.log(`Fix pack: ${outDir}`)

    if (githubRepo) {
      console.log(`==> GitHub PR deploy (${githubRepo})`)
      const pr = await apiPost('/deploy/github-pr', {
        url,
        repo: githubRepo,
        base_branch: baseBranch,
      })
      writeFileSync(resolve(outDir, 'github-pr.json'), JSON.stringify(pr, null, 2))
      console.log(`PR: ${pr.github?.pull_request_url}`)
    }

    if (cfPagesProject) {
      console.log(`==> Cloudflare Pages deploy (${cfPagesProject})`)
      const pages = await apiPost('/deploy/cloudflare-pages', {
        url,
        project_name: cfPagesProject,
        branch: cfBranch,
        wait: true,
      })
      writeFileSync(resolve(outDir, 'cf-pages.json'), JSON.stringify(pages, null, 2))
      console.log(
        `Deployment: ${pages.pages?.deployment_id} — ${pages.pages?.url ?? pages.pages?.deployment_status}`,
      )
    }

    if (!githubRepo && !cfPagesProject) {
      console.log('Deploy: use --github-pr owner/repo or --cf-pages project, or upload fix pack manually')
    }
  }

  console.log('==> Verify loop (isitagentready + optional CF purge)')
  const verify = await apiPost('/verify', {
    url,
    target_percent: 95,
    max_attempts: verifyOnly ? 3 : 1,
    purge_between: true,
  })
  writeFileSync(resolve(outDir, 'verify.json'), JSON.stringify(verify, null, 2))

  const last = verify.attempts?.[verify.attempts.length - 1]
  console.log(
    `Verify: ${verify.success ? 'PASS' : 'INCOMPLETE'} — ${last?.percent ?? '?'}% Level ${last?.level ?? ''} ${last?.level_name ?? ''}`,
  )
  if (!verify.success && verify.hint) console.log(verify.hint)
  process.exit(verify.success ? 0 : 2)
}

main().catch((err) => {
  console.error(err.message)
  process.exit(1)
})