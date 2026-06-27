"""Normalize user-supplied site URLs for expert skill workflows."""

from __future__ import annotations

import re
from urllib.parse import urlparse

_URL_IN_TEXT_RE = re.compile(r"https?://[^\s<>\"']+", re.IGNORECASE)
_DOMAIN_RE = re.compile(
    r"^(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}(?:/[^\s]*)?$",
    re.IGNORECASE,
)

_URL_INVALID_MSG = "Please enter a valid URL, e.g. example.com or https://example.com"


def _is_valid_domain(candidate: str) -> bool:
    host = candidate.split("/")[0]
    if "." not in host:
        return False
    return bool(_DOMAIN_RE.match(candidate))


def _validate_parsed_url(url: str) -> bool:
    try:
        parsed = urlparse(url)
    except ValueError:
        return False
    return bool(parsed.scheme in ("http", "https") and parsed.netloc and "." in parsed.hostname)


def normalize_expert_skill_task(task: str) -> str:
    """Add https:// to bare domains; preserve http(s) URLs and trailing task hints."""
    stripped = (task or "").strip()
    if not stripped:
        return stripped

    match = _URL_IN_TEXT_RE.search(stripped)
    if match:
        url = match.group(0).rstrip(".,);]")
        if not _validate_parsed_url(url):
            return stripped
        rest = stripped[match.end() :].strip()
        return f"{url} {rest}".strip() if rest else url

    parts = stripped.split(None, 1)
    candidate = parts[0].rstrip(".,);]")
    rest = parts[1] if len(parts) > 1 else ""

    if _is_valid_domain(candidate):
        url = f"https://{candidate}"
        if _validate_parsed_url(url):
            return f"{url} {rest}".strip() if rest else url

    return stripped


def extract_target_url(task: str) -> str | None:
    """Extract a normalized target URL from a task description."""
    normalized = normalize_expert_skill_task(task)
    match = _URL_IN_TEXT_RE.search(normalized)
    if match:
        url = match.group(0).rstrip(".,);]")
        return url if _validate_parsed_url(url) else None

    parts = normalized.split(None, 1)
    if not parts:
        return None
    candidate = parts[0].rstrip(".,);]")
    if _is_valid_domain(candidate):
        url = f"https://{candidate}"
        return url if _validate_parsed_url(url) else None

    return None