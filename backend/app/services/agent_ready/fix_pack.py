from __future__ import annotations

import httpx
import re
from urllib.parse import urlparse

AI_BOTS = [
    "GPTBot",
    "OAI-SearchBot",
    "ChatGPT-User",
    "ClaudeBot",
    "Claude-Web",
    "PerplexityBot",
    "Google-Extended",
    "Applebot-Extended",
    "Applebot",
]


def canonical_www(url: str) -> tuple[str, str]:
    parsed = urlparse(url.rstrip("/"))
    host = parsed.hostname or "localhost"
    base = f"{parsed.scheme}://{host}"
    www = base if host.startswith("www.") else f"{parsed.scheme}://www.{host}"
    return www, host


def fetch_page_content(url: str, timeout: float = 10.0) -> dict[str, str]:
    """Fetch real page text for smarter AEO/SEO summaries. No extra deps."""
    try:
        headers = {"User-Agent": "AIBotAuth-OBOLLA-AutoFix/1.0 (+https://obolla.com)"}
        resp = httpx.get(url, headers=headers, timeout=timeout, follow_redirects=True)
        resp.raise_for_status()
        html = resp.text

        # Basic extraction without BeautifulSoup
        title_match = re.search(r"<title[^>]*>(.*?)</title>", html, re.I | re.S)
        title = title_match.group(1).strip() if title_match else ""

        meta_match = re.search(r'<meta[^>]+name=["\']description["\'][^>]+content=["\']([^"\']+)', html, re.I)
        meta_desc = meta_match.group(1).strip() if meta_match else ""

        # Extract h1/h2
        h1s = re.findall(r"<h1[^>]*>(.*?)</h1>", html, re.I | re.S)[:3]
        h1s = [re.sub(r"<[^>]+>", "", h).strip() for h in h1s if h.strip()]

        h2s = re.findall(r"<h2[^>]*>(.*?)</h2>", html, re.I | re.S)[:5]
        h2s = [re.sub(r"<[^>]+>", "", h).strip() for h in h2s if h.strip()]

        # Extract paragraphs
        p_matches = re.findall(r"<p[^>]*>(.*?)</p>", html, re.I | re.S)
        paragraphs = []
        for p in p_matches:
            clean = re.sub(r"<[^>]+>", "", p).strip()
            if len(clean) > 50:
                paragraphs.append(clean)
            if len(paragraphs) >= 3:
                break

        main_content = " ".join(paragraphs)[:1500]

        return {
            "title": title,
            "meta_description": meta_desc,
            "h1s": h1s,
            "h2s": h2s,
            "main_content_summary": main_content or "No substantial text content extracted.",
            "full_url": str(resp.url),
        }
    except Exception as e:
        return {
            "title": "",
            "meta_description": "",
            "h1s": [],
            "h2s": [],
            "main_content_summary": f"[Could not fetch content: {str(e)[:100]}]",
            "full_url": url,
        }


def build_fix_pack_text_files(site_url: str) -> dict[str, str]:
    www, host = canonical_www(site_url)
    content = fetch_page_content(site_url)

    # Smarter summaries from real content
    real_title = content.get("title") or host
    summary = content.get("main_content_summary", "")[:800]
    h1_text = " ".join(content.get("h1s", [])[:2]) or "key pages and services"
    meta = content.get("meta_description", "")[:300]

    bots = "\n\n".join(f"User-agent: {b}\nAllow: /" for b in AI_BOTS)
    robots = f"""# {host} — agent-ready robots.txt
User-agent: *
Allow: /
Content-Signal: ai-train=no, search=yes, ai-input=yes

{bots}

Sitemap: {www}/sitemap.xml
"""
    # Expanded for SEO + AEO + AAIO with real page content
    llms = f"""# {host} — Machine-readable for LLM agents + Search Engines

> Policy: ai-train=no, search=yes, ai-input=yes. Optimized for traditional SEO, AI Answer Engines (AEO), and autonomous Agents (AAIO).

## About {real_title}
{summary or meta or "Key information about the site and services."}

## Core Pages (SEO + AEO ready)
- [Homepage]({www}/) — Primary landing with H1: {h1_text}
- [Key sections]({www}/) based on content: {", ".join(content.get("h2s", [])[:3]) or "main services"}

## Agent Discovery (AAIO)
- [llms.txt]({www}/llms.txt) — This file
- [agents.txt]({www}/agents.txt)
- [ai.txt]({www}/ai.txt)
- [robots.txt]({www}/robots.txt) — AI crawler rules + Content-Signal

## Structured Data & Commerce (SEO + AEO + AAIO)
- [API Catalog]({www}/.well-known/api-catalog)
- [OpenAPI / Schema]({www}/openapi.json)
- [Auth & Commerce]({www}/auth.md) — UCP / ACP / x402

Agents & search engines: Use clear intent, entities, and structured data from actual page content.
"""

    # Add SEO-specific recommendations
    seo_schema = f"""{{
  "@context": "https://schema.org",
  "@type": "WebSite",
  "name": "{host}",
  "url": "{www}",
  "potentialAction": {{
    "@type": "SearchAction",
    "target": "{www}/search?q={{search_term_string}}",
    "query-input": "required name=search_term_string"
  }},
  "sameAs": ["https://twitter.com/..."] 
}}"""

    aeo_faq = """<!-- AEO: Add FAQPage or HowTo schema on service pages for direct AI answers -->"""

    agents = f"""# agents.txt — {host} (AAIO)

contact: {www}/contact
policy: {www}/ai.txt
allowed-paths: /, /services, /blog, /contact
catalog: {www}/.well-known/api-catalog
skills: MCP / WebMCP ready (see API catalog)

# Optimized for autonomous agents + revenue attribution via OBOLLA skills
"""
    ai = f"""# ai.txt — {host} (AEO + AAIO)
ai-train: no
search: yes
ai-input: yes

Key from page: {summary[:400] or "Content optimized for agents and AI answers."}

See:
- {www}/llms.txt (full agent map)
- {www}/agents.txt
- Structured data for SEO/AEO: {www}/.well-known/api-catalog
"""

    api_catalog = f"""{{
  "@context": "https://schema.org",
  "@type": "APIReference",
  "name": "{host} API",
  "url": "{www}/api",
  "documentation": "{www}/auth.md",
  "target": {{
    "@type": "EntryPoint",
    "urlTemplate": "{www}/api/v1",
    "httpMethod": "GET",
    "contentType": "application/json"
  }}
}}"""

    # Update deploy_md to reference real content
    deploy_md = f"""# Agent-Ready deploy bundle (SEO + AEO + AAIO + Revenue Attribution)

Generated for **{www}** using actual page content from {content.get("full_url", www)}.

Title: {real_title}
Summary used: {summary[:200]}...

## SEO (Traditional)
- Improve Core Web Vitals, on-page based on extracted H1/H2, schema.
- Target Google/Bing rankings + AI citations.

## AEO (AI Answer Engines)
- Use extracted content for direct answers, entity optimization.
- FAQ/HowTo schema for Perplexity, ChatGPT Search, etc.

## AAIO (Agent Optimization)
- Full discovery stack using real site structure.
- Make site legible for autonomous agents.

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
node scripts/agent-ready-auto-deploy.mjs {www} --verify-only
```
Then run OBOLLA skills and check Creator Dashboard for attributed revenue.
"""
    agents = f"""# agents.txt for {host}

contact: {www}/contact
policy: {www}/ai.txt
allowed-paths: /, /services, /blog, /contact
catalog: {www}/.well-known/api-catalog
skills: {www}/agent-skills (if available)

# This site supports agent interactions via discovery files and API.
"""
    ai = f"""# ai.txt — {host}
ai-train: no
search: yes
ai-input: yes

See also:
- {www}/llms.txt
- {www}/agents.txt
- {www}/robots.txt
"""

    api_catalog = (
        '{\n  "linkset": [\n    {\n      "anchor": "'
        + f"{www}/api"
        + '",\n      "item": [\n        { "rel": "service-desc", "href": "'
        + f"{www}/openapi.json"
        + '", "type": "application/json" },\n        { "rel": "service-doc", "href": "'
        + f"{www}/auth.md"
        + '", "type": "text/markdown" },\n        { "rel": "status", "href": "'
        + f"{www}/api/health"
        + '", "type": "application/json" }\n      ]\n    }\n  ]\n}'
    )
    headers = f"""/*
  Content-Signal: ai-train=no, search=yes, ai-input=yes
  X-Content-Type-Options: nosniff
  Referrer-Policy: strict-origin-when-cross-origin

/robots.txt
  Content-Type: text/plain; charset=utf-8

/llms.txt
  Content-Type: text/plain; charset=utf-8

/ai.txt
  Content-Type: text/plain; charset=utf-8

/agents.txt
  Content-Type: text/plain; charset=utf-8

/.well-known/api-catalog
  Content-Type: application/linkset+json
"""
    deploy_md = f"""# Agent-Ready deploy bundle (SEO + AEO + AAIO + Revenue Attribution)

Generated for **{www}** (OBOLLA Agent-Ready Auto Fix).

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
node scripts/agent-ready-auto-deploy.mjs {www} --verify-only
```
Then run OBOLLA skills and check Creator Dashboard for attributed revenue.
"""

    revenue_note = f"""# Revenue Attribution Note
Fixes above are designed to increase:
- Traditional search traffic (SEO)
- AI answer citations (AEO)
- Autonomous agent executions (AAIO)

All executions on OBOLLA can be logged for revenue (via logged outreach → sale flow).
This powers the closed AIBotAuth + OBOLLA moat and creator earnings.
"""
    return {
        "robots.txt": robots,
        "llms.txt": llms,
        "agents.txt": agents,
        "ai.txt": ai,
        ".well-known/api-catalog": api_catalog,
        "_headers": headers,
        "seo-schema.jsonld": seo_schema,
        "aeo-faq-example.html": aeo_faq,
        "AGENT-READY-DEPLOY.md": deploy_md,
        "REVENUE-ATTRIBUTION.md": revenue_note,
    }


def generate_diff_for_file(filename: str, new_content: str, original_content: str = "") -> str:
    """Generate a simple unified diff for a file (PR-ready friendly)."""
    if not original_content:
        original_content = "# original content not available - this is the proposed new file\n"
    header = f"diff --git a/{filename} b/{filename}\nindex 0000000..0000000 100644\n--- a/{filename}\n+++ b/{filename}\n"
    diff_body = ""
    orig_lines = original_content.splitlines(keepends=True)
    new_lines = new_content.splitlines(keepends=True)
    # Simple approach: full replace as new for clarity in most cases
    diff_body += "@@ -1," + str(len(orig_lines)) + " +" + str(len(new_lines)) + " @@\n"
    for line in orig_lines:
        diff_body += "-" + line
    for line in new_lines:
        diff_body += "+" + line
    return header + diff_body


def build_enhanced_fix_pack_with_diffs(site_url: str, existing_files: dict[str, str] | None = None) -> dict[str, Any]:
    """Stronger generator: includes diffs and PR-ready patches for each file."""
    files = build_fix_pack_text_files(site_url)
    diffs: dict[str, str] = {}
    for name, content in files.items():
        orig = existing_files.get(name, "") if existing_files else ""
        diffs[name] = generate_diff_for_file(name, content, orig)
    return {
        "files": files,
        "diffs": diffs,
        "pr_ready_note": "Use these diffs to create a PR. Each file has unified diff format.",
        "apply_instructions": "Preferred: Use MCP (secure, no local bridge) - see mcp_tool below or connect your AI client to OBOLLA MCP. Alternatives: GitHub PR or CF Pages (existing endpoints). Bridge is optional/local only if you prefer.",
    }


def repo_paths_for_strategy(strategy: str, files: dict[str, str]) -> dict[str, str]:
    """Map bundle filenames to repository paths for GitHub PR."""
    if strategy in ("nextjs_app_router", "nextjs"):
        prefix = "public"
        mapped = {f"{prefix}/{name}": content for name, content in files.items() if name != "_headers"}
        mapped["agent-ready/_headers"] = files["_headers"]
        mapped["agent-ready/AGENT-READY-DEPLOY.md"] = files["AGENT-READY-DEPLOY.md"]
        return mapped
    return dict(files)


def pages_bundle(files: dict[str, str]) -> dict[str, str]:
    """Root-relative paths for Cloudflare Pages direct upload."""
    return dict(files)