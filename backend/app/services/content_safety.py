"""Platform content safety — scan outbound copy for vulgar or deceptive patterns."""

from __future__ import annotations

import re

# Minimal blocklist for platform-owned strings (not user input moderation).
_BLOCKED_PATTERNS: list[re.Pattern[str]] = [
    re.compile(p, re.IGNORECASE)
    for p in (
        r"\bf+u+c+k",
        r"\bsh+i+t",
        r"\basshole\b",
        r"\bbitch\b",
        r"\bควย\b",
        r"\bหี\b",
        r"\bสัส\b",
        r"\bไอ้สัตว์\b",
        r"\bไอ้เหี้ย\b",
    )
]

_DECEPTIVE_CLAIM_PATTERNS: list[re.Pattern[str]] = [
    re.compile(p, re.IGNORECASE)
    for p in (
        r"we\s+trained\s+this\s+model",
        r"obolla\s+trained",
        r"100%\s+guaranteed",
        r"no\s+risk",
        r"hidden\s+fee",
        r"ไม่มีค่าใช้จ่ายซ่อน",
        r"รับประกัน\s*100",
    )
]


def find_policy_violations(text: str) -> list[str]:
    """Return human-readable violation tags found in *text*."""
    if not text or not text.strip():
        return []
    hits: list[str] = []
    for pattern in _BLOCKED_PATTERNS:
        if pattern.search(text):
            hits.append(f"vulgar:{pattern.pattern}")
    for pattern in _DECEPTIVE_CLAIM_PATTERNS:
        if pattern.search(text):
            hits.append(f"deceptive:{pattern.pattern}")
    return hits


def is_platform_safe(text: str) -> bool:
    return not find_policy_violations(text)


def sanitize_platform_text(text: str, *, fallback: str = "") -> str:
    if is_platform_safe(text):
        return text
    return fallback