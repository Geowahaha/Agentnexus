# Portable Agent Prompt: AI Visibility Audit

Use this prompt with any capable coding, browser, or infrastructure agent. Do not include API tokens, account secrets, private keys, passwords, or bearer tokens in chat.

```text
You are auditing and improving AI/search visibility for a public website.

Goal:
- Verify live production AI crawler access, agentic browsing readiness, llms.txt quality, robots/content-signal consistency, www/canonical health, and analytics coverage.
- Explain before/after traffic changes as likely contributors, not guaranteed causality.
- Do not ask for or print API tokens, account secrets, private keys, passwords, or bearer tokens.
- If Cloudflare or hosting authentication is needed, use the existing authenticated local environment or tell the user exactly which dashboard action to perform without exposing secrets.

Inputs:
- Production site URL: <SITE_URL>
- Hosting provider, if known: <HOSTING_PROVIDER>
- Desired public AI policy: ai-train=no, search=yes, ai-input=yes

If the attached skill folder is available and Node.js is installed, run one of:
- JSON automation output: `node scripts/audit_ai_visibility.mjs <SITE_URL>`
- Markdown report output: `node scripts/audit_ai_visibility.mjs <SITE_URL> --markdown`
- Windows wrapper: `scripts\audit-ai-visibility.bat <SITE_URL> --markdown`
- Windows portability check: `scripts\verify-portable.bat`
- macOS/Linux wrapper: `sh scripts/audit-ai-visibility.sh <SITE_URL> --markdown`

Live checks to run:
1. Fetch these URLs with cache-busting:
   - <SITE_URL>/
   - <SITE_URL>/robots.txt
   - <SITE_URL>/llms.txt
   - <SITE_URL>/ai.txt
   - <SITE_URL>/agents.txt
   - <SITE_URL>/sitemap.xml
   - https://www.<HOST>/

2. Test these user-agents against the homepage:
   - GPTBot
   - ClaudeBot
   - Google-Extended
   - OAI-SearchBot
   - ChatGPT-User
   - PerplexityBot

3. Verify:
   - Homepage returns 200.
   - Important AI bot user-agents return 200.
   - robots.txt has no ai-input=no.
   - Content-Signal is consistent with: ai-train=no, search=yes, ai-input=yes.
   - llms.txt has at least one H1 Markdown heading.
   - llms.txt has Markdown links like [Home](https://example.com/), not only bare URLs.
   - www host either redirects to the canonical host or returns a healthy 200.
   - No Cloudflare 522/520/403 blocks on canonical public pages.
   - GA4 or analytics coverage exists on intended public HTML pages if analytics is part of the request.

If fixing is needed:
- Fix policy conflicts before adding new features.
- Keep ai-train=no if the user wants training opt-out.
- Use ai-input=yes when the business wants AI assistants to cite/summarize public content for user answers.
- Do not deploy a whole repo root if it contains .git, .env*, secrets, internal docs, node_modules, .vercel, or tooling folders.
- For Cloudflare Pages, deploy a clean static/public bundle only, then purge cache for root, robots.txt, llms.txt, ai.txt, agents.txt, sitemap.xml, feed.xml, and key landing pages.
- For www 522, add www as the hosting custom domain or create a 301 redirect from www to the canonical host.

Traffic-lift analysis:
- Treat traffic growth as evidence-weighted, not automatically caused by the technical change.
- Strong likely contributors include bot unblocking, ai-input=yes, valid llms.txt links, fixed www errors, cleaner sitemap/feed discovery, and recrawl timing.
- Measurement contributors include adding GA4 to pages that previously were not tracked.
- Confirm with GA4 source/medium and landing pages, Search Console clicks/impressions, and Cloudflare request or bot logs.

Report format:
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
- Cloudflare bot/request logs
```
