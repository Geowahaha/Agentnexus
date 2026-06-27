"""Parse paid AIBotAuth.com deep scan exports and fold into OBOLLA Smart Score."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

_REFERENCE_DIR = Path(__file__).resolve().parent / "reference_scans"

_CAT_SEO = "Technical SEO (Google 2026)"
_CAT_AEO = "AI Search / GEO-AEO"
_CAT_CRAWLER = "AI Crawler Access"
_CAT_SOCIAL = "Social Sharing & Open Graph"


def _normalize_host(url: str) -> str:
    host = (urlparse(url).hostname or "").lower().strip(".")
    if host.startswith("www."):
        host = host[4:]
    return host


def load_reference_deep_scan(url: str) -> dict[str, Any] | None:
    """Paid customer scans bundled under reference_scans/{host}.json."""
    host = _normalize_host(url)
    if not host:
        return None
    path = _REFERENCE_DIR / f"{host}.json"
    if not path.is_file():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def parse_deep_scan_payload(data: dict[str, Any]) -> dict[str, Any]:
    """Normalize AIBotAuth deep scan JSON (export or API) for scorecard."""
    cats = data.get("_category_scores") or {}
    checks = data.get("_checks") or []
    iar = data.get("_isitagentready") or {}

    findings_by_cat: dict[str, list[dict[str, Any]]] = {}
    for cat in data.get("categories") or []:
        if isinstance(cat, dict) and cat.get("name"):
            findings_by_cat[cat["name"]] = list(cat.get("findings") or [])

    fail_checks = [c for c in checks if isinstance(c, dict) and c.get("status") == "fail"]
    p0 = [
        {
            "priority": "P0" if c.get("severity") in ("critical", "high") else "P1",
            "issue": c.get("check"),
            "category": c.get("category"),
            "fix": c.get("detail") or c.get("check"),
            "severity": c.get("severity"),
        }
        for c in fail_checks[:12]
    ]

    return {
        "source": "aibotauth_deep_scan",
        "paid": bool(data.get("_credits_charged")),
        "url": data.get("url"),
        "overall": data.get("overall"),
        "grade": data.get("grade"),
        "summary": data.get("summary"),
        "scanned_at": data.get("scanned_at"),
        "categories": {
            "technical_seo": cats.get(_CAT_SEO),
            "geo_aeo": cats.get(_CAT_AEO),
            "crawler_access": cats.get(_CAT_CRAWLER),
            "social_og": cats.get(_CAT_SOCIAL),
        },
        "category_scores": cats,
        "performance": data.get("_performance"),
        "performance_verified": data.get("_performance_verified"),
        "pagespeed": data.get("_pagespeed") or data.get("_cwv"),
        "performance_lite": data.get("_performance_lite"),
        "cwv": data.get("_cwv"),
        "isitagentready": iar,
        "protocol_percent": iar.get("percent"),
        "findings_by_category": findings_by_cat,
        "checks_total": len(checks),
        "checks_fail": len(fail_checks),
        "priority_fixes": p0,
        "verification": data.get("_verification"),
        "migration": data.get("_migration"),
        "fetch": data.get("_fetch"),
    }


def deep_scan_layers(parsed: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """Map paid deep scan categories onto Smart Score layers."""
    cats = parsed.get("categories") or {}
    perf = parsed.get("performance")
    return {
        "aibotauth_deep": {
            "percent": parsed.get("overall") or 0,
            "grade": parsed.get("grade"),
            "label": "AIBotAuth Deep Scan (paid)",
            "paid": parsed.get("paid"),
            "scanned_at": parsed.get("scanned_at"),
            "summary": parsed.get("summary"),
        },
        "seo": {
            "percent": cats.get("technical_seo") or 0,
            "label": "SEO — Technical (AIBotAuth deep)",
            "source": "aibotauth_deep",
        },
        "aeo": {
            "percent": cats.get("geo_aeo") or 0,
            "label": "AEO — GEO/AI Search (AIBotAuth deep)",
            "source": "aibotauth_deep",
        },
        "social": {
            "percent": cats.get("social_og") or 0,
            "label": "Social / Open Graph (AIBotAuth deep)",
            "source": "aibotauth_deep",
        },
        "crawler_access": {
            "percent": cats.get("crawler_access") or 0,
            "label": "AI Crawler Access (AIBotAuth deep)",
            "source": "aibotauth_deep",
        },
        "performance": _performance_layer(parsed),
    }


def _performance_layer(parsed: dict[str, Any]) -> dict[str, Any]:
    perf = parsed.get("performance")
    ps = parsed.get("pagespeed") or parsed.get("cwv") or {}
    lite = parsed.get("performance_lite") or {}
    score = int(perf) if perf is not None else int(ps.get("performanceScore") or 0)

    lcp = ps.get("lcp") or {}
    cls = ps.get("cls") or {}
    inp = ps.get("inp")

    def _ms(v: Any) -> int | None:
        if isinstance(v, dict):
            v = v.get("value")
        return int(v) if isinstance(v, (int, float)) else None

    lcp_ms = _ms(lcp)
    cls_val = cls.get("value") if isinstance(cls, dict) else cls
    inp_ms = _ms(inp)

    ratings: list[str] = []
    if lcp_ms is not None:
        ratings.append("LCP " + ("good" if lcp_ms <= 2500 else "needs work" if lcp_ms <= 4000 else "poor"))
    if isinstance(cls_val, (int, float)):
        ratings.append("CLS " + ("good" if cls_val <= 0.1 else "needs work" if cls_val <= 0.25 else "poor"))
    if inp_ms is not None:
        ratings.append("INP " + ("good" if inp_ms <= 200 else "needs work" if inp_ms <= 500 else "poor"))

    return {
        "percent": score,
        "label": "PageSpeed / Core Web Vitals",
        "verified": parsed.get("performance_verified"),
        "source": ps.get("source") or lite.get("source") or "aibotauth_deep",
        "pagespeed_score": score,
        "lcp_ms": lcp_ms,
        "cls": round(float(cls_val), 3) if isinstance(cls_val, (int, float)) else None,
        "inp_ms": inp_ms,
        "cwv_ratings": ratings,
        "html_fetch_ms": lite.get("html_fetch_ms"),
        "html_kb": lite.get("html_kb"),
        "note": (
            "Lab Lighthouse from paid AIBotAuth deep scan."
            if "lighthouse" in str(ps.get("source", "")).lower()
            else (lite.get("note") or "Performance evidence from paid AIBotAuth deep scan.")
        ),
    }