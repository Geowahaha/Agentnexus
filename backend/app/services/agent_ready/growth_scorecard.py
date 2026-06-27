"""Revenue Growth Score — criteria aligned to measurable business outcomes."""

from __future__ import annotations

from typing import Any


# Criteria customers see on /agent-ready (revenue = main point)
GROWTH_CRITERIA = [
    {
        "id": "discover",
        "label": "Discoverability",
        "revenue_link": "AI + Google can find you → inbound leads",
        "weight": 0.18,
    },
    {
        "id": "content_aeo",
        "label": "Content & AEO",
        "revenue_link": "Answer-ready pages → AI citations & trust",
        "weight": 0.18,
    },
    {
        "id": "pagespeed",
        "label": "PageSpeed / CWV",
        "revenue_link": "Faster site → better rank, lower bounce, more sales",
        "weight": 0.15,
    },
    {
        "id": "convert",
        "label": "Share & Convert",
        "revenue_link": "OG/schema/social → higher CTR from shares",
        "weight": 0.14,
    },
    {
        "id": "agent_commerce",
        "label": "Agent Commerce (AAIO)",
        "revenue_link": "Agents can discover APIs & checkout paths",
        "weight": 0.10,
    },
    {
        "id": "measurable_roi",
        "label": "Measurable ROI",
        "revenue_link": "Proof + before/after + OBOLLA attribution",
        "weight": 0.25,
    },
]


def build_growth_scorecard(
    *,
    layers: dict[str, dict[str, Any]],
    parsed_deep: dict[str, Any] | None,
    iar_summary: dict[str, Any],
    bot_layer: dict[str, Any],
    has_paid_deep: bool,
) -> dict[str, Any]:
    """Composite score optimized for customer revenue growth, not protocol vanity."""
    cats = (parsed_deep or {}).get("categories") or {}
    perf = layers.get("performance") or {}

    discover = _avg(
        bot_layer.get("percent"),
        layers.get("protocol", {}).get("percent") or iar_summary.get("percent"),
        cats.get("crawler_access"),
    )
    content_aeo = _avg(cats.get("geo_aeo"), layers.get("aeo", {}).get("percent"))
    pagespeed = perf.get("percent") or perf.get("pagespeed_score") or 0
    convert_share = _avg(cats.get("technical_seo"), cats.get("social_og"), layers.get("seo", {}).get("percent"))
    agent_commerce = layers.get("aaio", {}).get("percent") or iar_summary.get("percent", 0)
    measurable = _measurable_roi_score(parsed_deep, has_paid_deep, iar_summary, bot_layer)

    pillar_scores = {
        "discover": round(discover),
        "content_aeo": round(content_aeo),
        "pagespeed": round(pagespeed),
        "convert": round(convert_share),
        "agent_commerce": round(agent_commerce),
        "measurable_roi": round(measurable),
    }

    weighted = 0.0
    for crit in GROWTH_CRITERIA:
        pct = pillar_scores.get(crit["id"], 0)
        weighted += crit["weight"] * float(pct)
    growth_score = round(weighted)

    actions = _revenue_actions(pillar_scores, perf, parsed_deep)

    return {
        "growth_score": growth_score,
        "pillars": [
            {
                **crit,
                "percent": pillar_scores.get(crit["id"], 0),
                "status": _status(pillar_scores.get(crit["id"], 0)),
            }
            for crit in GROWTH_CRITERIA
        ],
        "pagespeed": {
            "score": pagespeed,
            "lcp_ms": perf.get("lcp_ms"),
            "cls": perf.get("cls"),
            "inp_ms": perf.get("inp_ms"),
            "cwv_ratings": perf.get("cwv_ratings") or [],
            "weight_in_growth": "15%",
            "revenue_impact": "Every 100ms LCP improvement ≈ up to 1% conversion (industry avg). Target ≥75 PageSpeed.",
        },
        "revenue_actions": actions,
        "target_growth_score": 75,
        "headline": _growth_headline(growth_score, pillar_scores),
    }


def _avg(*values: Any) -> float:
    nums = [float(v) for v in values if v is not None and v != ""]
    return sum(nums) / len(nums) if nums else 0.0


def _status(pct: float) -> str:
    if pct >= 75:
        return "strong"
    if pct >= 50:
        return "building"
    return "gap"


def _measurable_roi_score(
    parsed_deep: dict[str, Any] | None,
    has_paid_deep: bool,
    iar: dict[str, Any],
    bot_layer: dict[str, Any],
) -> float:
    points = 0.0
    if has_paid_deep:
        points += 35  # baseline paid scan = proof anchor
    if iar.get("percent", 0) >= 85:
        points += 20
    if bot_layer.get("percent", 0) >= 75:
        points += 25
    else:
        points += bot_layer.get("percent", 0) * 0.2
    points += 20  # OBOLLA moat + MCP apply always available on platform
    return min(100.0, points)


def _revenue_actions(
    pillars: dict[str, int],
    perf: dict[str, Any],
    deep: dict[str, Any] | None,
) -> list[dict[str, str]]:
    actions: list[dict[str, str]] = []

    if pillars.get("pagespeed", 100) < 75:
        lcp = perf.get("lcp_ms")
        cls = perf.get("cls")
        fix = "Defer non-critical JS, preload LCP image/font, fix layout shift"
        if lcp and lcp > 2500:
            fix = f"LCP {lcp}ms — server-render hero, reduce JS blocking, preload LCP asset"
        if cls and cls > 0.1:
            fix += f"; CLS {cls} — set width/height on images, reserve ad space"
        actions.append({"priority": "P0", "pillar": "pagespeed", "action": fix, "revenue": "Speed → rank + checkout completion"})

    if pillars.get("content_aeo", 100) < 50:
        actions.append({
            "priority": "P0",
            "pillar": "content_aeo",
            "action": "Add 400+ words + FAQ schema on homepage/service pages",
            "revenue": "AI citations + long-tail search leads",
        })

    if pillars.get("convert", 100) < 60:
        actions.append({
            "priority": "P1",
            "pillar": "convert",
            "action": "Add og:image, Twitter card, JSON-LD Organization",
            "revenue": "Social shares → referral traffic",
        })

    if pillars.get("discover", 100) < 70:
        actions.append({
            "priority": "P0",
            "pillar": "discover",
            "action": "Server-render content for 8 AI crawlers; keep robots + llms.txt",
            "revenue": "Found in ChatGPT/Perplexity/Google AI",
        })

    actions.append({
        "priority": "P1",
        "pillar": "measurable_roi",
        "action": "Deploy fix pack → re-scan → share AIBotAuth proof URL in outreach",
        "revenue": "Before/after proof closes paid deals (case: SuccessCasting +450 USD)",
    })

    if deep:
        for fix in (deep.get("priority_fixes") or [])[:4]:
            if fix.get("issue") and not any(fix["issue"] in a.get("action", "") for a in actions):
                actions.append({
                    "priority": fix.get("priority", "P1"),
                    "pillar": "content_aeo",
                    "action": str(fix.get("issue")),
                    "revenue": "From paid AIBotAuth deep scan",
                })

    return actions[:8]


def build_revenue_growth_playbook_md(
    site_url: str,
    parsed_deep: dict[str, Any] | None,
    performance: dict[str, Any] | None,
) -> str:
    growth = build_growth_scorecard(
        layers={
            "performance": performance or {},
            "seo": {"percent": (parsed_deep or {}).get("categories", {}).get("technical_seo", 0)},
            "aeo": {"percent": (parsed_deep or {}).get("categories", {}).get("geo_aeo", 0)},
            "aaio": {"percent": (parsed_deep or {}).get("protocol_percent", 0)},
            "protocol": {"percent": (parsed_deep or {}).get("protocol_percent", 0)},
        },
        parsed_deep=parsed_deep,
        iar_summary=(parsed_deep or {}).get("isitagentready") or {},
        bot_layer={"percent": 0},
        has_paid_deep=bool(parsed_deep and parsed_deep.get("paid")),
    )
    lines = [
        f"# Revenue Growth Playbook — {site_url}",
        "",
        f"**Growth Score target:** {growth['target_growth_score']}%+ (current pillars below)",
        "",
        "## Growth criteria (what drives revenue)",
        "",
    ]
    for p in growth["pillars"]:
        lines.append(f"- **{p['label']}** ({int(p['weight']*100)}% weight): {p['percent']}% — {p['revenue_link']}")
    lines.extend(["", "## Priority revenue actions", ""])
    for a in growth.get("revenue_actions") or []:
        lines.append(f"- [{a.get('priority')}] **{a.get('pillar')}**: {a.get('action')} → *{a.get('revenue')}*")
    lines.extend([
        "",
        "## Closed loop (OBOLLA moat)",
        "1. Deploy fix pack (SEO + AEO + AAIO + PageSpeed)",
        "2. Re-scan → Growth Score delta logged automatically",
        "3. Share AIBotAuth proof URL in client outreach",
        "4. Log sale on OBOLLA → creator earnings + causal attribution",
        "",
        "Reference: SuccessCasting 25%→100% agent-ready + documented revenue outreach.",
    ])
    return "\n".join(lines)


def _growth_headline(growth: int, pillars: dict[str, int]) -> str:
    weak = sorted(pillars.items(), key=lambda x: x[1])[:2]
    weak_names = ", ".join(k.replace("_", " ") for k, _ in weak)
    if growth >= 75:
        return f"Growth Score {growth}% — ready to attribute revenue lifts on OBOLLA."
    if growth >= 50:
        return f"Growth Score {growth}% — fix {weak_names} first for measurable revenue impact."
    return f"Growth Score {growth}% — protocol alone won't grow revenue; prioritize {weak_names}."