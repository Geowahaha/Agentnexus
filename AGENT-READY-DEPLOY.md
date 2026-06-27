# Agent-Ready deploy bundle (SEO + AEO + AAIO + Revenue Attribution)

Generated for **https://www.obolla.com** (OBOLLA Agent-Ready Auto Fix).

## SEO (Traditional)
- Improve Core Web Vitals, on-page, internal links, schema.
- Target Google/Bing rankings + AI citations.

## AEO (AI Answer Engines)
- Use FAQ/HowTo schema, entity optimization, direct answers.
- Optimize for Perplexity, ChatGPT Search, Gemini, etc.

## AAIO (Agent Optimization)
- Full discovery stack (robots, llms, agents, MCP, commerce protocols).
- Make site legible and actionable for autonomous agents.

## Revenue Link (Closed Moat)
After deployment:
1. Log outreach or run relevant OBOLLA skills on the improved pages.
2. Track via moat: pre/post scan lift + skill executions.
3. Revenue attributed automatically (BillingTransaction + CreatorEarning records).
4. Use data for proprietary validation and better future recommendations.

Reference: successcasting.com (25% → 100% Level 5) — real revenue lift via agent visibility.

## Deploy
Static / Cloudflare Pages: Upload root (`wrangler pages deploy`).
Next.js: Copy public/* + add schema in layout/route.

## Verify + Attribute Revenue
```bash
node scripts/agent-ready-auto-deploy.mjs https://www.obolla.com --verify-only
```
Then run OBOLLA skills and check Creator Dashboard for attributed revenue.
