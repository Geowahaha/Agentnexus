from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any
from urllib.parse import urlparse

import httpx

NEXT_MARKERS = ("/_next/static", "__NEXT_DATA__", "next/dist")
WORDPRESS_MARKERS = ("wp-content", "wp-includes", "WordPress")
SHOPIFY_MARKERS = ("cdn.shopify.com", "Shopify.theme")
CLOUDFLARE_MARKERS = ("cf-ray", "cloudflare")


@dataclass
class StackProfile:
    url: str
    host: str
    platform: str
    confidence: float
    signals: list[str] = field(default_factory=list)
    headers: dict[str, str] = field(default_factory=dict)
    deploy_strategy: str = "static"
    deploy_paths: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "url": self.url,
            "host": self.host,
            "platform": self.platform,
            "confidence": self.confidence,
            "signals": self.signals,
            "deploy_strategy": self.deploy_strategy,
            "deploy_paths": self.deploy_paths,
        }


class StackDetector:
    """Fingerprint site stack from HTTP probes (no browser)."""

    async def detect(self, url: str, *, timeout: float = 20.0) -> StackProfile:
        normalized = url.rstrip("/")
        parsed = urlparse(normalized)
        host = parsed.hostname or normalized

        async with httpx.AsyncClient(
            follow_redirects=True,
            timeout=timeout,
            headers={"User-Agent": "AgentNexus-StackDetector/1.0"},
        ) as client:
            home = await self._fetch(client, normalized)
            robots = await self._fetch(client, f"{normalized}/robots.txt")

        headers_lower = {k.lower(): v for k, v in home.headers.items()}
        body = home.text[:120_000]
        signals: list[str] = []
        scores = {
            "nextjs": 0.0,
            "wordpress": 0.0,
            "shopify": 0.0,
            "cloudflare_pages": 0.0,
            "static": 0.1,
        }

        if headers_lower.get("x-powered-by", "").lower().find("next") >= 0:
            scores["nextjs"] += 0.4
            signals.append("header:x-powered-by=Next.js")
        if any(m in body for m in NEXT_MARKERS):
            scores["nextjs"] += 0.5
            signals.append("body:next.js markers")
        if headers_lower.get("x-vercel-id"):
            scores["nextjs"] += 0.2
            signals.append("header:x-vercel-id")
        if any(m in body for m in WORDPRESS_MARKERS):
            scores["wordpress"] += 0.7
            signals.append("body:wordpress markers")
        if any(m in body for m in SHOPIFY_MARKERS):
            scores["shopify"] += 0.7
            signals.append("body:shopify markers")
        if headers_lower.get("cf-ray"):
            scores["cloudflare_pages"] += 0.3
            signals.append("header:cf-ray")
        if headers_lower.get("server", "").lower().find("cloudflare") >= 0:
            scores["cloudflare_pages"] += 0.2
            signals.append("header:server=cloudflare")

        platform = max(scores, key=scores.get)
        confidence = min(0.99, scores[platform])

        deploy_strategy, deploy_paths = self._deploy_hints(platform, host)

        if robots.status_code == 200 and "content-signal" in robots.text.lower():
            signals.append("robots:content-signal present")

        return StackProfile(
            url=str(home.url) or normalized,
            host=host,
            platform=platform,
            confidence=confidence,
            signals=signals,
            headers={k: headers_lower[k] for k in ("server", "x-powered-by", "cf-ray") if k in headers_lower},
            deploy_strategy=deploy_strategy,
            deploy_paths=deploy_paths,
        )

    async def _fetch(self, client: httpx.AsyncClient, url: str) -> httpx.Response:
        return await client.get(url)

    def _deploy_hints(self, platform: str, host: str) -> tuple[str, list[str]]:
        if platform == "nextjs":
            return (
                "nextjs_app_router",
                [
                    "app/robots.txt/route.ts",
                    "app/llms.txt/route.ts",
                    "app/agents.txt/route.ts",
                    "app/ai.txt/route.ts",
                    "next.config.ts (headers + Link)",
                    "app/.well-known/**/route.ts",
                    "npm run build && restart service",
                ],
            )
        if platform == "wordpress":
            return (
                "wordpress",
                [
                    "wp-content/mu-plugins/agent-ready.php",
                    "or child theme functions.php for headers",
                    "upload robots.txt to site root (if static allowed)",
                ],
            )
        if platform == "shopify":
            return (
                "shopify",
                [
                    "theme liquid snippets for meta/link (limited)",
                    "Shopify app or proxy for /.well-known routes",
                ],
            )
        if platform == "cloudflare_pages":
            return (
                "cloudflare_pages",
                [
                    "public/robots.txt",
                    "public/llms.txt",
                    "public/_headers",
                    "functions/_middleware.ts for Link headers",
                    "npx wrangler pages deploy",
                ],
            )
        return (
            "static",
            [
                "public/robots.txt",
                "public/llms.txt",
                "public/agents.txt",
                "public/ai.txt",
                "public/_headers or nginx add_header",
            ],
        )