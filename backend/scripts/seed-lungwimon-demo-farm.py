"""Seed demo farm: สวนลงุหวิน เมล่อนฟาร์ม (postcode 30220)."""
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
from app.repositories.smart_farm_repository import SmartFarmRepository
from app.services.smart_farm_service import SmartFarmService

LAT = 15.380782592530936
LNG = 101.88227719350695
GOOGLE_MAPS_URL = (
    "https://www.google.com/maps/embed?pb=!1m18!1m12!1m3!1d675.1376282215176!"
    "2d101.88227719350695!3d15.380782592530936!2m3!1f0!2f0!3f0!3m2!1i1024!2i768!4f13.1!"
    "3m3!1m2!1s0x311ed9dfd262adc9%3A0xae492f9dd0fe7f0d!2z4Lia4Li44LiN4Lie4Li04LiH4Lir4Lih4Liy4LmE4LiX4Lii4Lir4Lil4Lix4LiH4Lit4Liy4LiZ!"
    "5e0!3m2!1sen!2sth!4v1782113119877!5m2!1sen!2sth"
)
GATEWAY_IP = "49.49.251.185"
ORG = "สวนลงุหวิน เมล่อนฟาร์ม"
NAME = "โรงเรือนเมล่อนญี่ปุ่น แปลงหลัก"
ADDRESS = "สวนลงุหวิน เมล่อนฟาร์ม ต.ด่านขุนทด อ.ด่านขุนทด จ.นครราชสีมา 30220"

USER_ID = sys.argv[1] if len(sys.argv) > 1 else "6dedd3f7-3a80-47f0-9f89-c003321eab72"
FARM_ID = sys.argv[2] if len(sys.argv) > 2 else None


def _hash(key: str) -> str:
    return hashlib.sha256(key.encode("utf-8")).hexdigest()


async def main() -> None:
    now = datetime.now(timezone.utc)
    gateway_ips = [
        {
            "ip": GATEWAY_IP,
            "label": "IoT Gateway",
            "registered_at": now.isoformat(),
        }
    ]

    async with async_session_maker() as session:
        farm = None
        if FARM_ID:
            result = await session.execute(
                select(SmartFarmORM).where(
                    SmartFarmORM.id == UUID(FARM_ID),
                    SmartFarmORM.user_id == UUID(USER_ID),
                )
            )
            farm = result.scalar_one_or_none()
        if farm is None:
            result = await session.execute(
                select(SmartFarmORM).where(
                    SmartFarmORM.user_id == UUID(USER_ID),
                    SmartFarmORM.organization_name == ORG,
                )
            )
            farm = result.scalar_one_or_none()
        action = "updated"
        if farm is None:
            action = "created"
            farm = SmartFarmORM(
                id=uuid4(),
                user_id=UUID(USER_ID),
                name=NAME,
                organization_name=ORG,
                address=ADDRESS,
                latitude=LAT,
                longitude=LNG,
                google_maps_url=GOOGLE_MAPS_URL,
                gateway_ips=gateway_ips,
                weather_alerts_enabled=True,
                crop_type="japanese_melon",
                timezone="Asia/Bangkok",
                auto_export_enabled=True,
                auto_export_hours=24,
                metadata_json={},
                created_at=now,
                updated_at=now,
            )
            session.add(farm)
        else:
            farm.name = NAME
            farm.address = ADDRESS
            farm.latitude = LAT
            farm.longitude = LNG
            farm.google_maps_url = GOOGLE_MAPS_URL
            farm.gateway_ips = gateway_ips
            farm.weather_alerts_enabled = True
            farm.updated_at = now

        await session.commit()
        await session.refresh(farm)

        devices = await session.execute(select(SmartFarmDeviceORM).where(SmartFarmDeviceORM.farm_id == farm.id))
        device = devices.scalars().first()
        device_key = None
        if device is None:
            device_key = f"sf_{secrets.token_urlsafe(28)}"
            topic = f"obolla/farm/{farm.id}/telemetry"
            device = SmartFarmDeviceORM(
                id=uuid4(),
                farm_id=farm.id,
                device_name="IoT Gateway",
                token_hash=_hash(device_key),
                protocol="http",
                mqtt_topic=topic,
                status="active",
                created_at=now,
            )
            session.add(device)
            await session.commit()

        readings_ingested = 0
        svc = SmartFarmService(SmartFarmRepository(session))
        if device_key:
            seed_key = device_key
        else:
            seed_device, seed_key = await SmartFarmRepository(session).create_device(
                farm_id=farm.id,
                device_name="Demo Seed Sensor",
                protocol="http",
            )
            device = seed_device
            await session.commit()
        sample = {
            "readings": [
                {"channel": "temp_day_c", "value": 28.4, "unit": "celsius"},
                {"channel": "humidity_pct", "value": 67, "unit": "percent"},
                {"channel": "uv_index", "value": 4.1, "unit": "index"},
                {"channel": "light_lux", "value": 18500, "unit": "lux"},
                {"channel": "co2_ppm", "value": 820, "unit": "ppm"},
                {"channel": "soil_moisture_pct", "value": 58, "unit": "percent"},
            ],
            "growth_stage": "fruiting",
            "harvest_cycle_day": 42,
        }
        try:
            result = await svc.ingest_device_payload(device_key=seed_key, payload=sample, source="seed")
            readings_ingested = int(result.get("readings_ingested") or 0)
        except ValueError:
            readings_ingested = 0
        if not device_key:
            device_key = seed_key

        out = {
            "action": action,
            "farm_id": str(farm.id),
            "organization_name": farm.organization_name,
            "name": farm.name,
            "address": farm.address,
            "latitude": farm.latitude,
            "longitude": farm.longitude,
            "google_maps_url": farm.google_maps_url,
            "gateway_ips": farm.gateway_ips,
            "device_id": str(device.id) if device else None,
            "device_key": device_key,
            "readings_ingested": readings_ingested,
            "smart_farm_url": "https://obolla.com/smart-farm",
            "tencent_sg_rule": f"TCP 8883 inbound allow {GATEWAY_IP}/32",
        }
        print(json.dumps(out, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    asyncio.run(main())