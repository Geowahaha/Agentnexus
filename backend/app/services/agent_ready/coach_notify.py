from __future__ import annotations

from typing import Any

from app.core.config import settings
from app.services.edge_notify_service import publish_edge_notification
from app.services.transactional_email import send_transactional_email


def _default_email_subject(site_host: str, coach: dict[str, Any]) -> str:
    scores = coach.get("scores") or {}
    growth = scores.get("growth_percent", "—")
    return coach.get("email_subject_th") or f"OBOLLA Agent-Ready · {site_host} · Growth {growth}% (re-scan)"


def _default_email_body(
    *,
    site_url: str,
    site_host: str,
    coach: dict[str, Any],
    user_name: str | None,
) -> str:
    if coach.get("email_body_plain_th"):
        return str(coach["email_body_plain_th"])

    scores = coach.get("scores") or {}
    growth = scores.get("growth_percent", "—")
    protocol = scores.get("protocol_percent", "—")
    delta = scores.get("delta_growth")
    delta_line = f"\nΔ Growth: {delta:+} จุด" if delta is not None else ""
    greeting = f"สวัสดี {user_name}" if user_name else "สวัสดี"
    summary = coach.get("executive_summary_th_business") or coach.get("executive_summary_th") or ""
    steps = coach.get("next_steps_th_business") or coach.get("next_steps_th") or []
    steps_text = "\n".join(f"• {s}" for s in steps[:4])
    return (
        f"{greeting}\n\n"
        f"OBOLLA Agent-Ready re-scan เสร็จแล้วสำหรับ {site_host}\n"
        f"Growth {growth}% · Protocol {protocol}%{delta_line}\n\n"
        f"{summary}\n\n"
        f"ขั้นตอนถัดไป:\n{steps_text}\n\n"
        f"เปิดรายละเอียด: {settings.obolla_public_url.rstrip('/')}/agent-ready\n"
        f"Site: {site_url}"
    )


def _email_html(text: str, site_url: str) -> str:
    escaped = (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace("\n", "<br>\n")
    )
    link = settings.obolla_public_url.rstrip("/") + "/agent-ready"
    return (
        f"<div style='font-family:sans-serif;max-width:560px;line-height:1.5'>"
        f"{escaped}"
        f"<p style='margin-top:16px'><a href='{link}?url={site_url}'>เปิด Agent Coach บน OBOLLA</a></p>"
        f"</div>"
    )


async def notify_rescan_complete(
    *,
    user_id: str,
    user_email: str,
    user_name: str | None,
    site_url: str,
    site_host: str,
    coach: dict[str, Any],
    send_email: bool = True,
) -> dict[str, Any]:
    scores = coach.get("scores") or {}
    growth = scores.get("growth_percent", "—")
    title = f"Agent-Ready re-scan · {site_host}"
    body = coach.get("headline_th_business") or coach.get("headline_th") or f"Growth {growth}%"
    delta = scores.get("delta_growth")
    if delta is not None:
        body += f" (Δ {delta:+})"

    await publish_edge_notification(
        user_id,
        event_type="agent_ready_rescan",
        title=title,
        body=body[:500],
        payload={"site_url": site_url, "site_host": site_host, "growth_percent": growth, "coach": coach},
    )

    email_result: dict[str, str] = {"sent": "false", "reason": "disabled"}
    if send_email and settings.agent_ready_rescan_email_enabled:
        subject = _default_email_subject(site_host, coach)
        plain = _default_email_body(
            site_url=site_url,
            site_host=site_host,
            coach=coach,
            user_name=user_name,
        )
        email_result = await send_transactional_email(
            to_email=user_email,
            subject=subject,
            text_body=plain,
            html_body=_email_html(plain, site_url),
        )

    return {"push_notified": True, "email": email_result}