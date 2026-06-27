import logging

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)


def _bridge_dispatch_urls() -> list[str]:
    urls: list[str] = []
    for preferred in ("https://obolla.com", "https://www.obolla.com"):
        urls.append(preferred)
    primary = (settings.notify_worker_url or "").rstrip("/")
    if primary and primary not in urls:
        urls.append(primary)
    return urls


async def dispatch_bridge_tool(
    *,
    user_id: str,
    device_id: str,
    tool: str,
    args: dict,
    timeout_ms: int = 30_000,
) -> dict:
    secret = settings.internal_notify_secret
    if not secret:
        return {"ok": False, "error": "bridge_edge_not_configured"}

    dispatch_urls = _bridge_dispatch_urls()
    if not dispatch_urls:
        return {"ok": False, "error": "bridge_edge_not_configured"}

    payload = {
        "user_id": user_id,
        "device_id": device_id,
        "tool": tool,
        "args": args,
        "timeout_ms": timeout_ms,
    }

    try:
        async with httpx.AsyncClient(timeout=timeout_ms / 1000 + 5) as client:
            last_status = 0
            last_body = ""
            for base_url in dispatch_urls:
                url = f"{base_url}/internal/bridge/dispatch"
                response = await client.post(
                    url,
                    json=payload,
                    headers={"X-Bridge-Secret": secret},
                )
                if response.status_code == 404:
                    last_status = response.status_code
                    last_body = response.text
                    logger.warning("Bridge dispatch 404 at %s — trying fallback", base_url)
                    continue
                if response.status_code >= 400:
                    logger.warning("Bridge dispatch failed: %s %s", response.status_code, response.text)
                    return {"ok": False, "error": f"bridge_dispatch_http_{response.status_code}"}
                return response.json()
            logger.warning(
                "Bridge dispatch failed: no reachable edge URL (last %s %s)",
                last_status,
                last_body,
            )
            return {"ok": False, "error": f"bridge_dispatch_http_{last_status or 404}"}
    except Exception as exc:
        logger.warning("Bridge dispatch error: %s", exc)
        return {"ok": False, "error": str(exc)}