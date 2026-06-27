from __future__ import annotations

import asyncio
from typing import Any
from urllib.parse import urlparse

import httpx

from app.services.agent_ready.url_utils import normalize_site_url as _normalize_site_url

# Paths we snapshot as text for before[] boxes (live origin).
DISCOVERY_SNAPSHOT_PATHS: list[str] = [
    "robots.txt",
    "llms.txt",
    "agents.txt",
    "ai.txt",
    "sitemap.xml",
    ".well-known/api-catalog",
    ".well-known/agent-card.json",
    ".well-known/mcp/server-card.json",
    ".well-known/agent-skills/index.json",
    "openapi.json",
    "auth.md",
]

TEXT_EXTENSIONS = {".txt", ".md", ".json", ".jsonld", ".html", ".xml", ""}


def host_slug(url: str) -> str:
    parsed = urlparse(_normalize_site_url(url))
    host = (parsed.hostname or "unknown").lower().removeprefix("www.")
    return host.replace(":", "_")


async def fetch_one(client: httpx.AsyncClient, base: str, path: str) -> tuple[str, str | None, int | None]:
    url = f"{base}/{path.lstrip('/')}"
    try:
        res = await client.get(url, follow_redirects=True)
        if res.status_code >= 400:
            return path, None, res.status_code
        ctype = (res.headers.get("content-type") or "").lower()
        if "text" not in ctype and "json" not in ctype and "markdown" not in ctype and "xml" not in ctype:
            if path.endswith((".txt", ".md", ".json", ".html", ".xml")):
                pass
            else:
                return path, None, res.status_code
        text = res.text
        if len(text) > 500_000:
            text = text[:500_000] + "\n... [truncated]\n"
        return path, text, res.status_code
    except Exception:  # noqa: BLE001
        return path, None, None


async def fetch_live_discovery_files(url: str, *, timeout: float = 15.0) -> dict[str, Any]:
    """Download current live discovery files for before[] archive."""
    base = _normalize_site_url(url)
    async with httpx.AsyncClient(
        timeout=timeout,
        headers={"User-Agent": "OBOLLA-AgentReady-Archive/1.0 (+https://obolla.com)"},
    ) as client:
        results = await asyncio.gather(
            *[fetch_one(client, base, p) for p in DISCOVERY_SNAPSHOT_PATHS]
        )
    files: dict[str, str] = {}
    meta: dict[str, Any] = {"fetched_at": None, "paths": {}}
    from datetime import datetime, timezone

    meta["fetched_at"] = datetime.now(timezone.utc).isoformat()
    for path, content, status in results:
        meta["paths"][path] = {"status": status, "found": content is not None}
        if content is not None:
            files[path] = content
    return {"files": files, "meta": meta, "url": base}