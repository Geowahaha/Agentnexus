# Level 5 Implementation Playbook

Use this reference when the user wants implementation, not just an audit.

## 1. Classify The Site

Find:

- Canonical origin: production URL with final redirect target.
- Framework: static HTML, Next.js, Astro, Vite, Cloudflare Pages, Vercel, or other.
- Public directory: commonly `public`, `dist`, `build`, `out`, or project root.
- Edge/runtime layer: Cloudflare Pages Functions, Workers, Vercel middleware/functions, Netlify functions, or static-only hosting.
- DNS authority: Cloudflare, Vercel, registrar DNS, or another provider.

Do not assume missing routes are real files when the server returns `200 text/html`; treat that as a soft-404 until content type and body validate.

For each new website, create a short implementation map before editing:

- `origin`: final production URL to scan.
- `repo_root`: directory where code changes should be made.
- `public_dir`: directory copied to the web root.
- `runtime`: Cloudflare Pages Functions, Workers, Vercel, Netlify, server framework, or static-only.
- `deploy_command`: command that pushes to production.
- `dns_provider`: where DNS-AID records must be created.
- `registrar`: where DS/DNSSEC delegation must be completed.

Owner rule: do not optimize the scanner at the expense of the live site. Avoid breaking existing API proxies, static asset delivery, login, payment, or DNSSEC state.

## 2. Fast Path For Static Or Cloudflare Pages

Run the bundled generator from the repository root:

```bash
node skills/isitagentready-one-stop/scripts/create-agent-ready-kit.mjs \
  --root . \
  --public public \
  --origin https://example.com \
  --site-name "Example"
```

Then inspect the diff. If files already exist and need controlled replacement, re-run with `--force` after reviewing user changes.

The generator creates:

- Search and agent text files: `robots.txt`, `sitemap.xml`, `llms.txt`, `ai.txt`, `agents.txt`, `auth.md`
- JSON discovery: API catalog, OpenAPI, OAuth/OIDC, MCP, A2A, agent skills, Web Bot Auth JWKS, UCP, ACP
- Cloudflare Pages headers and middleware for Link headers, Markdown for Agents, content types, and JSON/Markdown routing
- Cloudflare Pages x402 discovery route at `functions/api/v1.js`

## 3. Framework-Specific Integration

Cloudflare Pages:

- Use `_headers` for static file content types and Link headers.
- Use `functions/_middleware.js` for global Link headers and `Accept: text/markdown`.
- Use `functions/api/v1.js` for x402 402 responses.

Cloudflare Workers with assets:

- Add agent-ready routes in the Worker so content types and headers are exact.
- Set `assets.run_worker_first: true` when the homepage is served directly from assets and therefore misses Worker-added Link headers or Markdown negotiation.
- Keep the x402 scanner route exact, for example `GET /api/v1`, so existing backend proxy routes such as `/api/v1/*` keep working.
- Add global Link and Content-Signal headers in the Worker response wrapper.
- Inject WebMCP only into HTML responses; do not alter JSON, XML, Markdown, or binary assets.

Vercel/Next.js:

- Convert `_headers` rules to `next.config.js` `headers()` or middleware.
- Add route handlers under `app/.well-known/.../route.ts` or `pages/api`.
- Implement Markdown negotiation in middleware or the homepage route.
- Add x402 to an API route that intentionally returns `402` when unsigned.

Static hosting without functions:

- Static discovery files can pass most non-dynamic checks.
- Markdown negotiation and x402 generally require edge/server support.
- If no edge layer is available, recommend moving those endpoints to Cloudflare Pages Functions, Workers, Vercel Edge Middleware, or a reverse proxy.

## 4. DNS-AID

Create records in the authoritative zone:

- `TXT _index._agents` -> `agents=<service-slug>:https`
- `HTTPS _index._agents` -> priority `1`, target `<root-domain>`, params `alpn=h2,h3`
- `TXT _a2a._agents` -> `a2a=<origin>/.well-known/agent-card.json`
- `HTTPS _a2a._agents` -> priority `1`, target `<root-domain>`, params `alpn=h2,h3`

Then enable DNSSEC at the DNS host and publish the DS record at the registrar. For `.com`, a validating resolver must return authenticated data for the scanner to pass. If the parent DS is missing, the website code cannot fix it.

### Cloudflare DNSSEC Pending Pattern

If Cloudflare DNSSEC is stuck at `pending` while the DNS-AID records exist:

1. Reset once only.
2. PATCH DNSSEC to `disabled`.
3. Poll until Cloudflare API returns `status: "disabled"` and `ds: null`.
4. PATCH DNSSEC to `active`.
5. Confirm the final state is `pending` or `active`; if it is `disabled`, immediately enable it again.
6. Stop making DNSSEC state changes and wait for Cloudflare Registrar/parent registry DS publication.

Never leave DNSSEC disabled. Never keep cycling disable/enable. Repeated resets can restart the registrar workflow and delay the owner outcome. After reset-once, poll:

- Cloudflare DNSSEC API status.
- `DS` for the apex domain from Cloudflare DoH and Google DoH.
- `HTTPS` for `_index._agents.<domain>` with `do=1` and `AD=true`.
- Scanner result.

When Cloudflare DNSSEC is `pending` and parent DS count is `0`, report "waiting for parent DS propagation" rather than making further destructive DNSSEC changes.

## 5. Scanner Iteration

After deploy:

1. Scan with `POST https://isitagentready.com/api/scan`.
2. Directly fetch every failing endpoint and verify status, content type, and body.
3. Fix soft-404s before changing schema content.
4. Re-scan until all HTTP/app checks pass.
5. Record DNSSEC or payment-provider limitations honestly.

Useful live-readiness target:

- Discoverability: `robots.txt`, `sitemap.xml`, Link headers, DNS-AID.
- Content: Markdown negotiation.
- Bot access: AI rules, Content Signals, Web Bot Auth JWKS.
- API/Auth/MCP: API catalog, Auth.md, OAuth/OIDC, protected resource metadata, MCP, A2A, agent skills, WebMCP where applicable.
- Commerce: x402, MPP, UCP, ACP, AP2.

Use the live score honestly. A result such as Level 5 with `20 pass / 1 fail` and only DNSSEC pending is not a code failure; it is a parent DS propagation/registrar state.

## 6. Truthfulness Rules

- Do not publish private signing keys. Web Bot Auth needs public JWKS only.
- Do not claim production payment settlement unless a real facilitator/wallet/provider verifies it.
- Do not invent OAuth clients, license numbers, staff credentials, or approvals.
- Metadata can describe discovery/test flows, planned agent registration, and human-assisted paid review when labeled clearly.
- Do not leave DNSSEC disabled after troubleshooting. The safe owner state is enabled/pending while waiting for parent DS.
