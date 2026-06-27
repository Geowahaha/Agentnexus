# Implementation Checklist

## Minimal JSON Shapes

API catalog:

```json
{
  "linkset": [
    {
      "anchor": "https://example.com/api",
      "service-desc": [{ "href": "https://example.com/openapi.json", "type": "application/vnd.oai.openapi+json;version=3.1" }],
      "service-doc": [{ "href": "https://example.com/.well-known/api-docs.md", "type": "text/markdown" }],
      "service-meta": [{ "href": "https://example.com/auth.md", "type": "text/markdown" }]
    }
  ]
}
```

OAuth Protected Resource:

```json
{
  "resource": "https://example.com",
  "authorization_servers": ["https://example.com"],
  "scopes_supported": ["public:read"],
  "bearer_methods_supported": ["header"]
}
```

Authorization Server `agent_auth`:

```json
{
  "issuer": "https://example.com",
  "authorization_endpoint": "https://example.com/api/oauth/authorize",
  "token_endpoint": "https://example.com/api/oauth/token",
  "jwks_uri": "https://example.com/.well-known/jwks.json",
  "agent_auth": {
    "skill": "https://example.com/auth.md",
    "register_uri": "https://example.com/agent-registration",
    "identity_types_supported": ["anonymous"],
    "credential_types_supported": ["none"],
    "claim_uri": "https://example.com/auth.md#anonymous-claims",
    "revocation_uri": "https://example.com/auth.md#anonymous-revocation",
    "methods": [
      {
        "identity_type": "anonymous",
        "credential_types_supported": ["none"],
        "claim_uri": "https://example.com/auth.md#anonymous-claims",
        "revocation_uri": "https://example.com/auth.md#anonymous-revocation"
      }
    ],
    "anonymous": {
      "credential_types_supported": ["none"],
      "claim_uri": "https://example.com/auth.md#anonymous-claims",
      "revocation_uri": "https://example.com/auth.md#anonymous-revocation"
    }
  }
}
```

Web Bot Auth JWKS:

```json
{
  "keys": [
    {
      "kty": "OKP",
      "crv": "Ed25519",
      "kid": "example-web-bot-auth-2026",
      "use": "sig",
      "alg": "EdDSA",
      "x": "BASE64URL_PUBLIC_KEY_32_BYTES"
    }
  ]
}
```

UCP:

```json
{
  "protocol_version": "2026-04-08",
  "services": {},
  "capabilities": {},
  "endpoints": {},
  "ucp": {
    "version": "2026-04-08",
    "services": {},
    "capabilities": {}
  }
}
```

ACP:

```json
{
  "protocol": { "name": "acp", "version": "1.0.0" },
  "api_base_url": "https://example.com/api/commerce",
  "transports": ["rest", "a2a"],
  "capabilities": { "services": ["catalog_lookup", "checkout_session"] }
}
```

A2A Agent Card AP2 extensions:

```json
{
  "protocolVersion": "0.3.0",
  "version": "1.0.0",
  "supportedInterfaces": [{ "transport": "JSONRPC", "url": "https://example.com/" }],
  "defaultInputModes": ["text/plain", "application/json"],
  "defaultOutputModes": ["text/plain", "application/json"],
  "name": "Example Agent",
  "url": "https://example.com",
  "capabilities": {
    "streaming": false,
    "pushNotifications": false,
    "extensions": [
      { "uri": "https://x402.org", "name": "x402", "protocol": "x402", "version": "1", "required": false },
      { "uri": "https://paymentauth.org", "name": "MPP", "protocol": "mpp", "version": "1", "required": false },
      { "uri": "https://agentpayments.org/ap2", "name": "AP2", "protocol": "ap2", "version": "1.0", "required": false, "params": { "payment_protocol": "ap2" } },
      { "uri": "https://payments.google.com/ap2", "name": "AP2", "protocol": "ap2", "version": "1.0", "required": false, "params": { "payment_protocol": "ap2" } }
    ],
    "payment_protocols": ["x402", "mpp", "ap2"]
  },
  "extensions": [
    { "uri": "https://agentpayments.org/ap2", "name": "AP2", "protocol": "ap2", "version": "1.0", "required": false, "params": { "payment_protocol": "ap2" } }
  ]
}
```

## x402 Route Behavior

MPP `x-payment-info` inside OpenAPI payable operation should include top-level fields and method details:

```json
{
  "intent": "charge",
  "method": "card",
  "amount": "1.00",
  "currency": "USD",
  "methods": [{ "method": "card", "amount": "1.00", "currency": "USD" }],
  "description": "Discovery metadata for agent-native payment negotiation. Public website browsing remains free."
}
```

Unauthenticated request:

- Status: `402`
- Header: `PAYMENT-REQUIRED: <base64url-or-base64 payment requirements>`
- JSON body with `x402Version`, `error`, `resource`, and `accepts`.

Paid/signed request:

- Check for `payment-signature`, `PAYMENT-SIGNATURE`, or `x-payment`.
- If no production facilitator verification exists, do not claim payment settled. Return a clearly labeled discovery/test payload only.

## Common Scanner Failure Fixes

- Auth.md says protected resource missing: add `scopes_supported` and `bearer_methods_supported: ["header"]`.
- Auth.md fetches `/.well-known/oauth-authorization-server/.well-known/oauth-authorization-server`: `authorization_servers` is wrong; use issuer origin.
- Auth.md says `agent_auth` missing: add complete `anonymous` method.
- A2A card returns HTML: create `/.well-known/agent-card.json` and set JSON content type.
- AP2 stays neutral: put AP2 declarations in both root `extensions` and `capabilities.extensions`, with `name: "AP2"`, `protocol: "ap2"`, and `params.payment_protocol: "ap2"`.
- UCP missing `ucp` field: include both top-level `protocol_version/services/capabilities/endpoints` and nested `ucp`.
- Web Bot Auth returns HTML: create `/.well-known/http-message-signatures-directory` and set `application/jwk-set+json`.
- DNS-AID found but DNSSEC not validated: check parent DS. On Cloudflare, reset DNSSEC once only, re-enable immediately, then wait for parent DS propagation. HTTP deploy cannot fix missing DS.
