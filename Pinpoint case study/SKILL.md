---
name: audit-ai-visibility
description: Audit and improve a website's AI visibility, agentic browsing readiness, Cloudflare Pages deployment health, AI crawler access, robots.txt/llms.txt/ai.txt/agents.txt consistency, GA4 instrumentation, and before/after traffic lift analysis. Use when diagnosing traffic changes after SEO or AI bot fixes, checking GPTBot/ClaudeBot/Google-Extended access, fixing llms.txt recommendations, resolving www/Cloudflare 522 issues, or creating a before/after report for agentic search improvements.
---

# Audit AI Visibility

## Core Workflow

1. Confirm the live production host and hosting path first. Do not assume Vercel, Netlify, or Cloudflare Pages from repo files alone.
2. Capture a live baseline with cache-busting URLs before making claims. Check root HTML, `robots.txt`, `llms.txt`, `ai.txt`, `agents.txt`, `sitemap.xml`, `www`, and bot user-agents.
3. Compare live production to local/deploy artifacts. If live differs from local, treat the deploy target, branch, cache, or routing layer as the likely problem.
4. Fix conflicts before adding more signals. AI crawlers respond poorly to mixed policy such as `ai-input=no` in one place and `ai-input=yes` elsewhere.
5. Validate after deploy with the same checks. Report exact URLs, statuses, and counts instead of saying "looks good."
6. Explain traffic changes as evidence-weighted contributors, not guaranteed causality. Separate real traffic lift from analytics coverage changes.

Run the bundled audit script for a quick production snapshot:

```powershell
node scripts/audit_ai_visibility.mjs https://example.com
```

For Windows or AgentNexus command runners, use the batch wrapper:

```bat
scripts\audit-ai-visibility.bat https://example.com --markdown
```

For macOS/Linux command runners:

```bash
sh scripts/audit-ai-visibility.sh https://example.com --markdown
```

When using a non-Codex agent that cannot load skills directly, paste `references/portable-agent-prompt.md` into that agent and attach or copy the script if it can run Node.js.

For AgentNexus-specific setup, read `references/agentnexus-runbook.md`.

For portable installation and troubleshooting, read `README.md`.

## High-Value Checks

For AI visibility, verify these signals:

- `robots.txt` returns `200`, has no `ai-input=no`, and explicitly allows important AI/search crawlers when the business wants AI answer visibility.
- Response headers and policy files agree on `Content-Signal: ai-train=no, search=yes, ai-input=yes` when the desired posture is "do not train, but allow search and user-answer grounding."
- `llms.txt` is Markdown, starts with at least one H1, and contains Markdown links like `[Home](https://example.com/)`, not only bare URLs.
- GPTBot, ClaudeBot, Google-Extended, OAI-SearchBot, ChatGPT-User, and PerplexityBot can fetch the homepage with `200`.
- `www` either redirects to the canonical host or serves correctly. A Cloudflare `522` on `www` is a routing/DNS/origin problem, not an llms.txt problem.
- Sitemap and feed URLs are discoverable from `robots.txt` and `llms.txt`.
- GA4 exists across intended pages. Treat a traffic jump after GA4 rollout as possibly measurement coverage, not only demand growth.
- WebMCP form annotations are helpful for agent interaction, but may be unscored. Do not over-prioritize them above crawl access, policy consistency, and broken hosts.

## Traffic Lift Attribution

When traffic rises after fixes, evaluate these likely drivers:

- **Measured traffic coverage:** GA4 added to missing pages can make traffic appear to double even if users did not double.
- **Crawl eligibility:** Changing `ai-input=no` to `ai-input=yes` allows AI agents to use public content for user-answer grounding while keeping `ai-train=no`.
- **Bot reachability:** Removing Cloudflare/robots blocks for GPTBot, ClaudeBot, Google-Extended, PerplexityBot, and OAI crawlers increases the chance of AI search discovery and citations.
- **Agentic browse quality:** A valid `llms.txt` with H1 and Markdown links helps AI agents understand site structure.
- **Host availability:** Fixing `www` 522 recovers requests, reduces errors, and avoids losing users or crawlers who use the `www` host.
- **Discoverability:** Clean sitemap/feed references and public policy files improve machine navigation.
- **Time-based confounders:** Campaigns, seasonality, ranking changes, recrawl timing, and referral spikes can coincide with technical fixes.

Phrase conclusions like: "The strongest likely contributors are X and Y; Z may be measurement-related; confirm in GA/Search Console by source/medium, landing page, and first_seen timing."

## Cloudflare Fix Pattern

For Cloudflare-only production:

- Do not deploy to Vercel or diagnose Vercel output as production.
- Do not deploy a repo root directly if it contains secrets, internal docs, `.env*`, `.git`, `.vercel`, or tooling folders.
- Deploy a clean static bundle to Cloudflare Pages, then purge cache for root, policy files, sitemap, feed, and key landing pages.
- For `www` 522, add `www` as a Pages custom domain or create a Cloudflare 301 Redirect Rule to the apex host. Prefer a redirect when the apex is canonical.

## Report Template

Use this compact structure:

```text
Checked live production:
- URLs:
- Bot user-agents:
- Cache-busting used:

Before:
- Blocking/conflicting policies:
- Invalid llms.txt:
- Broken hosts:
- Missing analytics/measurement:

After:
- robots/content-signal:
- llms H1/link count:
- bot access:
- www/canonical:
- GA4 coverage:

Likely traffic lift drivers:
1. ...
2. ...
3. ...

Remaining risks:
- ...

Next validation:
- GA4 source/medium and landing pages
- Search Console crawl/index data
- AI bot logs/Cloudflare analytics
```

For the Pinpoint Accounting case, read `references/pinpoint-case-study.md`.

## Secret Safety

Do not ask the user to paste API tokens, account secrets, private keys, or password values into chat. For deploy or purge steps, instruct the user or their deployment agent to use existing authenticated environments, dashboard actions, or local environment variables that are never printed.

Never include secrets in reports. Redact any accidental credential-looking value before summarizing output.

## Skill Maintenance

Keep `agents/openai.yaml` synced when the skill's purpose changes. It affects the Codex UI label, short description, default prompt, and whether the skill may be invoked implicitly; it does not affect the website, Cloudflare, AI crawlers, or traffic.

Use `SKILL.md`, references, and scripts for actual audit/improvement logic. Use `agents/openai.yaml` only for packaging metadata:

- `display_name`: human-facing skill name.
- `short_description`: concise UI summary.
- `default_prompt`: one short prompt that explicitly mentions `$audit-ai-visibility`.
- `policy.allow_implicit_invocation`: keep `true` if this skill should appear automatically for AI visibility, crawler, or traffic-lift audit requests.

Do not put secrets, Cloudflare tokens, project IDs, or live client credentials in `agents/openai.yaml`.
