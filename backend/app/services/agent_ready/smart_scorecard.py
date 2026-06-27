"""OBOLLA Smart Visibility Scorecard — AIBotAuth + isitagentready + SEO/AEO/AAIO layers."""

from __future__ import annotations

import json
import re
from typing import Any

import httpx

from app.core.config import settings
from app.core.mcp_http import HttpMcpClient
from app.expert_skills.site_intelligence import gather_site_intelligence
from app.services.agent_ready.aibotauth_deep_scan import (
    deep_scan_layers,
    load_reference_deep_scan,
    parse_deep_scan_payload,
)
from app.services.agent_ready.growth_scorecard import build_growth_scorecard
from app.services.agent_ready.fix_pack import fetch_page_content
from app.services.agent_ready.isitagentready_client import IsitagentreadyClient

BOT_USER_AGENTS = [
    ("GPTBot", "GPTBot/1.0"),
    ("OAI-SearchBot", "OAI-SearchBot/1.0"),
    ("ChatGPT-User", "ChatGPT-User/1.0"),
    ("ClaudeBot", "ClaudeBot/1.0"),
    ("Claude-SearchBot", "Claude-SearchBot/1.0"),
    ("PerplexityBot", "PerplexityBot/1.0"),
    ("Googlebot", "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)"),
    ("Bingbot", "Mozilla/5.0 (compatible; bingbot/2.0; +http://www.bing.com/bingbot.htm)"),
]

_THIN_CHAR_THRESHOLD = 320
_TAG_RE = re.compile(r"<[^>]+>")
_SCRIPT_STYLE_RE = re.compile(r"<(script|style)[^>]*>.*?</\1>", re.IGNORECASE | re.DOTALL)
_WS_RE = re.compile(r"\s+")


def _visible_text(html: str) -> str:
    cleaned = _SCRIPT_STYLE_RE.sub(" ", html)
    text = _TAG_RE.sub(" ", cleaned)
    return _WS_RE.sub(" ", text).strip()


async def _probe_bot_readability(url: str) -> dict[str, Any]:
    """Mirror AIBotAuth free scan: 8 crawlers + thin-content detection."""
    rows: list[dict[str, Any]] = []
    async with httpx.AsyncClient(timeout=20.0, follow_redirects=True) as client:
        for name, ua in BOT_USER_AGENTS:
            try:
                res = await client.get(
                    url,
                    headers={"User-Agent": ua, "Accept": "text/html,application/xhtml+xml"},
                )
                html = res.text[:200_000]
                text = _visible_text(html)
                char_count = len(text)
                if res.status_code >= 400:
                    result = "blocked"
                elif char_count < _THIN_CHAR_THRESHOLD:
                    result = "served_thin"
                else:
                    result = "can_read"
                rows.append(
                    {
                        "bot": name,
                        "result": result,
                        "http": res.status_code,
                        "visible_chars": char_count,
                    }
                )
            except Exception as exc:  # noqa: BLE001
                rows.append({"bot": name, "result": "error", "http": None, "error": str(exc)[:120]})

    readable = sum(1 for r in rows if r.get("result") == "can_read")
    thin = sum(1 for r in rows if r.get("result") == "served_thin")
    blocked = sum(1 for r in rows if r.get("result") in ("blocked", "error"))
    total = len(rows) or 1
    percent = round(100 * readable / total)
    return {
        "source": "obolla_bot_probe",
        "bots": rows,
        "readable": readable,
        "served_thin": thin,
        "blocked": blocked,
        "total": total,
        "percent": percent,
        "verdict": "thin_spa_shell" if thin >= total - 1 and readable == 0 else (
            "mixed" if thin > 0 else "readable"
        ),
    }


async def _aibotauth_scan(url: str, *, lang: str = "en") -> dict[str, Any] | None:
    api_key = settings.aibotauth_mcp_api_key
    if not api_key:
        return None
    try:
        client = HttpMcpClient(
            settings.aibotauth_mcp_url,
            headers={"Authorization": f"Bearer {api_key}"},
        )
        raw = await client.call_tool("scan", {"url": url, "lang": lang})
        data = json.loads(raw) if raw.strip().startswith("{") else {"raw": raw}
        if isinstance(data, dict) and data.get("status") in (401, 403):
            return None
        return data
    except Exception:
        return None


def _score_seo(intel: dict[str, Any], page: dict[str, str]) -> dict[str, Any]:
    checks: list[dict[str, Any]] = []
    title = intel.get("title") or page.get("title") or ""
    meta = intel.get("meta_description") or page.get("meta_description") or ""
    headings = intel.get("headings") or []
    h1s = [h for h in headings if h.get("level") == "h1"] or [{"text": t} for t in page.get("h1s") or []]
    body_words = len((intel.get("body_text") or page.get("main_content_summary") or "").split())

    def add(cid: str, ok: bool, detail: str) -> None:
        checks.append({"id": cid, "pass": ok, "detail": detail})

    add("title", bool(title and len(title) >= 10), f"title len={len(title)}")
    add("meta_description", bool(meta and len(meta) >= 50), f"meta len={len(meta)}")
    add("single_h1", len(h1s) == 1, f"h1 count={len(h1s)}")
    add("body_depth", body_words >= 80, f"visible words≈{body_words}")
    add("keywords", bool(intel.get("keywords")), f"keywords={len(intel.get('keywords') or [])}")
    add("internal_links", bool(intel.get("internal_links")), f"links={len(intel.get('internal_links') or [])}")

    passed = sum(1 for c in checks if c["pass"])
    return {
        "percent": round(100 * passed / len(checks)) if checks else 0,
        "checks": checks,
        "label": "SEO (on-page)",
    }


def _score_aeo(intel: dict[str, Any], page: dict[str, str], bot_layer: dict[str, Any]) -> dict[str, Any]:
    checks: list[dict[str, Any]] = []

    def add(cid: str, ok: bool, detail: str) -> None:
        checks.append({"id": cid, "pass": ok, "detail": detail})

    summary = (page.get("main_content_summary") or intel.get("body_text") or "")[:2000]
    add("answer_ready_copy", len(summary.split()) >= 60, f"summary words≈{len(summary.split())}")
    add("entity_headings", bool(page.get("h2s") or intel.get("headings")), "H2/sections for answers")
    add("not_thin_to_bots", bot_layer.get("readable", 0) >= 4, f"{bot_layer.get('readable', 0)}/8 bots readable")
    add("intent_clear", bool(intel.get("search_intent")), str(intel.get("search_intent") or "unknown"))

    passed = sum(1 for c in checks if c["pass"])
    return {
        "percent": round(100 * passed / len(checks)) if checks else 0,
        "checks": checks,
        "label": "AEO (AI answers)",
    }


def _score_aaio(iar_summary: dict[str, Any]) -> dict[str, Any]:
    discovery_gaps = [
        g for g in (iar_summary.get("gaps") or [])
        if (g.get("category") or "") in ("discovery", "protocolDiscovery", "discovery ")
        or "discovery" in str(g.get("category", "")).lower()
    ]
    protocol_checks = iar_summary.get("pass", 0) + iar_summary.get("fail", 0)
    protocol_pct = iar_summary.get("percent", 0)
    return {
        "percent": protocol_pct,
        "protocol_percent": protocol_pct,
        "discovery_gaps": len(discovery_gaps),
        "label": "AAIO (agent protocol)",
        "note": "From isitagentready discovery + commerce checks",
    }


def _composite_score(
    layers: dict[str, dict[str, Any]],
    *,
    has_paid_deep: bool = False,
) -> dict[str, Any]:
    if has_paid_deep:
        weights = {
            "aibotauth_deep": 0.22,
            "seo": 0.18,
            "aeo": 0.18,
            "bot_readability": 0.18,
            "aaio": 0.10,
            "performance": 0.14,
            "social": 0.05,
        }
    else:
        weights = {
            "bot_readability": 0.35,
            "seo": 0.25,
            "aeo": 0.20,
            "aaio": 0.15,
            "signed_trust": 0.05,
        }
    total_w = 0.0
    weighted = 0.0
    for key, w in weights.items():
        pct = (layers.get(key) or {}).get("percent")
        if pct is None:
            continue
        weighted += w * float(pct)
        total_w += w
    composite = round(weighted / total_w) if total_w else 0
    return {"percent": composite, "weights": weights, "mode": "paid_deep" if has_paid_deep else "standard"}


async def build_smart_scorecard(
    url: str,
    *,
    lang: str = "en",
    aibotauth_deep_scan: dict[str, Any] | None = None,
) -> dict[str, Any]:
    scanner = IsitagentreadyClient()
    deep_raw = aibotauth_deep_scan or load_reference_deep_scan(url)
    parsed_deep = parse_deep_scan_payload(deep_raw) if deep_raw else None
    has_paid_deep = bool(parsed_deep and parsed_deep.get("paid"))

    iar_scan, bot_probe, intel, page, aibotauth = await _gather_all(url, lang, scanner)

    if parsed_deep and parsed_deep.get("isitagentready"):
        iar_summary = parsed_deep["isitagentready"]
        iar_summary.setdefault("percent", parsed_deep.get("protocol_percent"))
    else:
        iar_summary = scanner.score_summary(iar_scan)

    seo_live = _score_seo(intel, page)
    aeo_live = _score_aeo(intel, page, bot_probe)

    bot_layer = bot_probe
    signed_trust_pct = 0
    proof_hint: dict[str, Any] | None = None
    if aibotauth:
        ab_bots = aibotauth.get("bots") or aibotauth.get("bot_results") or []
        if ab_bots:
            bot_layer = _normalize_aibotauth_bots(ab_bots)
        signed_trust_pct = 100 if aibotauth.get("signed_verified") or aibotauth.get("web_bot_auth") else (
            100 if any("signed" in str(v).lower() for v in aibotauth.values()) else 0
        )
        proof_hint = {
            "overall": aibotauth.get("overall"),
            "grade": aibotauth.get("grade"),
            "headline": aibotauth.get("headline"),
        }

    aaio = _score_aaio(iar_summary)
    layers: dict[str, dict[str, Any]] = {
        "bot_readability": {**bot_layer, "label": "Bot readability (8 crawlers, live)"},
        "seo": seo_live,
        "aeo": aeo_live,
        "aaio": aaio,
        "protocol": {**iar_summary, "label": "Protocol (isitagentready)", "percent": iar_summary.get("percent", 0)},
        "signed_trust": {"percent": signed_trust_pct, "label": "AIBotAuth Ed25519 trust"},
    }

    deep_p0: list[dict[str, Any]] = []
    if parsed_deep:
        deep_layers = deep_scan_layers(parsed_deep)
        layers.update(deep_layers)
        # Paid deep scan authoritative for SEO/AEO; live probe for bot table
        layers["seo"] = {
            **deep_layers["seo"],
            "live_percent": seo_live.get("percent"),
            "checks": seo_live.get("checks"),
        }
        layers["aeo"] = {
            **deep_layers["aeo"],
            "live_percent": aeo_live.get("percent"),
            "checks": aeo_live.get("checks"),
        }
        deep_p0 = list(parsed_deep.get("priority_fixes") or [])
        proof_hint = {
            "overall": parsed_deep.get("overall"),
            "grade": parsed_deep.get("grade"),
            "headline": parsed_deep.get("summary"),
            "paid_deep_scan": True,
            "scanned_at": parsed_deep.get("scanned_at"),
        }

    composite = _composite_score(layers, has_paid_deep=has_paid_deep)
    growth = build_growth_scorecard(
        layers=layers,
        parsed_deep=parsed_deep,
        iar_summary=iar_summary,
        bot_layer=bot_layer,
        has_paid_deep=has_paid_deep,
    )

    p0: list[dict[str, Any]] = list(deep_p0)
    if not has_paid_deep:
        if bot_layer.get("served_thin", 0) >= 4:
            p0.append({
                "priority": "P0",
                "issue": "served_thin",
                "fix": "Server-render HTML or markdown for AI bots — SPA shell is invisible to 8/8 crawlers",
            })
        if seo_live.get("percent", 0) < 60:
            p0.append({"priority": "P0", "issue": "seo_on_page", "fix": "Title, meta, single H1, 80+ words in initial HTML"})
        if aeo_live.get("percent", 0) < 60:
            p0.append({"priority": "P1", "issue": "aeo_content", "fix": "Answer-ready copy + FAQ/schema for AI citations"})
    for gap in (iar_summary.get("gaps") or [])[:3]:
        p0.append({
            "priority": "P1",
            "issue": gap.get("id", "protocol"),
            "fix": gap.get("message", "Fix protocol gap"),
        })

    return {
        "url": url,
        "smart_score": composite["percent"],
        "growth_score": growth["growth_score"],
        "growth_scorecard": growth,
        "composite": composite,
        "layers": layers,
        "isitagentready": iar_summary,
        "aibotauth": proof_hint,
        "aibotauth_deep_scan": parsed_deep,
        "special_offer": {
            "included": has_paid_deep,
            "label": "AIBotAuth.com paid deep scan bundled for paying customers",
            "source": "aibotauth_deep_scan" if has_paid_deep else None,
        },
        "priority_fixes": p0[:15],
        "revenue_actions": growth.get("revenue_actions", []),
        "honest_verdict": growth.get("headline") or _verdict(
            composite["percent"],
            bot_layer,
            iar_summary,
            deep=parsed_deep,
        ),
        "revenue_tracking": {
            "moat_ready": True,
            "tracks": [
                "visibility_events",
                "billing_on_apply",
                "causal_lift_after_deploy",
                "aibotauth_deep_scan",
                "pagespeed_before_after",
                "growth_score_delta",
            ],
            "proof_flow": "Scan → fix pack → deploy → re-scan → AIBotAuth proof URL → close deal",
        },
    }


async def _gather_all(url: str, lang: str, scanner: IsitagentreadyClient):
    import asyncio

    iar_task = scanner.scan(url)
    bot_task = _probe_bot_readability(url)
    intel_task = gather_site_intelligence(url, lang=lang)
    aibotauth_task = _aibotauth_scan(url, lang=lang)
    iar_scan, bot_probe, intel, aibotauth = await asyncio.gather(
        iar_task, bot_task, intel_task, aibotauth_task
    )
    page = fetch_page_content(url)
    return iar_scan, bot_probe, intel, page, aibotauth


def _normalize_aibotauth_bots(ab_bots: list) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    for item in ab_bots:
        if not isinstance(item, dict):
            continue
        name = item.get("bot") or item.get("name") or "bot"
        result = item.get("result") or item.get("status") or "unknown"
        rows.append({
            "bot": name,
            "result": result,
            "http": item.get("http") or item.get("status_code"),
        })
    readable = sum(1 for r in rows if str(r.get("result")).lower() in ("can_read", "ok", "pass"))
    thin = sum(1 for r in rows if "thin" in str(r.get("result")).lower())
    total = len(rows) or 1
    return {
        "source": "aibotauth_mcp",
        "bots": rows,
        "readable": readable,
        "served_thin": thin,
        "total": total,
        "percent": round(100 * readable / total),
    }


def _verdict(
    composite: int,
    bot_layer: dict[str, Any],
    iar: dict[str, Any],
    *,
    deep: dict[str, Any] | None = None,
) -> str:
    proto = iar.get("percent", 0)
    bot = bot_layer.get("percent", 0)
    if deep and deep.get("paid"):
        overall = deep.get("overall")
        grade = deep.get("grade")
        cats = deep.get("categories") or {}
        perf = (deep.get("pagespeed") or {}).get("performanceScore") or deep.get("performance")
        perf_note = f" PageSpeed {perf}/100." if perf is not None else ""
        return (
            f"Paid AIBotAuth deep scan: {overall}% (grade {grade}). "
            f"Technical SEO {cats.get('technical_seo')}%, GEO-AEO {cats.get('geo_aeo')}%, "
            f"crawler access {cats.get('crawler_access')}%.{perf_note} "
            f"Live 8-bot probe: {bot}%. Protocol (isitagentready): {proto}%. "
            f"OBOLLA Smart Score {composite}% blends deep scan + live bots + PageSpeed — not protocol-only."
        )
    if proto >= 90 and bot < 40:
        return (
            f"Protocol looks strong ({proto}%) but bots cannot read your content ({bot}%). "
            "This is not full SEO+AEO+AAIO — fix served_thin first."
        )
    if composite >= 85:
        return "Strong across bots, content, and protocol — ready for revenue attribution tracking."
    if composite >= 60:
        return "Partial — protocol or content gaps remain; apply fix pack and re-scan."
    return "Weak — bots get thin/empty pages; discovery files alone are not enough."