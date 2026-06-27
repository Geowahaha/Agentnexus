"""Generate PageSpeed / CWV fix guidance for fix packs."""

from __future__ import annotations

from typing import Any


def build_pagespeed_fix_md(site_url: str, performance: dict[str, Any] | None) -> str:
    perf = performance or {}
    score = perf.get("pagespeed_score") or perf.get("percent") or "—"
    lcp = perf.get("lcp_ms")
    cls = perf.get("cls")
    inp = perf.get("inp_ms")

    lcp_fix = (
        f"- **LCP {lcp}ms** (target ≤2500ms): Server-render above-the-fold HTML; preload hero image/font; "
        "defer non-critical JS; avoid hiding hero behind scroll-reveal until JS runs."
        if lcp and lcp > 2500
        else "- LCP: maintain ≤2500ms after deploy."
    )
    cls_fix = (
        f"- **CLS {cls}** (target ≤0.1): Set explicit width/height on images; reserve space for ads/embeds; "
        "avoid injecting banners above existing content."
        if cls and cls > 0.1
        else "- CLS: maintain ≤0.1."
    )
    inp_fix = (
        f"- **INP {inp}ms** (target ≤200ms): Split long tasks; reduce main-thread JS on interaction."
        if inp and inp > 200
        else "- INP: monitor after JS bundle diet."
    )

    return f"""# PageSpeed & Core Web Vitals — Revenue Impact Fix Pack

Site: **{site_url}**
Current PageSpeed (lab): **{score}/100**

## Why this matters for revenue
- Google uses CWV in ranking → more organic traffic.
- Every ~100ms faster LCP can lift conversions ~1% (retail benchmarks).
- Slow mobile = higher bounce = lost leads before they see your offer.

## Targets (customer growth criteria)
| Metric | Target | Your scan |
|--------|--------|-----------|
| PageSpeed | ≥75 | {score} |
| LCP | ≤2500ms | {lcp or '—'} |
| CLS | ≤0.1 | {cls or '—'} |
| INP | ≤200ms | {inp or '—'} |

## P0 fixes (deploy this week)
{lcp_fix}
{cls_fix}
{inp_fix}
- **Thin HTML shell**: Ensure default HTML includes H1 + 400+ words (not JS-only SPA) — helps bots AND LCP text paint.
- **Cache**: Long-cache static assets; `immutable` on hashed JS/CSS bundles.

## Stack-specific
- **Cloudflare Worker + SPA**: Serve bot-readable `<main>` HTML for crawler UAs; keep SPA for humans.
- **Next.js**: Use SSR/SSG for marketing pages; `next/font` with `display: swap`.
- **WordPress**: Lazy-load images; critical CSS inline; disable render-blocking plugins on homepage.

## Verify
1. Re-run AIBotAuth deep scan or PageSpeed Insights after deploy.
2. `POST /api/v1/agent-ready/smart-scan` — PageSpeed pillar should reach ≥75.
3. Log before/after in OBOLLA moat for revenue attribution on your next client pitch.

Source: paid AIBotAuth deep scan + OBOLLA Growth Score criteria.
"""