from __future__ import annotations

import logging

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)


async def send_transactional_email(
    *,
    to_email: str,
    subject: str,
    text_body: str,
    html_body: str | None = None,
) -> dict[str, str]:
    """Send email via Resend when configured; otherwise no-op with reason."""
    api_key = (settings.resend_api_key or "").strip()
    from_email = (settings.obolla_from_email or "OBOLLA Agent-Ready <noreply@obolla.com>").strip()
    if not api_key:
        return {"sent": "false", "reason": "RESEND_API_KEY not configured"}

    payload: dict = {
        "from": from_email,
        "to": [to_email],
        "subject": subject[:500],
        "text": text_body[:12000],
    }
    if html_body:
        payload["html"] = html_body[:24000]

    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            res = await client.post(
                "https://api.resend.com/emails",
                headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                json=payload,
            )
            if res.status_code >= 400:
                logger.warning("Resend email failed: %s %s", res.status_code, res.text[:300])
                return {"sent": "false", "reason": f"resend HTTP {res.status_code}"}
            data = res.json()
            return {"sent": "true", "provider": "resend", "id": str(data.get("id") or "")}
    except Exception as exc:  # noqa: BLE001
        logger.warning("send_transactional_email error: %s", exc)
        return {"sent": "false", "reason": str(exc)[:200]}