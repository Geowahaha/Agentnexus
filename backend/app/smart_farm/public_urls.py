"""Absolute public URLs for smart-farm dataset downloads (buyer-facing)."""

from __future__ import annotations

import re

from app.core.config import settings

_DATASET_PATH = re.compile(
    r"/api/v1/smart-farm/datasets/([0-9a-f-]{36})/download",
    re.I,
)

# Buyer-facing links must always use the production edge — never workers.dev or internal API hosts.
OBOLLA_BUYER_ORIGIN = "https://obolla.com"


def public_origin() -> str:
    """Origin for links shown to marketplace buyers."""
    configured = (getattr(settings, "obolla_public_url", None) or OBOLLA_BUYER_ORIGIN).rstrip("/")
    if "workers.dev" in configured or "localhost" in configured or "127.0.0.1" in configured:
        return OBOLLA_BUYER_ORIGIN
    if configured in ("https://obolla.com", "https://www.obolla.com"):
        return OBOLLA_BUYER_ORIGIN
    return configured


def dataset_download_url(pack_id: str) -> str:
    return f"{public_origin()}/api/v1/smart-farm/datasets/{pack_id}/download"


def normalize_buyer_download_url(url: str | None) -> str | None:
    """Rewrite any host to obolla.com for smart-farm dataset download paths."""
    if not url:
        return None
    match = _DATASET_PATH.search(url)
    if match:
        return dataset_download_url(match.group(1))
    if url.startswith("/api/v1/smart-farm/datasets/"):
        pack_match = re.search(
            r"/api/v1/smart-farm/datasets/([0-9a-f-]{36})/download",
            url,
            re.I,
        )
        if pack_match:
            return dataset_download_url(pack_match.group(1))
    return url