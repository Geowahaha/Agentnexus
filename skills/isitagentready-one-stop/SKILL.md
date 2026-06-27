---
name: isitagentready-one-stop
description: End-to-end implementation skill for improving an existing website to pass isitagentready.com checks, including Link headers, Markdown for Agents, robots/content signals, API catalog, OAuth/OIDC/Auth.md, MCP/A2A/agent skills, DNS-AID/DNSSEC, x402, MPP, UCP, ACP/AP2 commerce discovery, and Web Bot Auth JWKS. Use when a user asks to make a site agent-ready, fix isitagentready scanner failures, reach Level 5/100%, add agent discovery, add commerce discovery, or reproduce the Pinpoint/Successcasting agent-readiness workflow on Cloudflare/Vercel/static sites.
---

# IsItAgentReady One Stop

## Operating Principle

Optimize for scanner pass **and** truthful production behavior. Think like the site owner: avoid changes that improve a scanner while harming live traffic, DNS availability, payment integrity, or customer trust. Do not fake approvals, private credentials, licensed claims, DNSSEC validation, or production payments. It is acceptable to publish discovery metadata for planned/agent-payable flows when the metadata clearly says public lead/contact remains free and production settlement requires configured credentials.

Use this skill as a checklist-driven implementation sprint:

1. Inspect the current site and scanner output.
2. Identify framework, public output directory, deploy target, and DNS provider.
3. Implement missing discovery surfaces in code, not only in notes.
4. Deploy to the live canonical origin.
5. Run `POST https://isitagentready.com/api/scan`.
6. Iterate until all fixable categories pass.
7. If DNSSEC parent DS is missing, use the DNSSEC reset-once workflow only when appropriate, leave DNSSEC enabled, then report the exact waiting/registrar state instead of claiming 100%.

## Implementation Mode

When the user asks to "implement", "upgrade to Level 5/100%", or "make it completed", do the work end to end:

1. Run the scanner and direct endpoint checks first.
2. Patch the repository with static discovery files, route handlers, headers, and markdown negotiation.
3. Add Cloudflare DNS-AID records when Cloudflare credentials are available. If the domain uses another registrar, collect and report the required DS record.
4. Deploy to the production origin the user requested.
5. Re-run the scanner and fix remaining issues until the only blocker is an external DNSSEC/registrar propagation step or another credential-gated operation.

For static or Cloudflare Pages projects, prefer the bundled generator:

```bash
node skills/isitagentready-one-stop/scripts/create-agent-ready-kit.mjs \
  --root . \
  --public public \
  --origin https://example.com \
  --site-name "Example"
```

Use `--force` only after checking diffs. The generator creates the baseline files and Cloudflare Pages Functions needed for most scanner checks, but the agent must still review generated copy, adapt business-specific claims, wire deploy commands, and validate live output.

## Apply To Any Site

This skill is reusable across domains such as `obolla.com`, Pinpoint, Successcasting, or any other website. Treat every site as a fresh implementation:

1. Determine the live canonical origin after redirects, for example `https://obolla.com` or `https://www.example.com`.
2. Locate the repository root and the deploy/public output directory. Do not assume `public`; confirm from the framework config.
3. Run the scanner before edits and save the failing categories.
4. Generate or manually add the agent-ready kit using the site's own origin and brand name.
5. Adapt files to the framework and hosting provider:
   - Cloudflare Pages: `_headers` plus `functions/`.
   - Cloudflare Workers with assets: route discovery endpoints in the Worker and set `assets.run_worker_first: true` when static assets would otherwise bypass homepage Link headers or Markdown negotiation.
   - Vercel/Next.js: `next.config.js` headers plus route handlers or middleware.
   - Static-only hosting: static discovery files pass many checks, but Markdown negotiation and x402 require an edge/server layer.
6. Deploy to the production origin, not only preview.
7. Re-scan the live production URL and keep iterating until Level 5/100% or until only registrar/DNSSEC remains blocked.

Example for Obolla from its repo root:

```bash
node path/to/skills/isitagentready-one-stop/scripts/create-agent-ready-kit.mjs \
  --root . \
  --public public \
  --origin https://obolla.com \
  --site-name "Obolla"
```

If the project uses `dist`, `build`, `out`, or another output directory, change `--public` accordingly.

## Core Files To Add

For a static/Cloudflare Pages-style site, add these public endpoints:

- `/robots.txt`
- `/sitemap.xml`
- `/llms.txt`, `/ai.txt`, `/agents.txt`
- `/.well-known/api-catalog`
- `/.well-known/openapi.json` and `/openapi.json`
- `/.well-known/api-docs.md`
- `/auth.md`
- `/.well-known/oauth-protected-resource`
- `/.well-known/oauth-authorization-server`
- `/.well-known/openid-configuration`
- `/.well-known/jwks.json`
- `/.well-known/mcp/server-card.json`
- `/.well-known/agent-card.json`
- `/.well-known/agent-skills/index.json`
- `/.well-known/http-message-signatures-directory`
- `/.well-known/ucp`
- `/.well-known/acp.json`
- `/api/v1` or another protected route returning x402 `402`
- Cloudflare Pages: `_headers`, `functions/_middleware.js`, and `functions/api/v1.js`

For implementation patterns and compact JSON examples, read `references/implementation-checklist.md`.
For an end-to-end implementation playbook, read `references/level5-implementation-playbook.md`.

When using Cloudflare Workers, keep API routing precise: an exact `GET /api/v1` x402 discovery route can satisfy the scanner without breaking existing backend proxies under `/api/v1/*`.

## HTTP Discovery

Add RFC 8288 `Link` response headers at least on the homepage and ideally globally:

- `rel="api-catalog"` -> `/.well-known/api-catalog`
- `rel="service-desc"` -> `/openapi.json` and/or `/.well-known/openapi.json`
- `rel="service-doc"` -> `/.well-known/api-docs.md`, `/auth.md`
- `rel="service-meta"` -> `agents.txt`, `llms.txt`, `ai.txt`, Web Bot Auth JWKS, UCP, ACP
- OAuth/OIDC metadata links where useful

Set precise content types:

- API catalog: `application/linkset+json`
- OpenAPI: `application/vnd.oai.openapi+json;version=3.1`
- Markdown docs: `text/markdown`
- OAuth/UCP/ACP/A2A/MCP/Web Bot Auth JSON: `application/json` or `application/jwk-set+json`

Support Markdown for Agents by returning `text/markdown` when requests include `Accept: text/markdown`; keep HTML as the browser default.

## Auth And API Discovery

Auth.md pass usually requires all of:

- `/auth.md` with an H1 containing `Auth.md`
- `/.well-known/oauth-protected-resource` with `resource`, `authorization_servers`, `scopes_supported`, and `bearer_methods_supported: ["header"]`
- `authorization_servers` should list the issuer origin, not the metadata URL, if the scanner appends `/.well-known/oauth-authorization-server`
- `/.well-known/oauth-authorization-server` with matching `issuer`
- `agent_auth` with `skill`, `register_uri`, and at least one complete method
- Anonymous method example: `identity_types_supported: ["anonymous"]` plus `anonymous.credential_types_supported` and `anonymous.claim_uri`

Do not invent a real OAuth provider. If public APIs do not require bearer tokens, say so; still publish metadata for private/future API review where appropriate.

## Bot Access Control

Pass these checks:

- `robots.txt` with valid user-agent rules and AI crawler rules.
- Content Signals in `robots.txt` or headers where the site uses them.
- Web Bot Auth: publish a JWKS at `/.well-known/http-message-signatures-directory`.

The Web Bot Auth endpoint must return a JSON Web Key Set with at least one public key. Publish only public keys. Never publish private signing material.

## Commerce Discovery

Commerce checks can pass without turning a service website into a live ecommerce store:

- x402: expose a route such as `/api/v1` that returns HTTP `402` and a `PAYMENT-REQUIRED` header when no payment signature is present.
- MPP: serve `/openapi.json` with `x-payment-info` on payable operations.
- UCP: serve `/.well-known/ucp` with `protocol_version`, `services`, `capabilities`, and a top-level `ucp` object.
- ACP: serve `/.well-known/acp.json` with `protocol.name: "acp"`, `protocol.version`, `api_base_url`, `transports`, and `capabilities.services`.
- AP2: declare AP2 commerce extension in the A2A agent card if appropriate. Put extension declarations both at root `extensions` and `capabilities.extensions`; include `name`, `protocol`, `version`, `uri`, and `params.payment_protocol: "ap2"` variants because scanner implementations can be strict.

Be honest in metadata: public lead/contact flow can remain free; paid agent review can be marked as discovery/testnet/future production unless a real wallet/payment provider is configured.

## DNS-AID And DNSSEC

DNS-AID is the hardest check because HTTP changes cannot fake DNSSEC.

Create DNS-AID records under the authoritative DNS zone:

- `_index._agents.example.com`
- `_a2a._agents.example.com`

Cloudflare API pattern that has passed scanner checks:

- `TXT _index._agents` -> `agents=service-name:https`
- `HTTPS _index._agents` -> `priority: 1`, `target: example.com`, `value: "alpn=h2,h3"`
- optional equivalent `_a2a._agents`

Then verify:

- DNS answers exist for HTTPS/SVCB-compatible queries.
- DNSSEC `AD=true` from a validating resolver.
- Parent zone has DS record. For `.com`, this means the registrar must publish DS. If registrar is Vercel/Name.com/Cloudflare Registrar, use the correct account. If no authorized token/session exists, report the exact DS record and blocker.

Do not mark DNS-AID complete until parent DS is visible and validated.

### Cloudflare DNSSEC Reset-Once Guardrail

If Cloudflare DNSSEC is stuck in `pending` after records exist, reset it at most once:

1. PATCH DNSSEC to `disabled`.
2. Wait until Cloudflare API returns `status: "disabled"` and `ds: null`.
3. PATCH DNSSEC back to `active`.
4. Confirm final Cloudflare API status is `pending` or `active`, never `disabled`.
5. Stop resetting. Leave DNSSEC enabled and wait for Cloudflare Registrar or the parent registry to publish DS.

Never leave DNSSEC disabled. Repeated reset cycles can delay parent DS publication and create owner-level risk. After reset-once, poll DS/AD and scanner status; if still pending, report that Cloudflare/parent registry propagation is the remaining blocker.

Use the bundled helper when Cloudflare API credentials are available:

```bash
node skills/isitagentready-one-stop/scripts/reset-cloudflare-dnssec-once.mjs \
  --zone-id <zone-id> \
  --env-file .env.cf.txt
```

## Validation Commands

Scanner:

```bash
curl -s https://isitagentready.com/api/scan \
  -H "Content-Type: application/json" \
  -d "{\"url\":\"https://example.com\"}"
```

Important direct checks:

```bash
curl -I https://example.com/
curl -H "Accept: text/markdown" https://example.com/
curl https://example.com/.well-known/http-message-signatures-directory
curl -i https://example.com/api/v1
curl https://example.com/openapi.json
curl https://example.com/.well-known/ucp
curl https://example.com/.well-known/acp.json
```

DNS:

```bash
curl -s "https://cloudflare-dns.com/dns-query?name=_index._agents.example.com&type=HTTPS&do=1" -H "accept: application/dns-json"
curl -s "https://cloudflare-dns.com/dns-query?name=example.com&type=DS&do=1" -H "accept: application/dns-json"
```

Cloudflare DNSSEC reset-once:

```bash
node skills/isitagentready-one-stop/scripts/reset-cloudflare-dnssec-once.mjs --zone-id <zone-id> --env-file .env.cf.txt
```

## Completion Standard

Report a completed improvement only when live scanner output shows:

- Discoverability: all pass except DNSSEC only when registrar access is unavailable and documented.
- Content accessibility: Markdown for Agents pass.
- Bot access control: robots/content signals/Web Bot Auth pass.
- API/Auth/MCP/Skill discovery: all pass.
- Commerce: x402/MPP/UCP/ACP/AP2 pass.

If DNSSEC is waiting on Cloudflare/registrar propagation after reset-once, state: "Everything fixable from HTTP/app code is complete; DNS-AID 100% is waiting for parent DS/DNSSEC validation. DNSSEC has been re-enabled and must remain enabled while Cloudflare/registrar propagation completes."

If DNSSEC is blocked by registrar credentials, state: "Everything fixable from HTTP/app code is complete; DNS-AID 100% requires publishing DS at the registrar."

Do not stop after creating files. A Level 5/100% task is not complete until the live canonical origin has been scanned after deploy and the result is recorded.
