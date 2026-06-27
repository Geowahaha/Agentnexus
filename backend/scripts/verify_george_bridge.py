import asyncio
import json
import selectors

import httpx
from sqlalchemy import text

from app.core.config import settings
from app.core.database import async_session_maker

EMAIL = "geowahaha@gmail.com"


async def main() -> None:
    async with async_session_maker() as session:
        user_row = (
            await session.execute(
                text("SELECT id::text FROM users WHERE email = :email"),
                {"email": EMAIL},
            )
        ).first()
        device_row = (
            await session.execute(
                text(
                    """
                    SELECT id::text, device_name, capabilities, last_seen_at
                    FROM bridge_devices
                    WHERE user_id = :user_id
                    ORDER BY created_at DESC
                    LIMIT 1
                    """
                ),
                {"user_id": user_row[0]},
            )
        ).first()

    print(f"device: {device_row[1]} ({device_row[0]})")
    print(f"capabilities: {device_row[2]}")

    base = (settings.notify_worker_url or "").rstrip("/")
    secret = settings.internal_notify_secret
    async with httpx.AsyncClient(timeout=35.0) as client:
        response = await client.post(
            f"{base}/internal/bridge/dispatch",
            json={
                "user_id": user_row[0],
                "device_id": device_row[0],
                "tool": "list_dir",
                "args": {"path": "."},
                "timeout_ms": 30000,
            },
            headers={"X-Bridge-Secret": secret or ""},
        )
        payload = response.json()
        print("invoke:", json.dumps(payload, indent=2)[:800])
        if not payload.get("ok"):
            raise SystemExit("bridge verify failed")
        print(f"verify ok — {len(payload['result']['entries'])} entries")


if __name__ == "__main__":
    asyncio.run(main(), loop_factory=lambda: asyncio.SelectorEventLoop(selectors.SelectSelector()))