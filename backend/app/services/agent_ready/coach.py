from __future__ import annotations

from typing import Any


def _layer_entries(smart: dict[str, Any]) -> list[tuple[str, dict[str, Any]]]:
    layers = smart.get("layers") or {}
    out: list[tuple[str, dict[str, Any]]] = []
    for key, layer in layers.items():
        if isinstance(layer, dict) and layer.get("percent") is not None:
            out.append((key, layer))
    out.sort(key=lambda item: item[1].get("percent", 0))
    return out


def _p0_count(recommendations: list[dict[str, Any]]) -> int:
    return sum(1 for r in recommendations if r.get("priority") == "P0")


def build_coach_brief(analyze: dict[str, Any], *, previous: dict[str, Any] | None = None) -> dict[str, Any]:
    """Rule-based coach — synthesizes scan into actionable narrative (no dumb script dump)."""
    summary = analyze.get("summary") or {}
    smart = analyze.get("smart_scorecard") or {}
    recs = list(analyze.get("recommendations") or [])
    growth = summary.get("growth_percent") or smart.get("growth_score") or summary.get("percent") or 0
    protocol = summary.get("protocol_percent") or analyze.get("agent_native_score") or 0
    smart_pct = summary.get("smart_percent") or smart.get("smart_score") or 0
    p0 = _p0_count(recs)
    weak_layers = _layer_entries(smart)[:3]
    revenue_actions = list(smart.get("revenue_actions") or [])[:5]

    prev_growth = None
    if previous:
        prev_summary = previous.get("summary") or {}
        prev_smart = previous.get("smart_scorecard") or {}
        prev_growth = (
            prev_summary.get("growth_percent")
            or prev_smart.get("growth_score")
            or prev_summary.get("percent")
        )

    delta = None
    delta_narrative_en = ""
    delta_narrative_th = ""
    if prev_growth is not None and growth is not None:
        delta = round(float(growth) - float(prev_growth), 1)
        if delta > 0:
            delta_narrative_en = f"Growth Score up {delta} pts since your last scan — deploy wins are showing."
            delta_narrative_th = f"Growth Score เพิ่ม {delta} จุดจากครั้งก่อน — การ deploy เริ่มเห็นผลแล้ว"
        elif delta < 0:
            delta_narrative_en = f"Growth Score down {abs(delta)} pts — re-check CDN cache and discovery files."
            delta_narrative_th = f"Growth Score ลด {abs(delta)} จุด — ตรวจ CDN cache และไฟล์ discovery อีกครั้ง"
        else:
            delta_narrative_en = "Score unchanged — finish deploying the fix pack, then re-scan."
            delta_narrative_th = "คะแนนเท่าเดิม — deploy fix pack ให้ครบแล้ว re-scan"

    honest = smart.get("honest_verdict") or ""
    if not honest:
        if p0 >= 3:
            honest = f"{p0} urgent protocol gaps block agents and revenue crawlers — fix pack addresses most in one pass."
        elif growth < 50:
            honest = "Discovery layer is thin — agents cannot reliably find APIs, auth, or commerce signals yet."
        else:
            honest = "Solid base — focus on PageSpeed + revenue attribution to push Growth Score past 75%."

    headline_en = f"Growth {growth}% · Protocol {protocol}% · {p0} urgent fixes"
    headline_th = f"Growth {growth}% · Protocol {protocol}% · แก้ด่วน {p0} จุด"

    executive_en = honest
    executive_th = honest
    if growth < 40:
        executive_th = (
            f"เว็บยังไม่พร้อมสำหรับ agent อย่างเต็มที่ — Protocol {protocol}% · Growth {growth}% "
            f"มี {p0} จุดที่ต้องแก้ก่อนรายได้จะโต"
        )
    elif growth >= 75:
        executive_th = f"ใกล้เป้าแล้ว — Growth {growth}% โฟกัส revenue proof และ outreach ต่อได้เลย"

    next_steps_en = [
        "Copy the MCP prompt → let your AI apply the fix pack securely",
        "Deploy discovery files (robots.txt, llms.txt, .well-known/*) to production",
        "Re-scan here (free) after deploy to confirm before → after lift",
    ]
    if p0:
        top = recs[0]
        next_steps_en.insert(0, f"P0: {top.get('fix') or top.get('problem')} ({top.get('path')})")

    next_steps_th = [
        "คัดลอก MCP prompt → ให้ AI ของคุณ apply fix pack อย่างปลอดภัย",
        "Deploy ไฟล์ discovery ขึ้น production",
        "Re-scan ที่นี่ (ฟรี) หลัง deploy เพื่อดู before → after",
    ]
    if p0 and recs:
        top = recs[0]
        next_steps_th.insert(0, f"P0: {top.get('fix') or top.get('problem')}")

    weakest = [
        {
            "id": key,
            "label": layer.get("label") or key,
            "percent": layer.get("percent"),
            "hint": _layer_hint(key, layer.get("percent")),
        }
        for key, layer in weak_layers
    ]

    return {
        "headline_en": headline_en,
        "headline_th": headline_th,
        "executive_summary_en": executive_en,
        "executive_summary_th": executive_th,
        "scores": {
            "growth_percent": growth,
            "protocol_percent": protocol,
            "smart_percent": smart_pct,
            "delta_growth": delta,
        },
        "delta_narrative_en": delta_narrative_en,
        "delta_narrative_th": delta_narrative_th,
        "priority_fixes": recs[:6],
        "weakest_layers": weakest,
        "revenue_queue": revenue_actions,
        "next_steps_en": next_steps_en[:5],
        "next_steps_th": next_steps_th[:5],
        "scan_level": (analyze.get("scan") or {}).get("level"),
        "scan_level_name": (analyze.get("scan") or {}).get("level_name"),
    }


def _layer_hint(layer_id: str, percent: int | float | None) -> str:
    pct = int(percent or 0)
    hints = {
        "performance": "PageSpeed / CWV — impacts conversion and agent timeout budgets",
        "crawler_access": "robots + signals — bots may be blocked or misled",
        "bot_readability": "thin HTML for agents — improve Markdown negotiation",
        "seo": "entity + schema — trust layer for AI citations",
        "aeo": "llms.txt + answer surfaces — AEO discovery",
        "aaio": "API catalog + MCP cards — agent commerce",
    }
    base = hints.get(layer_id, "Improve this pillar in the fix pack")
    if pct < 40:
        return f"Critical: {base}"
    if pct < 70:
        return f"Improve: {base}"
    return f"Maintain: {base}"


def build_session_state(
    *,
    analyze: dict[str, Any],
    coach: dict[str, Any],
    fix_pack: dict[str, Any] | None = None,
    progress: dict[str, Any] | None = None,
    initial_analyze: dict[str, Any] | None = None,
) -> dict[str, Any]:
    files = (fix_pack or {}).get("files") or {}
    slim_pack = {
        "url": (fix_pack or {}).get("url"),
        "strategy": (fix_pack or {}).get("strategy"),
        "file_count": len(files),
        "file_names": sorted(files.keys())[:20],
        "has_mcp_tool": bool((fix_pack or {}).get("mcp_tool")),
    }
    return {
        "latest_scan": _slim_analyze(analyze),
        "initial_scan": _slim_analyze(initial_analyze) if initial_analyze else None,
        "coach": coach,
        "fix_pack_meta": slim_pack,
        "fix_pack": fix_pack,
        "progress": progress or {"scanned": True, "fix_pack_ready": bool(files), "mcp_applied": False, "reverified": False},
    }


def _slim_analyze(analyze: dict[str, Any]) -> dict[str, Any]:
    if not analyze:
        return {}
    return {
        "url": analyze.get("url"),
        "summary": analyze.get("summary"),
        "scan": analyze.get("scan"),
        "recommendations": analyze.get("recommendations"),
        "smart_scorecard": analyze.get("smart_scorecard"),
        "growth_score": analyze.get("growth_score"),
        "smart_score": analyze.get("smart_score"),
        "deploy_plan": analyze.get("deploy_plan"),
        "recorded_at": analyze.get("recorded_at"),
    }