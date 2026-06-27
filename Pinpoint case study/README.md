# Audit AI Visibility Skill

Portable skill pack for auditing and improving AI/search visibility on public websites. It checks live production URLs, AI crawler access, `robots.txt`, `llms.txt`, `ai.txt`, `agents.txt`, `www` health, canonical signals, and analytics hints.

No API tokens or secrets are required. Do not paste API tokens, private keys, passwords, bearer tokens, or hosting credentials into any agent prompt or log.

## Contents

- `SKILL.md` - main Codex skill instructions.
- `agents/openai.yaml` - optional Codex/OpenAI UI metadata.
- `scripts/audit_ai_visibility.mjs` - dependency-free Node.js audit script.
- `scripts/audit-ai-visibility.bat` - Windows/AgentNexus wrapper.
- `scripts/audit-ai-visibility.sh` - macOS/Linux shell wrapper.
- `scripts/verify-portable.bat` - Windows runtime check.
- `references/portable-agent-prompt.md` - prompt for agents that cannot load Codex skills.
- `references/agentnexus-runbook.md` - AgentNexus setup and workflow.
- `references/pinpoint-case-study.md` - before/after case study and traffic-lift reasoning.

## Requirements

- Node.js 18 or newer.
- Network access to the public website being audited.
- No npm install is needed.
- No API token is needed for audit-only use.

Check Node:

```bat
node -v
```

On Windows, run the portable check:

```bat
scripts\verify-portable.bat
```

## Quick Start

Windows / AgentNexus:

```bat
scripts\audit-ai-visibility.bat https://example.com --markdown
```

Windows JSON output for automation:

```bat
scripts\audit-ai-visibility.bat https://example.com
```

macOS/Linux:

```bash
sh scripts/audit-ai-visibility.sh https://example.com --markdown
```

Direct Node command:

```bash
node scripts/audit_ai_visibility.mjs https://example.com --markdown
```

## AgentNexus Use

1. Upload or attach the whole `audit-ai-visibility` folder.
2. Paste the contents of `references/portable-agent-prompt.md` into the AgentNexus agent instructions.
3. Tell the agent to run:

```bat
scripts\audit-ai-visibility.bat <SITE_URL> --markdown
```

4. For automation, run without `--markdown` and parse JSON:

```bat
scripts\audit-ai-visibility.bat <SITE_URL>
```

5. If fixes require Cloudflare, hosting, GA4, or Search Console access, use an already-authenticated local environment or dashboard steps. Do not paste credentials into chat.

## What The Audit Checks

- Homepage HTTP status and canonical tag.
- `robots.txt`, `llms.txt`, `ai.txt`, `agents.txt`, and `sitemap.xml`.
- `Content-Signal` header consistency.
- `ai-input=no` conflicts.
- `llms.txt` H1 and Markdown link count.
- `www` health and final URL.
- AI bot user-agent access for GPTBot, ClaudeBot, Google-Extended, OAI-SearchBot, ChatGPT-User, and PerplexityBot.
- GA4-like measurement ID presence and tracking loader hints.
- WebMCP attribute hints.

## Output

JSON output is best for agent pipelines. Important fields:

- `endpoints`
- `robotsPolicy`
- `llms`
- `homepage`
- `botChecks`
- `likelyIssues`

Markdown output is best for human reports.

## Interpreting Traffic Lift

Do not claim technical fixes caused all traffic growth without checking data. Common contributors:

- AI/search crawlers were unblocked.
- `ai-input=yes` allowed public content to be used for user-answer grounding.
- `llms.txt` became valid Markdown with links.
- `www` errors were fixed.
- Sitemap/feed/policy discovery became clearer.
- GA4 was added to more pages, increasing measured traffic coverage.
- Recrawl timing, campaigns, rankings, and seasonality overlapped.

Confirm with GA4 source/medium and landing pages, Search Console clicks/impressions, and CDN or hosting bot logs.

## Safe Case Summary: Pinpoint Accounting

This package was created after improving the public AI/search visibility of `https://pinpointaccountingservice.com/`. The case is included as a reusable pattern, not as a guarantee that every site will see the same lift.

No API tokens, account credentials, private keys, passwords, Cloudflare project IDs, or private customer data are included in this package.

Before improvement:

- Production hosting assumptions were unclear, so live checks had to confirm the actual production path first.
- AI/search bot access was reported as blocked or unreliable for important crawlers.
- Public policy signals were inconsistent, including `ai-input=no` where the business goal was AI answer visibility.
- `llms.txt` did not meet agentic browsing expectations because it lacked Markdown links.
- `www` returned a Cloudflare 522 error.
- Analytics coverage needed verification, so traffic changes could not be interpreted safely without separating real growth from measurement coverage.

Actions taken:

- Verified live production directly instead of relying on local files or non-production deploy output.
- Aligned public policy intent to `ai-train=no, search=yes, ai-input=yes`.
- Kept private routes such as `/api/` and form-confirmation pages out of public AI usage.
- Allowed important AI/search crawlers to access public pages.
- Reworked `llms.txt` into Markdown with an H1 and linked public discovery pages.
- Fixed `www` availability so the host no longer returned 522.
- Verified analytics presence while treating any traffic lift as evidence to analyze, not automatic proof of causality.

After improvement:

- Main public pages returned healthy `200` responses.
- Important AI bot user-agents returned `200`.
- `Content-Signal` was consistent with the desired public AI policy.
- `llms.txt` had a valid H1 and Markdown links.
- `www` no longer failed with 522.
- The site owner observed a traffic lift after the fixes.

Likely traffic-lift contributors:

- AI/search crawlers could reach public content more reliably.
- `ai-input=yes` matched the goal of letting AI assistants cite or summarize public pages for user answers.
- A valid `llms.txt` made the site easier for agents to browse.
- The `www` fix removed a broken entry point for users and crawlers.
- Analytics coverage changes may have increased measured traffic, so GA4 and Search Console should still be used to separate true demand growth from tracking improvements.

Use this case as a checklist for similar sites: confirm production first, remove policy conflicts, fix broken hosts, improve machine-readable discovery, validate with bot user-agents, and measure before/after carefully.

## Safe Fix Rules

- Keep `ai-train=no` when the user wants training opt-out.
- Use `search=yes, ai-input=yes` when the business wants AI assistants to cite or summarize public content.
- Keep private routes, admin paths, `/api/`, form submissions, credentials, and internal files out of public AI usage.
- Do not deploy a repo root if it includes `.git`, `.env*`, secrets, internal docs, `.vercel`, `node_modules`, or tooling folders.
- For Cloudflare Pages, deploy a clean public/static bundle and purge policy files after deployment.

## Troubleshooting

`Node.js was not found on PATH`:

- Install Node.js 18 or newer.
- Reopen the terminal or AgentNexus runner.

`fetch failed` or all endpoints are `ERR`:

- Confirm the machine has internet access.
- Confirm the URL starts with `https://` or is a valid domain.
- Check local firewall/proxy rules.

`www` is `522`, `520`, or `403`:

- Fix hosting/CDN routing.
- For Cloudflare, add `www` as a valid custom domain or create a 301 redirect to the canonical host.

`llms Markdown links` is `0`:

- Rewrite `llms.txt` as Markdown links like `[Home](https://example.com/)`, not only bare URLs.

## Secret Safety

This package contains no API tokens or secrets. Keep it that way. Redact credential-looking values before sharing logs or reports.
