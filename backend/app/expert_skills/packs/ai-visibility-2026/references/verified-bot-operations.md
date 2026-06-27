# Operating a Verified Bot / Signed Agent on Cloudflare (2026)

Use when building, registering, or operating an audit/crawler bot that needs cryptographic identity (Web Bot Auth) and listing in the Cloudflare Bots & Agents Directory. Battle-tested from registering AIBotAuth (the audit bot in this stack).

## The two identities — pick ONE per bot (cannot be both)
- **Verified Bot** = directed by the bot OWNER (search crawlers, monitoring, audit tools). This is what an audit/visibility scanner is.
- **Signed Agent** = carries out a goal directed by the END USER (autonomous agents acting per-user, e.g. an AI that books/buys on someone's behalf). Different policy, different registration.
- A single bot/keyid cannot register as both. If a product needs both surfaces (e.g. an audit bot AND a per-user agent), run them as separate bots with separate keys.

## Verification methods (choose by hosting reality)
- **Web Bot Auth (Request Signature)** — RFC 9421 Ed25519 HTTP Message Signatures. REQUIRED choice when the bot runs on shared egress IPs (Cloudflare Workers/Pages, most serverless). Form label may read "Request signature (beta)".
- **IP validation (Reverse DNS / IP List)** — only viable when you control dedicated, stable egress IPs. Do NOT pick this on Pages/Workers — egress is Cloudflare's shared pool and verification will fail.

## Web Bot Auth implementation checklist (what actually passes)
1. Ed25519 keypair; kid = RFC 7638 JWK thumbprint. On workerd: strip `alg`/`use`/`key_ops` before `crypto.subtle.importKey` (workerd rejects `alg:"Ed25519"`; spec value is `EdDSA`, but stripping is safest).
2. Key directory at `/.well-known/http-message-signatures-directory`, media type `application/http-message-signatures-directory+json`, body `{"keys":[<public JWK>]}`. Serve only PUBLIC keys (has `x`, never `d`).
3. **Directory self-signature** differs from request signatures:
   - Directory: component list `("@authority";req "signature-agent")`, `tag="http-message-signatures-directory"`, include `nonce` (32 random bytes, base64), `@authority` derived from the INCOMING request host.
   - Outgoing requests: plain `("@authority" "signature-agent")`, `tag="web-bot-auth"`, plus `Signature-Agent: "<origin>"`.
4. Sign every TARGET-site fetch with `signedFetch`; NEVER sign requests that wear another bot's User-Agent (bot-simulation/comparison modes stay unsigned — signing them is identity fraud).
5. Fail-open: missing key ⇒ plain fetch, so audits never break on identity.

## Validate BEFORE submitting (don't guess)
- `curl -sD- -o NUL "https://<origin>/.well-known/http-message-signatures-directory?v=x"` — confirm 200, correct media type, `Signature-Agent`, `("@authority";req ...)`, tag, nonce, Signature.
- **Cloudflare's live validator:** sign a GET to `https://crawltest.com/cdn-cgi/web-bot-auth`. Expected **401** = "unknown public key…for keyid" = format ACCEPTED, key just not registered yet → ready to submit. **400** = format problem (check field presence, @authority;req, alg). **200** = already registered.
- CLI option: `cargo install http-signature-directory` then validate the directory.

## The submission form (Manage Account → Configurations → Bot Submission Form)
Account-level, not zone-level. Fields:
- Bot name; "I own this bot"; **Bot documentation URL** = a public /bot page describing the bot (REQUIRED-quality: identity, UA, policy, opt-out, key-directory link, TH/EN if relevant).
- **Short description: HARD LIMIT 120 chars.** Write it tight up front.
- Bot type: Verified Bot.
- **Crawler category** (sticky, shows on Radar — pick honestly; Cloudflare reserves the right to re-assign if behavior differs):
  - Audit/visibility/monitoring tool → `Monitoring & Analytics` ("uptime, performance, traffic metrics").
  - SEO analysis tool → `Search Engine Optimization` (Lighthouse/GTmetrix/Pingdom class).
  - NEVER pick `AI Crawler`/`AI Search`/`AI Assistant` for a tool that promises no training-data collection — it contradicts the policy and many sites auto-block those categories.
  - Other categories: Academic Research, Accessibility, Advertising & Marketing, Aggregator, Archiver, Feed Fetcher, Page Preview, Search Engine Crawler, Security, Social Media Marketing, Webhooks, Other.
- Verification method: Request signature (beta).
- **Validation instructions** = the key-directory URL.
- UA header values (optional, recommended): full UA string, press Enter to chip it.
- UA match pattern (optional, recommended): a substring matching all the bot's UAs (e.g. the bot name), press Enter.

## Post-approval operating rules (the part everyone misses)
- Approval → listed on Cloudflare Radar verified-bots directory. Use this as public proof / sales asset.
- **DELISTING RISK:** a listed bot is delisted if Cloudflare sees NO traffic from it for a period (inactive IPs drop in ~24h). **You must run real signed scans regularly to stay listed.** Operationally: schedule recurring real audits (your own properties + customer scans) so the identity stays warm. A registered-but-idle bot quietly falls off.
- Benefit once verified: excluded from Bot Fight Mode by default, and sites can allow/segment you via `cf.verified_bot_category` in WAF rules — i.e. far fewer WAF blocks on your scans.
- Re-verify the directory + crawltest after ANY change to domain, keys, or signing code (regressions hide in merges — directory signature params are the usual casualty).

## Strategic note for an audit-bot business
Verified-bot status is a moat amplifier, not the moat: it makes the scanner trustworthy and un-spoofable, which lets you sell a signed "verified by <you>" proof certificate and own the rubric. The durable asset is the accumulating scan dataset + the standard you publish, not the signature itself. Keep the bot active (delisting rule) and version your audit standard publicly.
