from __future__ import annotations


def normalize_site_url(url: str) -> str:
    u = (url or "").strip()
    if not u:
        return u
    if not u.startswith(("http://", "https://")):
        u = f"https://{u.lstrip('/')}"
    return u.rstrip("/")