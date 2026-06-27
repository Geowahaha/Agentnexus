import logging

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)


async def publish_edge_notification(
    user_id: str,
    *,
    event_type: str,
    title: str,
    body: str,
    payload: dict | None = None,
    notification_id: str | None = None,
) -> None:
    base_url = (settings.notify_worker_url or "").rstrip("/")
    secret = settings.internal_notify_secret
    if not base_url or not secret:
        return

    url = f"{base_url}/internal/notifications/publish"
    data = {
        "user_id": user_id,
        "event_type": event_type,
        "title": title,
        "body": body,
        "payload": payload or {},
    }
    if notification_id:
        data["id"] = notification_id

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.post(
                url,
                json=data,
                headers={"X-Notify-Secret": secret},
            )
            if response.status_code >= 400:
                logger.warning("Edge notify failed: %s %s", response.status_code, response.text)
    except Exception as exc:
        logger.warning("Edge notify error: %s", exc)