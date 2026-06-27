# successcasting.com — 100% playbook (copy patterns, not NAP)

Production reference: https://www.successcasting.com — Level 5 Agent-Native.

## File map (Next.js App Router)

| Check | Path |
|-------|------|
| robots.txt | `app/robots.txt/route.ts` + `lib/seo/robots.ts` |
| llms.txt / ai.txt / agents.txt | `app/{llms,ai,agents}.txt/route.ts` |
| Link headers | `next.config.ts` headers() |
| api-catalog | `app/.well-known/api-catalog/route.ts` |
| agent-skills | `app/.well-known/agent-skills/index.json/route.ts` |
| MCP card | `app/.well-known/mcp/server-card.json/route.ts` |
| A2A card | `app/.well-known/agent-card.json/route.ts` |
| OAuth | `app/.well-known/oauth-authorization-server/route.ts` |
| auth.md | `app/auth.md/route.ts` |
| Markdown | `app/api/markdown/[...path]/route.ts` |
| UCP / ACP | `app/.well-known/ucp/route.ts`, `app/.well-known/acp.json/route.ts` |
| MPP | `app/openapi.json/route.ts` |
| x402 | `app/api/v1/route.ts` + `lib/commerce/x402Payment.ts` |
| WebMCP | `data-tool*` on RFQ form (server-rendered) |
| DNS-AID | Cloudflare DNS SVCB at `_index._agents.www` |

## x402 v2 (scanner requirement)

`GET /api/v1` without payment → **402** with header:

```
PAYMENT-REQUIRED: <base64 JSON>
```

Payload: `x402Version: 2`, `resource.url` = canonical site URL, `accepts[].network` = `eip155:84532`, USDC asset, `amount: "10000"`.

**Do not** set duplicate payment-required headers (breaks base64 validation).

## Commerce optional

isitagentready marks Commerce "Optional" in UI but scores 100 when product schema exists. Generate commerce stubs when scan reports `isCommerce: true`.