"""One-shot seed for live Smart Farm smoke test (run inside API container)."""
from __future__ import annotations

import asyncio
import hashlib
import json
import secrets
import sys
from datetime import datetime, timezone
from uuid import UUID, uuid4

from sqlalchemy import select

from app.core.database import async_session_maker
from app.db.models.smart_farm import SmartFarmDeviceORM, SmartFarmORM
from app.smart_farm.mqtt_credentials import register_device_mqtt_auth


def _hash(key: str) -> str:
    return hashlib.sha256(key.encode("utf-8")).hexdigest()


async def main() -> None:
    user_id = sys.argv[1] if len(sys.argv) > 1 else "6dedd3f7-3a80-47f0-9f89-c003321eab72"
    async with async_session_maker() as session:
        result = await session.execute(
            select(SmartFarmORM).where(
                SmartFarmORM.user_id == UUID(user_id),
                SmartFarmORM.crop_type == "japanese_melon",
            )
        )
        farm = result.scalar_one_or_none()
        now = datetime.now(timezone.utc)
        if farm is None:
            farm = SmartFarmORM(
                id=uuid4(),
                user_id=UUID(user_id),
                name="Live Test Melon House",
                crop_type="japanese_melon",
                timezone="Asia/Bangkok",
                auto_export_enabled=True,
                auto_export_hours=24,
                metadata_json={},
                created_at=now,
                updated_at=now,
            )
            session.add(farm)
            await session.commit()
            await session.refresh(farm)

        devices = await session.execute(select(SmartFarmDeviceORM).where(SmartFarmDeviceORM.farm_id == farm.id))
        existing = devices.scalars().first()
        if existing:
            print(json.dumps({"farm_id": str(farm.id), "device_id": str(existing.id), "note": "device exists — key not recoverable"}))
            return

        device_key = f"sf_{secrets.token_urlsafe(28)}"
        topic = f"obolla/farm/{farm.id}/telemetry"
        device = SmartFarmDeviceORM(
            id=uuid4(),
            farm_id=farm.id,
            device_name="live-test-sensor",
            token_hash=_hash(device_key),
            protocol="mqtt",
            mqtt_topic=topic,
            status="active",
            created_at=now,
        )
        session.add(device)
        await session.commit()
        mqtt_auth = register_device_mqtt_auth(device_id=device.id, farm_id=farm.id, device_key=device_key)
        print(
            json.dumps(
                {
                    "farm_id": str(farm.id),
                    "device_id": str(device.id),
                    "device_key": device_key,
                    "mqtt_topic": topic,
                    "mqtt_username": mqtt_auth["mqtt_username"],
                    "mqtt_password": device_key,
                    "mqtt_url": "mqtts://43.128.75.149:8883",
                }
            )
        )


if __name__ == "__main__":
    asyncio.run(main())