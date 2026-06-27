import { BridgeHub } from './bridge-hub'
import { handleBridgeInstallRequest } from './bridge-install-handlers'
import { handleBridgePairingEdge } from './bridge-pairing-edge'
import { handleBridgeRequest, handleInternalBridgeDispatch } from './bridge-handlers'
import { NotificationHub } from './notification-hub'
import {
  handleInternalPublish,
  handleNotificationRequest,
  processNotificationBatch,
  type NotificationEnv,
} from './notification-handlers'
import type { NotifyQueueMessage } from './notification-types'
import type { BridgeEnv } from './bridge-types'
import { handleSpeechTranscribe } from './speech-handlers'

export { BridgeHub, NotificationHub }

export interface Env extends NotificationEnv, BridgeEnv {
  ASSETS: Fetcher
  AI: Ai
  BACKEND_URL: string
  OPENAI_API_KEY?: string
  APP_NAME: string
  PUBLIC_URL: string
}

const AGENT_READY_MARKER = 'obolla-agent-ready-2026-06-25'
const BOT_UA_PATTERN = /GPTBot|OAI-SearchBot|ChatGPT-User|ClaudeBot|Claude-SearchBot|PerplexityBot|Googlebot|bingbot|Applebot|Bytespider/i
const AGENT_READY_ORIGIN = 'https://obolla.com'
const AGENT_READY_SITE_NAME = 'OBOLLA'
const AGENT_READY_CONTENT_SIGNAL = 'ai-train=yes, ai-input=yes, search=yes'
const AGENT_READY_WEB_BOT_JWKS = {
  keys: [
    {
      kty: 'OKP',
      crv: 'Ed25519',
      kid: 'obolla-web-bot-auth-2026',
      use: 'sig',
      alg: 'EdDSA',
      x: 'kiQr8V_p2JF-3jlnhYFpXht8Et8MvzNqkEG6nW6mnwY',
    },
  ],
}
const AGENT_READY_PAYMENT_EXTENSIONS = [
  { uri: 'https://x402.org', name: 'x402', protocol: 'x402', version: '1', description: 'x402 payment discovery route', required: false },
  { uri: 'https://paymentauth.org', name: 'MPP', protocol: 'mpp', version: '1', description: 'MPP payment discovery metadata', required: false },
  { uri: 'https://agentpayments.org/ap2', name: 'AP2', protocol: 'ap2', version: '1.0', description: 'AP2-compatible commerce discovery', required: false, params: { payment_protocol: 'ap2' } },
  { uri: 'https://payments.google.com/ap2', name: 'AP2', protocol: 'ap2', version: '1.0', description: 'Agent Payments Protocol discovery', required: false, params: { payment_protocol: 'ap2' } },
  { uri: 'https://github.com/google-agentic-commerce/ap2', name: 'AP2', protocol: 'ap2', version: '1.0', description: 'Agent Payments Protocol extension', required: false, params: { payment_protocol: 'ap2' } },
  { uri: 'https://a2a-protocol.org/extensions/ap2', name: 'AP2', protocol: 'ap2', version: '1.0', description: 'A2A AP2 extension declaration', required: false, params: { payment_protocol: 'ap2' } },
]

function agentReadyOrigin(env: Env): string {
  return (env.PUBLIC_URL || AGENT_READY_ORIGIN).replace(/\/$/, '')
}

function agentReadyLinks(origin: string): string {
  return [
    `<${origin}/.well-known/api-catalog>; rel="api-catalog"`,
    `<${origin}/openapi.json>; rel="service-desc"; type="application/vnd.oai.openapi+json;version=3.1"`,
    `<${origin}/.well-known/api-docs.md>; rel="service-doc"; type="text/markdown"`,
    `<${origin}/auth.md>; rel="service-doc"; type="text/markdown"`,
    `<${origin}/agents.txt>; rel="service-meta"; type="text/plain"`,
    `<${origin}/llms.txt>; rel="service-meta"; type="text/plain"`,
    `<${origin}/.well-known/http-message-signatures-directory>; rel="service-meta"; type="application/jwk-set+json"`,
    `<${origin}/.well-known/ucp>; rel="service-meta"; type="application/json"`,
    `<${origin}/.well-known/acp.json>; rel="service-meta"; type="application/json"`,
  ].join(', ')
}

function withAgentReadyHeaders(response: Response, env: Env): Response {
  const headers = new Headers(response.headers)
  headers.set('Link', agentReadyLinks(agentReadyOrigin(env)))
  headers.set('Content-Signal', AGENT_READY_CONTENT_SIGNAL)
  headers.append('Vary', 'Accept')
  // Allow Google Sign-In popups and postMessage for auth flows (COOP)
  headers.set('Cross-Origin-Opener-Policy', 'same-origin-allow-popups')
  return new Response(response.body, {
    status: response.status,
    statusText: response.statusText,
    headers,
  })
}

function agentText(body: string, contentType: string, env: Env, init: ResponseInit = {}): Response {
  const headers = new Headers(init.headers)
  headers.set('Content-Type', contentType)
  const response = new Response(body, { ...init, headers })
  return withAgentReadyHeaders(response, env)
}

function agentJson(body: unknown, env: Env, contentType = 'application/json; charset=utf-8', init: ResponseInit = {}): Response {
  const headers = new Headers(init.headers)
  headers.set('Content-Type', contentType)
  const response = new Response(JSON.stringify(body, null, 2), { ...init, headers })
  return withAgentReadyHeaders(response, env)
}

function openApiDocument(origin: string) {
  return {
    openapi: '3.1.0',
    info: {
      title: 'OBOLLA Agent API',
      version: '1.0.0',
      description: 'Agent discovery and commerce metadata for OBOLLA.',
    },
    servers: [{ url: origin }],
    paths: {
      '/api/v1': {
        get: {
          operationId: 'getObollaAgentReview',
          summary: 'OBOLLA paid agent review discovery endpoint',
          'x-payment-info': {
            intent: 'charge',
            method: 'card',
            amount: '1.00',
            currency: 'USD',
            methods: [{ method: 'card', amount: '1.00', currency: 'USD' }],
            description: 'Discovery metadata for agent-native payment negotiation. Public OBOLLA browsing remains free.',
          },
          responses: {
            '200': { description: 'Signed discovery response' },
            '402': { description: 'Payment required metadata for x402-compatible clients' },
          },
        },
      },
      '/api/v1/smart-farm': {
        get: {
          operationId: 'getSmartFarmApi',
          summary: 'Smart farm API entrypoint proxied to the OBOLLA backend',
          responses: { '200': { description: 'Smart farm API response' } },
        },
      },
    },
  }
}

function oauthServer(origin: string) {
  return {
    issuer: origin,
    authorization_endpoint: `${origin}/api/oauth/authorize`,
    token_endpoint: `${origin}/api/oauth/token`,
    jwks_uri: `${origin}/.well-known/jwks.json`,
    response_types_supported: ['code'],
    grant_types_supported: ['authorization_code', 'client_credentials'],
    scopes_supported: ['public:read', 'agent:review'],
    token_endpoint_auth_methods_supported: ['client_secret_basic', 'none'],
    agent_auth: {
      skill: `${origin}/auth.md`,
      register_uri: `${origin}/agent-registration`,
      identity_types_supported: ['anonymous'],
      credential_types_supported: ['none'],
      claim_uri: `${origin}/auth.md#anonymous-claims`,
      revocation_uri: `${origin}/auth.md#anonymous-revocation`,
      methods: [
        {
          identity_type: 'anonymous',
          credential_types_supported: ['none'],
          claim_uri: `${origin}/auth.md#anonymous-claims`,
          revocation_uri: `${origin}/auth.md#anonymous-revocation`,
        },
      ],
      anonymous: {
        credential_types_supported: ['none'],
        claim_uri: `${origin}/auth.md#anonymous-claims`,
        revocation_uri: `${origin}/auth.md#anonymous-revocation`,
      },
    },
  }
}

function x402Response(request: Request, env: Env): Response {
  const origin = agentReadyOrigin(env)
  const signature = request.headers.get('payment-signature') || request.headers.get('PAYMENT-SIGNATURE') || request.headers.get('x-payment')
  if (signature) {
    return agentJson({ ok: true, settlement: 'not_verified_by_this_demo_route', site: AGENT_READY_SITE_NAME }, env)
  }
  const requirements = {
    x402Version: 1,
    accepts: [
      {
        scheme: 'exact',
        network: 'base-sepolia',
        maxAmountRequired: '1000000',
        resource: `${origin}/api/v1`,
        description: 'OBOLLA paid agent review discovery. Public website browsing remains free.',
        mimeType: 'application/json',
        payTo: '0x0000000000000000000000000000000000000000',
        maxTimeoutSeconds: 300,
        asset: '0x0000000000000000000000000000000000000000',
      },
    ],
  }
  const encoded = btoa(JSON.stringify(requirements))
  return agentJson({ error: 'payment_required', ...requirements }, env, 'application/json; charset=utf-8', {
    status: 402,
    headers: { 'PAYMENT-REQUIRED': encoded },
  })
}

function webMcpScript(origin: string): string {
  return `<script id="obolla-webmcp-agent-ready">\n(() => {\n  const tool = {\n    name: 'obolla_agent_ready_contact',\n    description: 'Request OBOLLA agent marketplace, smart farm, or agent-ready support.',\n    inputSchema: { type: 'object', properties: { topic: { type: 'string' }, email: { type: 'string' }, message: { type: 'string' } }, required: ['topic'] },\n    execute: async (input) => ({ ok: true, next: '${origin}/auth.md', received: input })\n  };\n  try {\n    if (navigator.modelContext?.provideContext) navigator.modelContext.provideContext({ tools: [tool] });\n    window.__OBOLLA_WEBMCP_TOOLS__ = [tool];\n  } catch (error) { window.__OBOLLA_WEBMCP_ERROR__ = String(error); }\n})();\n</script>`
}

async function finalizeAssetResponse(request: Request, response: Response, env: Env): Promise<Response> {
  const origin = agentReadyOrigin(env)
  const contentType = response.headers.get('content-type') ?? ''
  if (!contentType.includes('text/html')) {
    return withAgentReadyHeaders(response, env)
  }
  const headers = new Headers(response.headers)
  for (const [key, value] of Object.entries(HTML_SECURITY_HEADERS)) {
    headers.set(key, value)
  }
  headers.set('Link', agentReadyLinks(origin))
  headers.set('Content-Signal', AGENT_READY_CONTENT_SIGNAL)
  headers.append('Vary', 'Accept')
  let html = await response.text()
  if (!html.includes('obolla-webmcp-agent-ready')) {
    html = html.includes('</body>') ? html.replace('</body>', `${webMcpScript(origin)}</body>`) : `${html}${webMcpScript(origin)}`
  }
  return new Response(html, {
    status: response.status,
    statusText: response.statusText,
    headers,
  })
}

function botReadableHomeMarkdown(origin: string): string {
  return `# OBOLLA — AI Garden & Expert Skills Marketplace

OBOLLA is an AI expert skills marketplace, agent-ready service surface, and smart farm data workflow platform. Creators publish production agent skills; buyers and autonomous agents discover, run, and attribute revenue on real URLs.

## What OBOLLA offers
- **Marketplace** — Expert agent skills (SEO, visibility, smart farm, content pipelines)
- **Agent-Ready Pro** — Full SEO + AEO + AAIO scan, fix pack, MCP apply without local Bridge
- **Smart Farm** — Telemetry ingest, dataset packs, MQTT workflows
- **Closed-loop moat** — AIBotAuth signed scans + revenue attribution on skill runs

## Core pages
- [Marketplace](${origin}/marketplace) — Browse and run expert skills
- [Agent-Ready](${origin}/agent-ready) — Scan → fix pack → apply with your AI
- [Smart Farm](${origin}/smart-farm) — Farm data agents

## Agent discovery (AAIO)
- [API catalog](${origin}/.well-known/api-catalog)
- [OpenAPI](${origin}/openapi.json)
- [MCP server](${origin}/.well-known/mcp/server-card.json) — apply_agent_ready_fix tool
- [Agent card](${origin}/.well-known/agent-card.json)
- [Auth instructions](${origin}/auth.md)
- [llms.txt](${origin}/llms.txt) · [robots.txt](${origin}/robots.txt)

Content-Signal: ai-train=no, search=yes, ai-input=yes. Public browsing is free; paid workflows require account approval.
`
}

function botReadableHomeHtml(origin: string): string {
  const md = botReadableHomeMarkdown(origin)
  const plain = md.replace(/^#+\s*/gm, '').replace(/\[([^\]]+)\]\([^)]+\)/g, '$1')
  return `<!DOCTYPE html><html lang="en"><head><meta charset="utf-8"><title>OBOLLA — AI Garden & Expert Skills Marketplace</title><meta name="description" content="OBOLLA is an AI expert skills marketplace with Agent-Ready SEO+AEO+AAIO scans, MCP fix packs, smart farm workflows, and revenue attribution."><link rel="canonical" href="${origin}/"></head><body><main id="obolla-bot-readable"><h1>OBOLLA — AI Garden & Expert Skills Marketplace</h1><p>OBOLLA is an AI expert skills marketplace, agent-ready service surface, and smart farm data workflow platform.</p><h2>Marketplace &amp; Agent-Ready</h2><p>Creators publish production agent skills. Buyers run full SEO, AEO, and AAIO improvements with real deployable files. Autonomous agents apply fixes via MCP at ${origin}/mcp without a local Bridge.</p><h2>Smart Farm</h2><p>Telemetry ingest, dataset packs, and MQTT workflows for agriculture and IoT operators.</p><h2>Discovery</h2><ul><li><a href="${origin}/marketplace">Marketplace</a></li><li><a href="${origin}/agent-ready">Agent-Ready Pro</a></li><li><a href="${origin}/llms.txt">llms.txt</a></li><li><a href="${origin}/.well-known/mcp/server-card.json">MCP server card</a></li></ul><pre>${plain.slice(0, 4000)}</pre></main></body></html>`
}

function handleAgentReadinessRequest(request: Request, env: Env): Response | null {
  const url = new URL(request.url)
  const origin = agentReadyOrigin(env)
  const path = url.pathname.replace(/\/$/, '') || '/'
  const acceptsMarkdown = request.headers.get('accept')?.includes('text/markdown')
  const ua = request.headers.get('user-agent') || ''

  if (path === '/' && acceptsMarkdown) {
    return agentText(botReadableHomeMarkdown(origin), 'text/markdown; charset=utf-8', env, {
      headers: { 'x-markdown-tokens': 'approx-400' },
    })
  }

  if (path === '/' && BOT_UA_PATTERN.test(ua)) {
    return agentText(botReadableHomeHtml(origin), 'text/html; charset=utf-8', env)
  }

  if (path === '/api/v1' && request.method === 'GET') return x402Response(request, env)

  if (path === '/robots.txt') {
    return agentText(`User-agent: *\nAllow: /\n\nUser-agent: GPTBot\nAllow: /\n\nUser-agent: ChatGPT-User\nAllow: /\n\nUser-agent: ClaudeBot\nAllow: /\n\nUser-agent: Claude-SearchBot\nAllow: /\n\nUser-agent: PerplexityBot\nAllow: /\n\nContent-Signal: ${AGENT_READY_CONTENT_SIGNAL}\nSitemap: ${origin}/sitemap.xml\n`, 'text/plain; charset=utf-8', env)
  }

  if (path === '/sitemap.xml') {
    return agentText(`<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n  <url><loc>${origin}/</loc><changefreq>weekly</changefreq><priority>1.0</priority></url>\n  <url><loc>${origin}/marketplace</loc><changefreq>weekly</changefreq><priority>0.8</priority></url>\n  <url><loc>${origin}/agent-ready-pro</loc><changefreq>weekly</changefreq><priority>0.8</priority></url>\n</urlset>\n`, 'application/xml; charset=utf-8', env)
  }

  if (path === '/llms.txt') return agentText(`# OBOLLA\n\nOBOLLA is an AI expert skills marketplace, agent-ready service surface, and smart farm data workflow platform.\n\nCanonical origin: ${origin}\nAPI catalog: ${origin}/.well-known/api-catalog\nAgent card: ${origin}/.well-known/agent-card.json\nAuth instructions: ${origin}/auth.md\n`, 'text/plain; charset=utf-8', env)
  if (path === '/ai.txt') return agentText(`# OBOLLA AI Access\n\nPublic pages may be fetched for search, summarization, and agent discovery. Do not treat public website content as final professional advice or production payment settlement.\n`, 'text/plain; charset=utf-8', env)
  if (path === '/agents.txt') return agentText(`# OBOLLA Agent Discovery\n\nOrigin: ${origin}\nAPI catalog: ${origin}/.well-known/api-catalog\nOpenAPI: ${origin}/openapi.json\nMCP server card: ${origin}/.well-known/mcp/server-card.json\nA2A agent card: ${origin}/.well-known/agent-card.json\nSkills index: ${origin}/.well-known/agent-skills/index.json\nAuth.md: ${origin}/auth.md\n`, 'text/plain; charset=utf-8', env)
  if (path === '/auth.md') return agentText(`# Auth.md\n\n## OBOLLA Agent Registration\n\nPublic website pages are available without authentication. Protected marketplace, creator, smart-farm, and payable agent workflows require user or partner approval.\n\nDiscovery metadata:\n\n- ${origin}/.well-known/oauth-protected-resource\n- ${origin}/.well-known/oauth-authorization-server\n- ${origin}/.well-known/openid-configuration\n\n## agent_auth\n\nagent_auth = {\n  "skill": "${origin}/auth.md",\n  "register_uri": "${origin}/agent-registration",\n  "identity_types_supported": ["anonymous"],\n  "anonymous": {\n    "credential_types_supported": ["none"],\n    "claim_uri": "${origin}/auth.md#anonymous-claims"\n  }\n}\n\n## Anonymous Claims\n\nClaim URI: ${origin}/auth.md#anonymous-claims\nRevocation URI: ${origin}/auth.md#anonymous-revocation\n\nAgents may identify themselves as anonymous clients for public discovery. Production access to private data, paid workflows, or account-specific operations requires a separate human-approved registration or provider credential.\n`, 'text/markdown; charset=utf-8', env)
  if (path === '/.well-known/api-docs.md') return agentText(`# OBOLLA API Documentation\n\nPublic discovery endpoints are available for AI agents. Payable examples are discovery metadata; production settlement requires configured provider credentials.\n\n- OpenAPI: ${origin}/openapi.json\n- Auth.md: ${origin}/auth.md\n- Agent card: ${origin}/.well-known/agent-card.json\n`, 'text/markdown; charset=utf-8', env)

  if (path === '/openapi.json' || path === '/.well-known/openapi.json') return agentJson(openApiDocument(origin), env, 'application/vnd.oai.openapi+json;version=3.1; charset=utf-8')
  if (path === '/.well-known/api-catalog') return agentJson({ linkset: [{ anchor: `${origin}/api`, 'service-desc': [{ href: `${origin}/openapi.json`, type: 'application/vnd.oai.openapi+json;version=3.1' }], 'service-doc': [{ href: `${origin}/.well-known/api-docs.md`, type: 'text/markdown' }, { href: `${origin}/auth.md`, type: 'text/markdown' }], 'service-meta': [{ href: `${origin}/agents.txt`, type: 'text/plain' }, { href: `${origin}/.well-known/http-message-signatures-directory`, type: 'application/jwk-set+json' }, { href: `${origin}/.well-known/ucp`, type: 'application/json' }, { href: `${origin}/.well-known/acp.json`, type: 'application/json' }] }] }, env, 'application/linkset+json; charset=utf-8')
  if (path === '/.well-known/oauth-protected-resource') return agentJson({ resource: origin, authorization_servers: [origin], scopes_supported: ['public:read', 'agent:review'], bearer_methods_supported: ['header'], resource_documentation: `${origin}/auth.md` }, env)
  if (path === '/.well-known/oauth-authorization-server') return agentJson(oauthServer(origin), env)
  if (path === '/.well-known/openid-configuration') return agentJson({ ...oauthServer(origin), userinfo_endpoint: `${origin}/api/oauth/userinfo`, subject_types_supported: ['public'], id_token_signing_alg_values_supported: ['EdDSA', 'RS256'] }, env)
  if (path === '/.well-known/jwks.json') return agentJson(AGENT_READY_WEB_BOT_JWKS, env, 'application/jwk-set+json; charset=utf-8')
  if (path === '/.well-known/http-message-signatures-directory') return agentJson(AGENT_READY_WEB_BOT_JWKS, env, 'application/jwk-set+json; charset=utf-8')
  if (path === '/.well-known/mcp/server-card.json' || path === '/.well-known/mcp.json') return agentJson({ schema_version: '2026-01-01', name: 'OBOLLA MCP', description: 'OBOLLA public website and agent discovery metadata.', url: `${origin}/mcp`, protocol: 'mcp', transport: { type: 'http', url: `${origin}/mcp` }, auth: { type: 'none', instructions: `${origin}/auth.md` }, tools: [{ name: 'site_discovery', description: 'Read public OBOLLA discovery and contact information.' }, { name: 'apply_agent_ready_fix', description: 'Securely apply the generated agent-ready fix pack (full SEO + AEO + AAIO) without needing local Bridge. Pass scoped tokens for PR/deploy. Revenue is auto-logged to OBOLLA moat on success.' }] }, env)
  if (path === '/.well-known/agent-card.json') return agentJson({ protocolVersion: '0.3.0', version: '1.0.0', supportedInterfaces: [{ transport: 'JSONRPC', url: origin + '/' }], defaultInputModes: ['text/plain', 'application/json'], defaultOutputModes: ['text/plain', 'application/json'], name: 'OBOLLA Agent', description: 'OBOLLA public information and commerce discovery agent.', url: origin, preferredTransport: 'JSONRPC', skills: [{ id: 'site-discovery', name: 'Site Discovery', description: 'Provide public website discovery metadata.', tags: ['discovery'] }, { id: 'paid-review-discovery', name: 'Paid Review Discovery', description: 'Advertise payable agent review capability where production payment is configured.', tags: ['commerce', 'x402', 'mpp', 'ap2'] }], capabilities: { streaming: false, pushNotifications: false, extensions: AGENT_READY_PAYMENT_EXTENSIONS, payment_protocols: ['x402', 'mpp', 'ap2'], ap2: { supported: true, version: '1.0', mandate_required: false, discovery_url: `${origin}/.well-known/agent-card.json` } }, extensions: AGENT_READY_PAYMENT_EXTENSIONS, payment_protocols: ['x402', 'mpp', 'ap2'], commerce: { ap2: { supported: true, version: '1.0' } }, authentication: { schemes: ['none'], credentials: `${origin}/auth.md` } }, env)
  if (path === '/.well-known/agent-skills/index.json') return agentJson({ skills: [{ id: 'site-discovery', name: 'OBOLLA Site Discovery', description: 'Fetch public website, API, auth, and commerce discovery metadata.', url: `${origin}/.well-known/agent-skills/site-discovery/SKILL.md` }] }, env)
  if (path === '/.well-known/agent-skills/site-discovery/SKILL.md') return agentText(`# OBOLLA Site Discovery Skill\n\nUse this skill to inspect public discovery metadata for OBOLLA.\n\n- ${origin}/agents.txt\n- ${origin}/.well-known/api-catalog\n- ${origin}/openapi.json\n- ${origin}/auth.md\n`, 'text/markdown; charset=utf-8', env)
  if (path === '/.well-known/ucp') return agentJson({ protocol_version: '2026-04-08', services: { discovery: { name: 'OBOLLA public discovery', type: 'information' } }, capabilities: { content_payments: false, agent_checkout: true }, endpoints: { profile: `${origin}/.well-known/ucp`, api: `${origin}/api/v1` }, ucp: { version: '2026-04-08', services: { discovery: { name: 'OBOLLA public discovery' } }, capabilities: { agent_checkout: true } } }, env)
  if (path === '/.well-known/acp.json') return agentJson({ protocol: { name: 'acp', version: '1.0.0' }, api_base_url: `${origin}/api/commerce`, transports: ['rest', 'a2a'], capabilities: { services: ['catalog_lookup', 'checkout_session', 'agent_review_discovery'] }, documentation_url: `${origin}/.well-known/api-docs.md` }, env)

  return null
}
const CORS_HEADERS = {
  'Access-Control-Allow-Methods': 'GET, POST, PUT, PATCH, DELETE, OPTIONS',
  'Access-Control-Allow-Headers': 'Authorization, Content-Type',
  'Access-Control-Max-Age': '86400',
}

const HTML_SECURITY_HEADERS = {
  'Permissions-Policy': 'camera=(), geolocation=(), microphone=*',
  'X-Frame-Options': 'DENY',
  'X-Content-Type-Options': 'nosniff',
  'Referrer-Policy': 'strict-origin-when-cross-origin',
}

function withHtmlSecurityHeaders(response: Response): Response {
  const contentType = response.headers.get('content-type') ?? ''
  if (!contentType.includes('text/html')) {
    return response
  }
  const headers = new Headers(response.headers)
  for (const [key, value] of Object.entries(HTML_SECURITY_HEADERS)) {
    headers.set(key, value)
  }
  return new Response(response.body, {
    status: response.status,
    statusText: response.statusText,
    headers,
  })
}

function withCors(response: Response, origin: string | null): Response {
  const headers = new Headers(response.headers)
  if (origin) {
    headers.set('Access-Control-Allow-Origin', origin)
    headers.set('Access-Control-Allow-Credentials', 'true')
  }
  headers.set('Vary', 'Origin')
  return new Response(response.body, {
    status: response.status,
    statusText: response.statusText,
    headers,
  })
}

async function proxyApi(request: Request, env: Env): Promise<Response> {
  const url = new URL(request.url)
  const backendBase = (env.BACKEND_URL || 'http://127.0.0.1:8000').replace(/\/$/, '')
  const targetUrl = `${backendBase}${url.pathname}${url.search}`

  const headers = new Headers(request.headers)
  headers.delete('host')

  const init: RequestInit = {
    method: request.method,
    headers,
    redirect: 'manual',
  }

  if (request.method !== 'GET' && request.method !== 'HEAD') {
    init.body = request.body
  }

  let upstream: Response
  try {
    upstream = await fetch(targetUrl, init)
  } catch (error) {
    const message = error instanceof Error ? error.message : 'API proxy failed'
    const origin = request.headers.get('Origin')
    return withCors(
      Response.json(
        {
          detail:
            'Backend API is unreachable. Start the local server and Cloudflare tunnel (backend/sync-tunnel.ps1).',
          error: message,
        },
        { status: 503 },
      ),
      origin,
    )
  }

  const origin = request.headers.get('Origin')
  const contentType = upstream.headers.get('content-type') ?? ''
  if (
    upstream.status >= 500 &&
    contentType.includes('text/html') &&
    !contentType.includes('json')
  ) {
    return withCors(
      Response.json(
        {
          detail:
            'Backend tunnel is down or stale. Re-run backend/sync-tunnel.ps1 to refresh BACKEND_URL.',
          upstream_status: upstream.status,
        },
        { status: 503 },
      ),
      origin,
    )
  }
  return withCors(upstream, origin)
}

export default {
  async fetch(request: Request, env: Env): Promise<Response> {
    const url = new URL(request.url)

    const agentReadinessResponse = handleAgentReadinessRequest(request, env)
    if (agentReadinessResponse) {
      return agentReadinessResponse
    }

    if (url.pathname === '/internal/notifications/publish' && request.method === 'POST') {
      return handleInternalPublish(request, env)
    }

    if (url.pathname === '/internal/bridge/dispatch' && request.method === 'POST') {
      return handleInternalBridgeDispatch(request, env)
    }

    const installResponse = handleBridgeInstallRequest(request)
    if (installResponse) {
      return installResponse
    }

    const pairingResponse = await handleBridgePairingEdge(request, env)
    if (pairingResponse) {
      return pairingResponse
    }

    const bridgeResponse = await handleBridgeRequest(request, env)
    if (bridgeResponse) {
      return bridgeResponse
    }

    const notificationResponse = await handleNotificationRequest(request, env)
    if (notificationResponse) {
      return notificationResponse
    }

    if (request.method === 'OPTIONS' && url.pathname.startsWith('/api/')) {
      const origin = request.headers.get('Origin')
      return new Response(null, {
        status: 204,
        headers: {
          ...CORS_HEADERS,
          ...(origin
            ? {
                'Access-Control-Allow-Origin': origin,
                'Access-Control-Allow-Credentials': 'true',
              }
            : {}),
        },
      })
    }

    if (url.pathname === '/api/v1/speech/transcribe' && request.method === 'POST') {
      const origin = request.headers.get('Origin')
      try {
        return withCors(await handleSpeechTranscribe(request, env), origin)
      } catch (error) {
        const message = error instanceof Error ? error.message : 'Speech transcription failed'
        return withCors(Response.json({ detail: message }, { status: 502 }), origin)
      }
    }

    if (url.pathname === '/mcp' && request.method === 'POST') {
      const backendBase = (env.BACKEND_URL || 'http://127.0.0.1:8000').replace(/\/$/, '')
      const targetUrl = `${backendBase}/api/v1/mcp${url.search}`
      const headers = new Headers(request.headers)
      headers.delete('host')
      try {
        const upstream = await fetch(targetUrl, {
          method: 'POST',
          headers,
          body: request.body,
          redirect: 'manual',
        })
        const origin = request.headers.get('Origin')
        return withCors(upstream, origin)
      } catch (error) {
        const message = error instanceof Error ? error.message : 'MCP proxy failed'
        return Response.json({ detail: message }, { status: 502 })
      }
    }

    if (url.pathname.startsWith('/api/')) {
      try {
        return await proxyApi(request, env)
      } catch (error) {
        const message = error instanceof Error ? error.message : 'API proxy failed'
        return Response.json({ detail: message }, { status: 502 })
      }
    }

    if (url.pathname === '/health') {
      const backendBase = (env.BACKEND_URL || 'http://127.0.0.1:8000').replace(/\/$/, '')
      let backendReachable = false
      let backendStatus: number | null = null
      let backendHealth: any = null
      try {
        // Prefer richer backend health
        const probe = await fetch(`${backendBase}/api/v1/health`, { method: 'GET' })
        backendStatus = probe.status
        backendReachable = probe.status >= 200 && probe.status < 500
        if (probe.ok) {
          try { backendHealth = await probe.json() } catch {}
        }
        if (!backendReachable) {
          // fallback probe
          const fb = await fetch(`${backendBase}/docs`, { method: 'GET' })
          backendStatus = fb.status
          backendReachable = fb.status >= 200 && fb.status < 500
        }
      } catch {
        backendReachable = false
      }
      const status = backendReachable ? 'ok' : 'degraded'
      return Response.json({
        status,
        app: env.APP_NAME,
        edge: 'cloudflare-workers',
        public_url: env.PUBLIC_URL,
        realtime_notifications: true,
        bridge_hub: true,
        bridge_consent_queue: true,
        backend_reachable: backendReachable,
        backend_status: backendStatus,
        backend_checks: backendHealth,
      })
    }

    const assetResponse = await env.ASSETS.fetch(request)
    return await finalizeAssetResponse(request, assetResponse, env)
  },

  async queue(batch: MessageBatch<NotifyQueueMessage>, env: Env): Promise<void> {
    const messages = batch.messages.map((message) => message.body)
    await processNotificationBatch(messages, env)
    batch.ackAll()
  },
}





