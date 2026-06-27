from __future__ import annotations

import os
from typing import Any
from urllib.parse import urlparse

import httpx

CF_API = "https://api.cloudflare.com/client/v4"


class CloudflareAdapter:
    """Cloudflare API helpers for agent-ready deploy (cache purge, zone lookup)."""

    def __init__(
        self,
        *,
        api_token: str | None = None,
        zone_id: str | None = None,
    ) -> None:
        self.api_token = (api_token or os.environ.get("CLOUDFLARE_API_TOKEN") or "").strip()
        self.default_zone_id = (zone_id or os.environ.get("CLOUDFLARE_ZONE_ID") or "").strip()

    @property
    def configured(self) -> bool:
        return bool(self.api_token)

    def _headers(self) -> dict[str, str]:
        if not self.api_token:
            raise RuntimeError("CLOUDFLARE_API_TOKEN not configured")
        return {
            "Authorization": f"Bearer {self.api_token}",
            "Content-Type": "application/json",
        }

    async def resolve_zone_id(self, url: str) -> str | None:
        if self.default_zone_id:
            return self.default_zone_id
        host = urlparse(url).hostname
        if not host:
            return None
        # Strip www for zone lookup
        zone_name = host.removeprefix("www.")
        async with httpx.AsyncClient(timeout=30.0) as client:
            res = await client.get(
                f"{CF_API}/zones",
                params={"name": zone_name, "status": "active"},
                headers=self._headers(),
            )
            if res.status_code != 200:
                return None
            data = res.json()
            zones = data.get("result") or []
            if zones:
                return zones[0].get("id")
        return None

    async def purge_urls(self, urls: list[str], *, zone_id: str | None = None) -> dict[str, Any]:
        zid = zone_id or self.default_zone_id
        if not zid:
            raise RuntimeError("Cloudflare zone_id required for purge")
        async with httpx.AsyncClient(timeout=60.0) as client:
            res = await client.post(
                f"{CF_API}/zones/{zid}/purge_cache",
                headers=self._headers(),
                json={"files": urls},
            )
            res.raise_for_status()
            payload = res.json()
            if not payload.get("success"):
                raise RuntimeError(f"Cloudflare purge failed: {payload.get('errors')}")
            return {"purged": len(urls), "zone_id": zid, "id": payload.get("result", {}).get("id")}

    def agent_ready_purge_urls(self, base_url: str) -> list[str]:
        base = base_url.rstrip("/")
        paths = [
            "/",
            "/robots.txt",
            "/llms.txt",
            "/ai.txt",
            "/agents.txt",
            "/sitemap.xml",
            "/.well-known/api-catalog",
            "/.well-known/agent-skills/index.json",
            "/.well-known/mcp/server-card.json",
            "/.well-known/agent-card.json",
            "/.well-known/ucp",
            "/.well-known/acp.json",
            "/openapi.json",
            "/api/v1",
        ]
        return [f"{base}{p}" for p in paths]