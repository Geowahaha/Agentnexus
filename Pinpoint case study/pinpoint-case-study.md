# Pinpoint Accounting AI Visibility Case Study

## Context

Production domain: `https://pinpointaccountingservice.com/`

Hosting reality discovered during the work: production was Cloudflare-only. Vercel deploy output was not production.

Business goal: increase AI/search visibility for a Thai accounting service site while keeping model-training opt-out.

Desired public content signal:

```text
ai-train=no, search=yes, ai-input=yes
```

This means public pages may be indexed, cited, summarized, and used for user-answer grounding, while training use is still denied.

## Before Fixes

Observed or reported problems:

- `robots.txt` and related policy surfaces used `ai-input=no`.
- AI bot audit tools reported critical bots such as GPTBot, ClaudeBot, and Google-Extended as blocked or unable to access the site.
- Cloudflare Managed robots.txt had been involved and needed to be disabled so the site's real policy could be served.
- `llms.txt` did not satisfy Lighthouse Agentic Browsing recommendations because it lacked usable Markdown links.
- Policy consistency was risky across `robots.txt`, `llms.txt`, `ai.txt`, `agents.txt`, `_headers`, and `vercel.json`.
- `www.pinpointaccountingservice.com` returned Cloudflare `522`, meaning the host was routed to an unavailable origin or not properly connected to Pages.
- GA4 coverage was missing or inconsistent across HTML pages before the analytics pass.
- WebMCP form annotations were not live on production, though this was unscored compared with crawler access and `llms.txt`.

## Changes Made

Policy and crawler access:

- Changed public AI content signal from `ai-input=no` to `ai-input=yes` while preserving `ai-train=no`.
- Kept private routes such as `/api/` and `/thank-you` disallowed/noindexed.
- Allowed AI/search crawlers including GPTBot, OAI-SearchBot, ChatGPT-User, ClaudeBot, Claude-User, Claude-SearchBot, Google-Extended, GoogleOther, PerplexityBot, Perplexity-User, Applebot, CCBot, Bytespider, Amazonbot, and meta-externalagent.
- Ensured no `ai-input=no` remained on the main policy surfaces.
- Added or confirmed `Content-Signal` response headers through Cloudflare headers.

Agentic browsing:

- Reworked `llms.txt` into Markdown with an H1 heading.
- Replaced bare URLs with Markdown links such as `[Home](https://pinpointaccountingservice.com/)`.
- Linked primary machine-readable discovery files: sitemap, feed, robots, ai policy, and agents policy.

Analytics:

- Added GA4 measurement ID `G-T1N30W3D87` across intended HTML pages.
- Added or adjusted tracking guard logic to avoid duplicate GA config when both an inline snippet and a loader exist.
- Important interpretation: adding GA4 can increase measured traffic even if real human traffic did not rise by the same amount.

Cloudflare and host routing:

- Treated Cloudflare as production and ignored Vercel output for production verification.
- Fixed `www.pinpointaccountingservice.com` from `522` to `200`.
- Canonical tag on both apex and `www` points to `https://pinpointaccountingservice.com/`.
- A 301 `www` to apex redirect remains cleaner for SEO, but the critical 522 failure was removed.

## After Fixes

Verified live production:

- Apex homepage: `200`.
- `robots.txt`: `200`, `ai-input=yes`, no `ai-input=no`.
- `llms.txt`: `200`, H1 present, Markdown link count changed from `0` to `27`.
- `www.pinpointaccountingservice.com`: changed from `522` to `200`.
- AI bot user-agents tested with `200`: GPTBot, ClaudeBot, Google-Extended, OAI-SearchBot, ChatGPT-User, PerplexityBot.
- `Content-Signal` header: `ai-train=no, search=yes, ai-input=yes`.

## Most Likely Reasons Traffic Increased

Strong contributors:

1. AI/search crawlers were no longer blocked from public pages. This improves eligibility for AI answers, citations, and crawler discovery.
2. `ai-input=yes` removed a direct policy conflict with the goal of letting ChatGPT, Claude, Perplexity, and similar systems use public content for answers.
3. `llms.txt` became machine-friendly Markdown with links, improving agentic browsing quality.
4. The `www` 522 fix removed a broken hostname, recovering requests from users and crawlers that entered via `www`.
5. Sitemap/feed/robots/agents references became clearer and more consistent.

Measurement contributor:

- GA4 coverage may have doubled measured traffic if pages that previously did not send analytics now send events. Always check whether the lift is in users/sessions from real sources or simply better measurement coverage.

Possible external contributors:

- Recrawl timing after Cloudflare purge/deploy.
- Search ranking changes.
- Referral or ad campaigns.
- Seasonality or business demand.
- Direct/brand traffic changes after DNS/cache stabilization.

## How To Prove The Lift

Check GA4:

- Compare date ranges before and after deploy.
- Segment by source/medium, landing page, country, device, and new vs returning users.
- Look for whether traffic growth appears on pages that newly received GA4.
- Compare page_view count with user/session count; a page_view-only jump may be instrumentation.

Check Google Search Console:

- Compare clicks, impressions, average position, indexed pages, and crawl stats.
- Look for query/page pairs that started rising after the policy deploy.

Check Cloudflare:

- Review bot analytics and request logs for GPTBot, ClaudeBot, Google-Extended, PerplexityBot, OAI-SearchBot, and ChatGPT-User.
- Confirm `www` requests are no longer 522.

Conclusion phrasing:

```text
Traffic likely increased because crawl access and machine-readable site policy improved, `www` errors were removed, and GA4 coverage became more complete. The exact share of real demand growth vs measurement improvement should be confirmed by GA4 source/medium and landing-page deltas, Search Console clicks/impressions, and Cloudflare bot/request logs.
```
