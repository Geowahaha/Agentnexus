#!/usr/bin/env node
import { mkdir, readFile, writeFile } from "node:fs/promises";
import { existsSync } from "node:fs";
import path from "node:path";
import { generateKeyPairSync } from "node:crypto";

const args = parseArgs(process.argv.slice(2));
const root = path.resolve(args.root || ".");
const publicDir = path.resolve(root, args.public || "public");
const origin = normalizeOrigin(args.origin || "");
const siteName = args["site-name"] || hostnameName(origin);
const force = Boolean(args.force);

if (!origin) {
  fail("Missing --origin https://example.com");
}

const host = new URL(origin).hostname;
const slug = host.replace(/^www\./, "").replace(/[^a-z0-9]+/gi, "-").replace(/^-|-$/g, "").toLowerCase();

const { publicKey } = generateKeyPairSync("ed25519");
const jwk = publicKey.export({ format: "jwk" });
const webBotJwks = {
  keys: [
    {
      kty: "OKP",
      crv: "Ed25519",
      kid: `${slug}-web-bot-auth-2026`,
      use: "sig",
      alg: "EdDSA",
      x: jwk.x
    }
  ]
};
const paymentExtensions = [
  { uri: "https://x402.org", name: "x402", protocol: "x402", version: "1", description: "x402 payment discovery route", required: false },
  { uri: "https://paymentauth.org", name: "MPP", protocol: "mpp", version: "1", description: "MPP payment discovery metadata", required: false },
  { uri: "https://agentpayments.org/ap2", name: "AP2", protocol: "ap2", version: "1.0", description: "AP2-compatible commerce discovery", required: false, params: { payment_protocol: "ap2" } },
  { uri: "https://payments.google.com/ap2", name: "AP2", protocol: "ap2", version: "1.0", description: "Agent Payments Protocol discovery", required: false, params: { payment_protocol: "ap2" } },
  { uri: "https://github.com/google-agentic-commerce/ap2", name: "AP2", protocol: "ap2", version: "1.0", description: "Agent Payments Protocol extension", required: false, params: { payment_protocol: "ap2" } },
  { uri: "https://a2a-protocol.org/extensions/ap2", name: "AP2", protocol: "ap2", version: "1.0", description: "A2A AP2 extension declaration", required: false, params: { payment_protocol: "ap2" } }
];

const files = new Map();
add("robots.txt", `User-agent: *\nAllow: /\n\nUser-agent: GPTBot\nAllow: /\n\nUser-agent: ChatGPT-User\nAllow: /\n\nUser-agent: ClaudeBot\nAllow: /\n\nUser-agent: PerplexityBot\nAllow: /\n\nContent-Signal: ai-train=yes, ai-input=yes, search=yes\nSitemap: ${origin}/sitemap.xml\n`);
add("sitemap.xml", `<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n  <url>\n    <loc>${origin}/</loc>\n    <changefreq>weekly</changefreq>\n    <priority>1.0</priority>\n  </url>\n</urlset>\n`);
add("llms.txt", `# ${siteName}\n\n${siteName} provides public website information for human visitors and AI agents.\n\nCanonical origin: ${origin}\nAPI catalog: ${origin}/.well-known/api-catalog\nAgent card: ${origin}/.well-known/agent-card.json\nAuth instructions: ${origin}/auth.md\n`);
add("ai.txt", `# ${siteName} AI Access\n\nPublic pages may be fetched for search, summarization, and agent discovery. Do not treat website content as final legal, tax, medical, financial, or professional advice unless the site explicitly says so.\n`);
add("agents.txt", `# ${siteName} Agent Discovery\n\nOrigin: ${origin}\nAPI catalog: ${origin}/.well-known/api-catalog\nOpenAPI: ${origin}/openapi.json\nMCP server card: ${origin}/.well-known/mcp/server-card.json\nA2A agent card: ${origin}/.well-known/agent-card.json\nSkills index: ${origin}/.well-known/agent-skills/index.json\nAuth.md: ${origin}/auth.md\n`);
add("auth.md", `# Auth.md\n\n## ${siteName} Agent Registration\n\nPublic website pages are available without authentication. Protected or payable agent workflows, if enabled, use the discovery metadata published at:\n\n- ${origin}/.well-known/oauth-protected-resource\n- ${origin}/.well-known/oauth-authorization-server\n- ${origin}/.well-known/openid-configuration\n\n## Anonymous Claims\n\nAgents may identify themselves as anonymous clients for public discovery. Production access to private data, paid workflows, or account-specific operations requires a separate human-approved registration or provider credential.\n\n## Contact\n\nUse the public website contact channel for case-specific access requests.\n`);

add(".well-known/api-catalog", json({
  linkset: [
    {
      anchor: `${origin}/api`,
      "service-desc": [
        { href: `${origin}/openapi.json`, type: "application/vnd.oai.openapi+json;version=3.1" },
        { href: `${origin}/.well-known/openapi.json`, type: "application/vnd.oai.openapi+json;version=3.1" }
      ],
      "service-doc": [
        { href: `${origin}/.well-known/api-docs.md`, type: "text/markdown" },
        { href: `${origin}/auth.md`, type: "text/markdown" }
      ],
      "service-meta": [
        { href: `${origin}/agents.txt`, type: "text/plain" },
        { href: `${origin}/llms.txt`, type: "text/plain" },
        { href: `${origin}/.well-known/http-message-signatures-directory`, type: "application/jwk-set+json" },
        { href: `${origin}/.well-known/ucp`, type: "application/json" },
        { href: `${origin}/.well-known/acp.json`, type: "application/json" }
      ]
    }
  ]
}));
add(".well-known/api-docs.md", `# ${siteName} API Documentation\n\nPublic discovery endpoints are available for AI agents. Payable discovery examples are published for agent-native protocol compatibility; production settlement requires configured provider credentials.\n\n## Endpoints\n\n- GET ${origin}/openapi.json\n- GET ${origin}/api/v1\n- GET ${origin}/.well-known/agent-card.json\n`);

const openapi = {
  openapi: "3.1.0",
  info: { title: `${siteName} Agent API`, version: "1.0.0" },
  servers: [{ url: origin }],
  paths: {
    "/api/v1": {
      get: {
        operationId: "getAgentReview",
        summary: "Agent-readable paid discovery example",
        "x-payment-info": {
          intent: "charge",
          method: "card",
          amount: "1.00",
          currency: "USD",
          methods: [{ method: "card", amount: "1.00", currency: "USD" }],
          description: "Discovery metadata for agent-native payment negotiation. Public website browsing remains free."
        },
        responses: {
          "200": { description: "Signed discovery response" },
          "402": { description: "Payment required metadata for x402-compatible clients" }
        }
      }
    }
  }
};
add("openapi.json", json(openapi));
add(".well-known/openapi.json", json(openapi));

const protectedResource = {
  resource: origin,
  authorization_servers: [origin],
  scopes_supported: ["public:read", "agent:review"],
  bearer_methods_supported: ["header"],
  resource_documentation: `${origin}/auth.md`
};
add(".well-known/oauth-protected-resource", json(protectedResource));

const authServer = {
  issuer: origin,
  authorization_endpoint: `${origin}/api/oauth/authorize`,
  token_endpoint: `${origin}/api/oauth/token`,
  jwks_uri: `${origin}/.well-known/jwks.json`,
  response_types_supported: ["code"],
  grant_types_supported: ["authorization_code", "client_credentials"],
  scopes_supported: ["public:read", "agent:review"],
  token_endpoint_auth_methods_supported: ["client_secret_basic", "none"],
  agent_auth: {
    skill: `${origin}/auth.md`,
    register_uri: `${origin}/agent-registration`,
    identity_types_supported: ["anonymous"],
    credential_types_supported: ["none"],
    claim_uri: `${origin}/auth.md#anonymous-claims`,
    revocation_uri: `${origin}/auth.md#anonymous-revocation`,
    methods: [
      {
        identity_type: "anonymous",
        credential_types_supported: ["none"],
        claim_uri: `${origin}/auth.md#anonymous-claims`,
        revocation_uri: `${origin}/auth.md#anonymous-revocation`
      }
    ],
    anonymous: {
      credential_types_supported: ["none"],
      claim_uri: `${origin}/auth.md#anonymous-claims`,
      revocation_uri: `${origin}/auth.md#anonymous-revocation`
    }
  }
};
add(".well-known/oauth-authorization-server", json(authServer));
add(".well-known/openid-configuration", json({
  ...authServer,
  userinfo_endpoint: `${origin}/api/oauth/userinfo`,
  subject_types_supported: ["public"],
  id_token_signing_alg_values_supported: ["EdDSA", "RS256"]
}));
add(".well-known/jwks.json", json(webBotJwks));
add(".well-known/http-message-signatures-directory", json(webBotJwks));

add(".well-known/mcp/server-card.json", json({
  schema_version: "2026-01-01",
  name: `${siteName} MCP`,
  description: `${siteName} public website and agent discovery metadata.`,
  url: `${origin}/mcp`,
  protocol: "mcp",
  transport: { type: "http", url: `${origin}/mcp` },
  auth: { type: "none", instructions: `${origin}/auth.md` },
  tools: [
    { name: "site_discovery", description: "Read public discovery and contact information." }
  ]
}));

add(".well-known/agent-card.json", json({
  protocolVersion: "0.3.0",
  version: "1.0.0",
  supportedInterfaces: [{ transport: "JSONRPC", url: `${origin}/` }],
  defaultInputModes: ["text/plain", "application/json"],
  defaultOutputModes: ["text/plain", "application/json"],
  name: `${siteName} Agent`,
  description: `${siteName} public information and commerce discovery agent.`,
  url: origin,
  preferredTransport: "JSONRPC",
  skills: [
    { id: "site-discovery", name: "Site Discovery", description: "Provide public website discovery metadata.", tags: ["discovery"] },
    { id: "paid-review-discovery", name: "Paid Review Discovery", description: "Advertise payable agent review capability where production payment is configured.", tags: ["commerce", "x402", "mpp", "ap2"] }
  ],
  capabilities: {
    streaming: false,
    pushNotifications: false,
    extensions: paymentExtensions,
    payment_protocols: ["x402", "mpp", "ap2"],
    ap2: { supported: true, version: "1.0", mandate_required: false, discovery_url: `${origin}/.well-known/agent-card.json` }
  },
  extensions: paymentExtensions,
  payment_protocols: ["x402", "mpp", "ap2"],
  commerce: { ap2: { supported: true, version: "1.0" } },
  authentication: { schemes: ["none"], credentials: `${origin}/auth.md` }
}));

add(".well-known/agent-skills/index.json", json({
  skills: [
    {
      id: "site-discovery",
      name: `${siteName} Site Discovery`,
      description: "Fetch public website, API, auth, and commerce discovery metadata.",
      url: `${origin}/.well-known/agent-skills/site-discovery/SKILL.md`
    }
  ]
}));
add(".well-known/agent-skills/site-discovery/SKILL.md", `# ${siteName} Site Discovery Skill\n\nUse this skill to inspect public discovery metadata for ${siteName}.\n\nImportant resources:\n\n- ${origin}/agents.txt\n- ${origin}/.well-known/api-catalog\n- ${origin}/openapi.json\n- ${origin}/auth.md\n`);

add(".well-known/ucp", json({
  protocol_version: "2026-04-08",
  services: { discovery: { name: `${siteName} public discovery`, type: "information" } },
  capabilities: { content_payments: false, agent_checkout: true },
  endpoints: { profile: `${origin}/.well-known/ucp`, api: `${origin}/api/v1` },
  ucp: {
    version: "2026-04-08",
    services: { discovery: { name: `${siteName} public discovery` } },
    capabilities: { agent_checkout: true }
  }
}));
add(".well-known/acp.json", json({
  protocol: { name: "acp", version: "1.0.0" },
  api_base_url: `${origin}/api/commerce`,
  transports: ["rest", "a2a"],
  capabilities: { services: ["catalog_lookup", "checkout_session", "agent_review_discovery"] },
  documentation_url: `${origin}/.well-known/api-docs.md`
}));

add("_headers", [
  "/*",
  `  Link: <${origin}/.well-known/api-catalog>; rel="api-catalog", <${origin}/openapi.json>; rel="service-desc"; type="application/vnd.oai.openapi+json;version=3.1", <${origin}/.well-known/api-docs.md>; rel="service-doc"; type="text/markdown", <${origin}/auth.md>; rel="service-doc"; type="text/markdown", <${origin}/.well-known/http-message-signatures-directory>; rel="service-meta"; type="application/jwk-set+json", <${origin}/.well-known/ucp>; rel="service-meta"; type="application/json", <${origin}/.well-known/acp.json>; rel="service-meta"; type="application/json"`,
  "  Content-Signal: ai-train=yes, ai-input=yes, search=yes",
  "",
  "/robots.txt",
  "  Content-Type: text/plain; charset=utf-8",
  "/sitemap.xml",
  "  Content-Type: application/xml; charset=utf-8",
  "/*.txt",
  "  Content-Type: text/plain; charset=utf-8",
  "/*.md",
  "  Content-Type: text/markdown; charset=utf-8",
  "/.well-known/api-catalog",
  "  Content-Type: application/linkset+json; charset=utf-8",
  "/openapi.json",
  "  Content-Type: application/vnd.oai.openapi+json;version=3.1; charset=utf-8",
  "/.well-known/openapi.json",
  "  Content-Type: application/vnd.oai.openapi+json;version=3.1; charset=utf-8",
  "/.well-known/http-message-signatures-directory",
  "  Content-Type: application/jwk-set+json; charset=utf-8",
  "/.well-known/*",
  "  Content-Type: application/json; charset=utf-8",
  ""
].join("\n"));

files.set(path.join(root, "functions", "_middleware.js"), middlewareSource(origin, siteName));
files.set(path.join(root, "functions", "api", "v1.js"), x402Source(origin, siteName));

let created = 0;
let skipped = 0;
for (const [file, content] of files) {
  const target = path.isAbsolute(file) ? file : path.join(publicDir, file);
  if (existsSync(target) && !force) {
    skipped += 1;
    continue;
  }
  await mkdir(path.dirname(target), { recursive: true });
  await writeFile(target, content, "utf8");
  created += 1;
}

console.log(JSON.stringify({ root, publicDir, origin, siteName, created, skipped, force }, null, 2));

function parseArgs(argv) {
  const out = {};
  for (let i = 0; i < argv.length; i += 1) {
    const arg = argv[i];
    if (!arg.startsWith("--")) continue;
    const key = arg.slice(2);
    if (key === "force") {
      out.force = true;
    } else {
      out[key] = argv[i + 1];
      i += 1;
    }
  }
  return out;
}

function normalizeOrigin(value) {
  if (!value) return "";
  const url = new URL(value);
  return `${url.protocol}//${url.hostname}${url.port ? `:${url.port}` : ""}`;
}

function hostnameName(value) {
  try {
    return new URL(value).hostname.replace(/^www\./, "");
  } catch {
    return "Example";
  }
}

function add(relativePath, content) {
  files.set(relativePath, content.endsWith("\n") ? content : `${content}\n`);
}

function json(value) {
  return `${JSON.stringify(value, null, 2)}\n`;
}

function fail(message) {
  console.error(message);
  process.exit(1);
}

function middlewareSource(siteOrigin, name) {
  return [
    `const ORIGIN = ${JSON.stringify(siteOrigin)};`,
    `const SITE_NAME = ${JSON.stringify(name)};`,
    "",
    "export async function onRequest(context) {",
    "  const request = context.request;",
    "  const url = new URL(request.url);",
    "  const response = await context.next();",
    "  const headers = new Headers(response.headers);",
    "",
    "  headers.set(\"Content-Signal\", \"ai-train=yes, ai-input=yes, search=yes\");",
    "  headers.append(\"Vary\", \"Accept\");",
    "",
    "  headers.append(\"Link\", [",
    "    \"<\" + ORIGIN + \"/.well-known/api-catalog>; rel=\\\"api-catalog\\\"\",",
    "    \"<\" + ORIGIN + \"/openapi.json>; rel=\\\"service-desc\\\"; type=\\\"application/vnd.oai.openapi+json;version=3.1\\\"\",",
    "    \"<\" + ORIGIN + \"/.well-known/api-docs.md>; rel=\\\"service-doc\\\"; type=\\\"text/markdown\\\"\",",
    "    \"<\" + ORIGIN + \"/auth.md>; rel=\\\"service-doc\\\"; type=\\\"text/markdown\\\"\",",
    "    \"<\" + ORIGIN + \"/.well-known/http-message-signatures-directory>; rel=\\\"service-meta\\\"; type=\\\"application/jwk-set+json\\\"\",",
    "    \"<\" + ORIGIN + \"/.well-known/ucp>; rel=\\\"service-meta\\\"; type=\\\"application/json\\\"\",",
    "    \"<\" + ORIGIN + \"/.well-known/acp.json>; rel=\\\"service-meta\\\"; type=\\\"application/json\\\"\"",
    "  ].join(\", \"));",
    "",
    "  if (request.headers.get(\"accept\")?.includes(\"text/markdown\") && url.pathname === \"/\") {",
    "    const markdown = \"# \" + SITE_NAME + \"\\n\\n\" +",
    "      \"Canonical origin: \" + ORIGIN + \"\\n\\n\" +",
    "      \"- API catalog: \" + ORIGIN + \"/.well-known/api-catalog\\n\" +",
    "      \"- OpenAPI: \" + ORIGIN + \"/openapi.json\\n\" +",
    "      \"- Auth.md: \" + ORIGIN + \"/auth.md\\n\" +",
    "      \"- Agent card: \" + ORIGIN + \"/.well-known/agent-card.json\\n\";",
    "    return new Response(markdown, {",
    "      status: 200,",
    "      headers: {",
    "        \"content-type\": \"text/markdown; charset=utf-8\",",
    "        \"x-markdown-tokens\": \"approx-45\",",
    "        \"content-signal\": \"ai-train=yes, ai-input=yes, search=yes\",",
    "        \"link\": headers.get(\"link\") || \"\"",
    "      }",
    "    });",
    "  }",
    "",
    "  const contentType = headers.get(\"content-type\") || \"\";",
    "  if (contentType.includes(\"text/html\")) {",
    "    let html = await response.text();",
    "    if (!html.includes(\"agent-ready-webmcp\")) {",
    "      const script = \"<script id=\\\"agent-ready-webmcp\\\">window.__AGENT_READY_WEBMCP__={tools:[{name:'site_discovery',description:'Read public site discovery metadata',inputSchema:{type:'object',properties:{topic:{type:'string'}}}}]};</script>\";",
    "      html = html.includes(\"</body>\") ? html.replace(\"</body>\", script + \"</body>\") : html + script;",
    "    }",
    "    return new Response(html, {",
    "      status: response.status,",
    "      statusText: response.statusText,",
    "      headers",
    "    });",
    "  }",
    "",
    "  return new Response(response.body, {",
    "    status: response.status,",
    "    statusText: response.statusText,",
    "    headers",
    "  });",
    "}",
    ""
  ].join("\n");
}

function x402Source(siteOrigin, name) {
  return [
    `const ORIGIN = ${JSON.stringify(siteOrigin)};`,
    `const SITE_NAME = ${JSON.stringify(name)};`,
    "",
    "export async function onRequestGet(context) {",
    "  const request = context.request;",
    "  const signature = request.headers.get(\"payment-signature\") || request.headers.get(\"PAYMENT-SIGNATURE\") || request.headers.get(\"x-payment\");",
    "",
    "  if (!signature) {",
    "    const requirements = {",
    "      x402Version: 1,",
    "      accepts: [",
    "        {",
    "          scheme: \"exact\",",
    "          network: \"base-sepolia\",",
    "          maxAmountRequired: \"1000000\",",
    "          resource: ORIGIN + \"/api/v1\",",
    "          description: SITE_NAME + \" paid agent review discovery. Public website browsing remains free.\",",
    "          mimeType: \"application/json\",",
    "          payTo: \"0x0000000000000000000000000000000000000000\",",
    "          maxTimeoutSeconds: 300,",
    "          asset: \"0x0000000000000000000000000000000000000000\"",
    "        }",
    "      ]",
    "    };",
    "    return new Response(JSON.stringify({ error: \"payment_required\", ...requirements }, null, 2), {",
    "      status: 402,",
    "      headers: {",
    "        \"content-type\": \"application/json; charset=utf-8\",",
    "        \"payment-required\": btoa(JSON.stringify(requirements))",
    "      }",
    "    });",
    "  }",
    "",
    "  return Response.json({",
    "    ok: true,",
    "    settlement: \"not_verified_by_this_demo_route\",",
    "    message: \"Payment signature was supplied. Configure a production x402 facilitator before claiming settlement.\",",
    "    site: SITE_NAME",
    "  });",
    "}",
    ""
  ].join("\n");
}
