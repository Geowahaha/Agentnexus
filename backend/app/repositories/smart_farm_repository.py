import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from uuid import UUID, uuid4

from sqlalchemy import desc, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.smart_farm import (
    SmartFarmChannelORM,
    SmartFarmDatasetPackORM,
    SmartFarmDeviceORM,
    SmartFarmIngestEventORM,
    SmartFarmORM,
    SmartFarmReadingORM,
)


def hash_device_key(key: str) -> str:
    return hashlib.sha256(key.encode("utf-8")).hexdigest()


def generate_device_key() -> str:
    return f"sf_{secrets.token_urlsafe(28)}"


class SmartFarmRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create_farm(
        self,
        *,
        user_id: str,
        name: str,
        crop_type: str,
        timezone_name: str,
        auto_export_enabled: bool,
        auto_export_hours: int,
        metadata: dict | None = None,
        organization_name: str | None = None,
        address: str | None = None,
        latitude: float | None = None,
        longitude: float | None = None,
        google_maps_url: str | None = None,
        gateway_ips: list | None = None,
        weather_alerts_enabled: bool = True,
    ) -> SmartFarmORM:
        now = datetime.now(timezone.utc)
        farm = SmartFarmORM(
            id=uuid4(),
            user_id=UUID(user_id),
            name=name.strip(),
            crop_type=crop_type.strip(),
            timezone=timezone_name.strip(),
            auto_export_enabled=auto_export_enabled,
            auto_export_hours=auto_export_hours,
            organization_name=(organization_name or "").strip() or None,
            address=(address or "").strip() or None,
            latitude=latitude,
            longitude=longitude,
            google_maps_url=(google_maps_url or "").strip() or None,
            gateway_ips=gateway_ips or [],
            weather_alerts_enabled=weather_alerts_enabled,
            metadata_json=metadata or {},
            created_at=now,
            updated_at=now,
        )
        self._session.add(farm)
        await self._session.commit()
        await self._session.refresh(farm)
        return farm

    async def list_farms(self, user_id: str) -> list[SmartFarmORM]:
        result = await self._session.execute(
            select(SmartFarmORM)
            .where(SmartFarmORM.user_id == UUID(user_id))
            .order_by(desc(SmartFarmORM.created_at))
        )
        return list(result.scalars().all())

    async def get_farm(self, farm_id: str, user_id: str | None = None) -> SmartFarmORM | None:
        query = select(SmartFarmORM).where(SmartFarmORM.id == UUID(farm_id))
        if user_id:
            query = query.where(SmartFarmORM.user_id == UUID(user_id))
        result = await self._session.execute(query)
        return result.scalar_one_or_none()

    async def update_farm(self, farm: SmartFarmORM, **fields) -> SmartFarmORM:
        for key, value in fields.items():
            if value is not None or key in ("organization_name", "address", "google_maps_url"):
                setattr(farm, key, value)
        farm.updated_at = datetime.now(timezone.utc)
        await self._session.commit()
        await self._session.refresh(farm)
        return farm

    async def list_all_gateway_ips(self) -> list[dict]:
        result = await self._session.execute(select(SmartFarmORM))
        farms = list(result.scalars().all())
        merged: dict[str, dict] = {}
        for farm in farms:
            for entry in farm.gateway_ips or []:
                if not isinstance(entry, dict):
                    continue
                ip = str(entry.get("ip") or "").strip()
                if not ip:
                    continue
                merged[ip] = {
                    "ip": ip,
                    "label": entry.get("label"),
                    "farm_id": str(farm.id),
                    "farm_name": farm.name,
                    "organization_name": farm.organization_name,
                }
        return list(merged.values())

    async def create_device(
        self,
        *,
        farm_id: str,
        device_name: str,
        protocol: str,
    ) -> tuple[SmartFarmDeviceORM, str]:
        device_key = generate_device_key()
        topic = f"obolla/farm/{farm_id}/telemetry"
        now = datetime.now(timezone.utc)
        device = SmartFarmDeviceORM(
            id=uuid4(),
            farm_id=UUID(farm_id),
            device_name=device_name.strip(),
            token_hash=hash_device_key(device_key),
            protocol=protocol,
            mqtt_topic=topic,
            status="active",
            created_at=now,
        )
        self._session.add(device)
        await self._session.commit()
        await self._session.refresh(device)
        return device, device_key

    async def list_devices(self, farm_id: str) -> list[SmartFarmDeviceORM]:
        result = await self._session.execute(
            select(SmartFarmDeviceORM)
            .where(
                SmartFarmDeviceORM.farm_id == UUID(farm_id),
                SmartFarmDeviceORM.revoked_at.is_(None),
            )
            .order_by(desc(SmartFarmDeviceORM.created_at))
        )
        return list(result.scalars().all())

    async def get_device_by_key(self, device_key: str) -> SmartFarmDeviceORM | None:
        result = await self._session.execute(
            select(SmartFarmDeviceORM).where(
                SmartFarmDeviceORM.token_hash == hash_device_key(device_key),
                SmartFarmDeviceORM.revoked_at.is_(None),
                SmartFarmDeviceORM.status == "active",
            )
        )
        return result.scalar_one_or_none()

    async def get_device_by_mqtt_topic(self, topic: str) -> SmartFarmDeviceORM | None:
        result = await self._session.execute(
            select(SmartFarmDeviceORM).where(
                SmartFarmDeviceORM.mqtt_topic == topic,
                SmartFarmDeviceORM.revoked_at.is_(None),
                SmartFarmDeviceORM.status == "active",
            )
        )
        return result.scalar_one_or_none()

    async def touch_device(self, device_id: UUID) -> None:
        await self._session.execute(
            update(SmartFarmDeviceORM)
            .where(SmartFarmDeviceORM.id == device_id)
            .values(last_seen_at=datetime.now(timezone.utc))
        )
        await self._session.commit()

    async def get_or_create_channel(
        self,
        *,
        device_id: UUID,
        channel_key: str,
        unit: str = "",
    ) -> SmartFarmChannelORM:
        result = await self._session.execute(
            select(SmartFarmChannelORM).where(
                SmartFarmChannelORM.device_id == device_id,
                SmartFarmChannelORM.channel_key == channel_key,
            )
        )
        existing = result.scalar_one_or_none()
        if existing:
            return existing
        channel = SmartFarmChannelORM(
            id=uuid4(),
            device_id=device_id,
            channel_key=channel_key,
            label=channel_key.replace("_", " ").title(),
            unit=unit,
            created_at=datetime.now(timezone.utc),
        )
        self._session.add(channel)
        await self._session.flush()
        return channel

    async def insert_readings(
        self,
        rows: list[SmartFarmReadingORM],
    ) -> int:
        if not rows:
            return 0
        self._session.add_all(rows)
        await self._session.flush()
        return len(rows)

    async def log_ingest_event(
        self,
        *,
        device_id: UUID | None,
        source: str,
        payload: dict,
        status: str,
        error_message: str | None,
        readings_count: int,
    ) -> None:
        self._session.add(
            SmartFarmIngestEventORM(
                device_id=device_id,
                source=source,
                payload=payload,
                status=status,
                error_message=error_message,
                readings_count=readings_count,
                created_at=datetime.now(timezone.utc),
            )
        )
        await self._session.commit()

    async def query_readings(
        self,
        farm_id: str,
        *,
        since: datetime | None = None,
        until: datetime | None = None,
        limit: int = 500,
    ) -> list[tuple[SmartFarmReadingORM, SmartFarmChannelORM, SmartFarmDeviceORM]]:
        query = (
            select(SmartFarmReadingORM, SmartFarmChannelORM, SmartFarmDeviceORM)
            .join(SmartFarmChannelORM, SmartFarmReadingORM.channel_id == SmartFarmChannelORM.id)
            .join(SmartFarmDeviceORM, SmartFarmChannelORM.device_id == SmartFarmDeviceORM.id)
            .where(SmartFarmDeviceORM.farm_id == UUID(farm_id))
            .order_by(desc(SmartFarmReadingORM.recorded_at))
            .limit(limit)
        )
        if since:
            query = query.where(SmartFarmReadingORM.recorded_at >= since)
        if until:
            query = query.where(SmartFarmReadingORM.recorded_at <= until)
        result = await self._session.execute(query)
        return list(result.all())

    async def latest_by_channel(self, farm_id: str) -> list[tuple[SmartFarmChannelORM, SmartFarmReadingORM | None, SmartFarmDeviceORM]]:
        devices = await self.list_devices(farm_id)
        out: list[tuple[SmartFarmChannelORM, SmartFarmReadingORM | None, SmartFarmDeviceORM]] = []
        for device in devices:
            channels_result = await self._session.execute(
                select(SmartFarmChannelORM).where(SmartFarmChannelORM.device_id == device.id)
            )
            channels = list(channels_result.scalars().all())
            for channel in channels:
                reading_result = await self._session.execute(
                    select(SmartFarmReadingORM)
                    .where(SmartFarmReadingORM.channel_id == channel.id)
                    .order_by(desc(SmartFarmReadingORM.recorded_at))
                    .limit(1)
                )
                out.append((channel, reading_result.scalar_one_or_none(), device))
        return out

    async def create_dataset_pack(
        self,
        *,
        farm_id: str,
        name: str,
        fmt: str,
        file_path: str,
        record_count: int,
        window_start: datetime | None,
        window_end: datetime | None,
        auto_generated: bool,
    ) -> SmartFarmDatasetPackORM:
        pack = SmartFarmDatasetPackORM(
            id=uuid4(),
            farm_id=UUID(farm_id),
            name=name,
            format=fmt,
            file_path=file_path,
            record_count=record_count,
            window_start=window_start,
            window_end=window_end,
            status="ready",
            auto_generated=auto_generated,
            created_at=datetime.now(timezone.utc),
        )
        self._session.add(pack)
        await self._session.commit()
        await self._session.refresh(pack)
        return pack

    async def list_dataset_packs(self, farm_id: str) -> list[SmartFarmDatasetPackORM]:
        result = await self._session.execute(
            select(SmartFarmDatasetPackORM)
            .where(SmartFarmDatasetPackORM.farm_id == UUID(farm_id))
            .order_by(desc(SmartFarmDatasetPackORM.created_at))
        )
        return list(result.scalars().all())

    async def get_dataset_pack(self, pack_id: str, user_id: str | None = None) -> SmartFarmDatasetPackORM | None:
        if user_id:
            result = await self._session.execute(
                select(SmartFarmDatasetPackORM)
                .join(SmartFarmORM, SmartFarmDatasetPackORM.farm_id == SmartFarmORM.id)
                .where(
                    SmartFarmDatasetPackORM.id == UUID(pack_id),
                    SmartFarmORM.user_id == UUID(user_id),
                )
            )
            return result.scalar_one_or_none()
        result = await self._session.execute(
            select(SmartFarmDatasetPackORM).where(SmartFarmDatasetPackORM.id == UUID(pack_id))
        )
        return result.scalar_one_or_none()

    async def farms_due_auto_export(self) -> list[SmartFarmORM]:
        result = await self._session.execute(
            select(SmartFarmORM).where(SmartFarmORM.auto_export_enabled.is_(True))
        )
        return list(result.scalars().all())

    async def count_readings_since(self, farm_id: str, since: datetime) -> int:
        result = await self._session.execute(
            select(func.count())
            .select_from(SmartFarmReadingORM)
            .join(SmartFarmChannelORM, SmartFarmReadingORM.channel_id == SmartFarmChannelORM.id)
            .join(SmartFarmDeviceORM, SmartFarmChannelORM.device_id == SmartFarmDeviceORM.id)
            .where(
                SmartFarmDeviceORM.farm_id == UUID(farm_id),
                SmartFarmReadingORM.recorded_at >= since,
            )
        )
        return int(result.scalar_one())

    async def last_auto_export_at(self, farm_id: str) -> datetime | None:
        result = await self._session.execute(
            select(SmartFarmDatasetPackORM.created_at)
            .where(
                SmartFarmDatasetPackORM.farm_id == UUID(farm_id),
                SmartFarmDatasetPackORM.auto_generated.is_(True),
            )
            .order_by(desc(SmartFarmDatasetPackORM.created_at))
            .limit(1)
        )
        return result.scalar_one_or_none()