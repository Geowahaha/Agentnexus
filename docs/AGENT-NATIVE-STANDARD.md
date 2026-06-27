# Agent-Native Web Standard (Draft v0.1)

## Goal
Make websites easily understandable and actionable by AI agents, similar to how SEO made them friendly for search engines.

## Core Requirements for Agent-Friendly Sites

### 1. Discoverability
- robots.txt with AI-specific directives
- llms.txt (Markdown link map)
- ai.txt / agents.txt
- Proper Link headers and sitemap

### 2. Content Accessibility
- Markdown negotiation (Accept: text/markdown)
- Clean, semantic HTML
- Structured data (JSON-LD)

### 3. API / Action Layer
- api-catalog (OpenAPI or MCP)
- OAuth / Auth discovery
- x402 / payment stubs if monetized

### 4. Proof & Trust
- Verifiable output via isitagentready.com
- Signed proofs

## Tools & Primitives (AgentNexus)

- AgentReadyOrchestrator (analyze + generate fix pack)
- Fix pack generators (for Next.js, Cloudflare, WordPress, static)
- Headers and policy templates

## Recommended Implementation

### Next.js
```ts
// middleware.ts
export { agentNativeMiddleware } from '@agentnexus/next'
```

### Cloudflare
Use Workers + Headers + D1 for catalogs.

### WordPress
Plugin to generate llms.txt + headers.

## Version
0.1 - 2026
See also: isitagentready.com taxonomy
