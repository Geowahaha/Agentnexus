---
name: agent-ready-auto-fix
description: Paid agent-readiness auto-fix — scan any URL with isitagentready.com taxonomy, generate full deployable fix pack (robots, llms, protocol stubs, commerce layer), stack-specific deploy steps, and re-verify checklist. Reference implementation successcasting.com 100% Level 5.
---

# Agent-Ready Auto Fix Pro

**URL in → Level 5 fix pack out.** Targets [isitagentready.com](https://isitagentready.com/) All Checks — same 5 categories buyers see in the UI.

| Category | What we auto-generate |
|----------|----------------------|
| Discoverability | robots.txt, sitemap refs, Link headers, DNS-AID playbook |
| Content | Markdown negotiation routes / CF toggle steps |
| Bot Access | Content-Signal in robots + headers |
| API, Auth, MCP | api-catalog, OAuth discovery, auth.md, MCP card, agent-skills, WebMCP hints |
| Commerce | UCP, ACP, openapi MPP, x402 /api/v1 stub (when product schema detected) |

## Workflow

1. **Scan** — AIBotAuth MCP + isitagentready category mapping
2. **Gap map** — P0/P1/P2 per failing check with file paths
3. **Fix pack** — Full file contents from templates (not placeholders)
4. **Deploy guide** — Next.js / Cloudflare / WordPress / static paths
5. **QA + re-verify** — Checklist + `POST isitagentready.com/api/scan` command

## Reference site

**successcasting.com** — documented 25% → 100% Level 5 Agent-Native.  
Read `references/successcasting-100-playbook.md` before generating protocol/commerce stubs.

## Honest limits (tell buyer upfront)

- **DNS-AID** — requires DNS panel access (script gives exact SVCB records)
- **x402** — needs wallet + deploy; we ship working 402 header template
- **OAuth/MCP** — stubs point to real routes on buyer origin; never invent paid APIs
- **Auto-deploy** — paste-ready files + commands; git/CF API deploy is buyer step unless they grant access

## Non-negotiable

- Policy one source: robots.txt, llms.txt, ai.txt, agents.txt, Content-Signal agree
- llms.txt uses Markdown links only
- No secrets in output
- Re-verify link in every delivery footer