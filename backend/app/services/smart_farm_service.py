import csv
import io
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from uuid import UUID

from app.db.models.smart_farm import SmartFarmReadingORM
from app.repositories.smart_farm_repository import SmartFarmRepository
from app.core.config import settings
from app.smart_farm.dataset_exporter import (
    dataset_storage_root,
    export_rows_to_file,
    export_schema_template_to_file,
    file_sha256,
)
from app.smart_farm.public_urls import dataset_download_url, normalize_buyer_download_url
from app.smart_farm.mqtt_credentials import register_device_mqtt_auth
from app.smart_farm.ip_utils import gateway_ip_records
from app.smart_farm.schemas import (
    CreateDeviceRequest,
    CreateFarmRequest,
    ExportDatasetRequest,
    IngestPayload,
    UpdateFarmRequest,
)
from app.smart_farm.weather_service import build_weather_alerts, fetch_weather, geocode_address


RESERVED_KEYS = frozenset({"readings", "growth_stage", "harvest_cycle_day", "meta", "at", "timestamp"})


class SmartFarmService:
    def __init__(self, repository: SmartFarmRepository) -> None:
        self._repo = repository

    @staticmethod
    def _parse_recorded_at(raw: Any, default: datetime) -> datetime:
        if raw is None:
            return default
        if isinstance(raw, datetime):
            return raw if raw.tzinfo else raw.replace(tzinfo=timezone.utc)
        text = str(raw).strip()
        if not text:
            return default
        if text.endswith("Z"):
            text = text[:-1] + "+00:00"
        try:
            parsed = datetime.fromisoformat(text)
            return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
        except ValueError:
            return default

    @staticmethod
    def _coerce_numeric(value: Any) -> float | None:
        if value is None or isinstance(value, bool):
            return None
        if isinstance(value, (int, float)):
            return float(value)
        try:
            return float(str(value).strip())
        except ValueError:
            return None

    def _normalize_payload(self, payload: dict[str, Any]) -> tuple[list[dict], dict]:
        now = datetime.now(timezone.utc)
        meta = {
            "growth_stage": payload.get("growth_stage"),
            "harvest_cycle_day": payload.get("harvest_cycle_day"),
            **(payload.get("meta") or {}),
        }
        rows: list[dict] = []

        structured = payload.get("readings")
        if isinstance(structured, list):
            for item in structured:
                if not isinstance(item, dict):
                    continue
                channel = str(item.get("channel") or "").strip()
                if not channel:
                    continue
                rows.append(
                    {
                        "channel": channel,
                        "value": item.get("value"),
                        "unit": str(item.get("unit") or ""),
                        "recorded_at": self._parse_recorded_at(item.get("at"), now),
                    }
                )
            return rows, meta

        for key, value in payload.items():
            if key in RESERVED_KEYS or value is None:
                continue
            rows.append(
                {
                    "channel": str(key),
                    "value": value,
                    "unit": "",
                    "recorded_at": self._parse_recorded_at(payload.get("at") or payload.get("timestamp"), now),
                }
            )
        return rows, meta

    async def ingest_device_payload(
        self,
        *,
        device_key: str,
        payload: dict[str, Any],
        source: str = "http",
    ) -> dict:
        device = await self._repo.get_device_by_key(device_key)
        if device is None:
            await self._repo.log_ingest_event(
                device_id=None,
                source=source,
                payload=payload,
                status="error",
                error_message="Invalid device key",
                readings_count=0,
            )
            raise ValueError("Invalid device key")

        try:
            parsed = IngestPayload.model_validate(payload)
            body = parsed.model_dump(exclude_none=True)
        except Exception:
            body = payload

        return await self._ingest_for_device(device.id, device.farm_id, body, source=source)

    async def ingest_mqtt_payload(self, topic: str, payload: dict[str, Any]) -> dict:
        device = await self._repo.get_device_by_mqtt_topic(topic)
        if device is None:
            await self._repo.log_ingest_event(
                device_id=None,
                source="mqtt",
                payload={"topic": topic, **payload},
                status="error",
                error_message="Unknown MQTT topic",
                readings_count=0,
            )
            raise ValueError(f"Unknown MQTT topic: {topic}")
        return await self._ingest_for_device(device.id, device.farm_id, payload, source="mqtt")

    async def _ingest_for_device(
        self,
        device_id: UUID,
        farm_id: UUID,
        payload: dict[str, Any],
        *,
        source: str,
    ) -> dict:
        rows, meta = self._normalize_payload(payload)
        reading_rows: list[SmartFarmReadingORM] = []
        for spec in rows:
            channel = await self._repo.get_or_create_channel(
                device_id=device_id,
                channel_key=spec["channel"],
                unit=spec.get("unit") or "",
            )
            numeric = self._coerce_numeric(spec.get("value"))
            reading_rows.append(
                SmartFarmReadingORM(
                    channel_id=channel.id,
                    recorded_at=spec["recorded_at"],
                    value_numeric=numeric,
                    value_json=None if numeric is not None else spec.get("value"),
                    source=source,
                    ingest_meta=meta,
                )
            )
        count = await self._repo.insert_readings(reading_rows)
        await self._repo.touch_device(device_id)
        await self._repo.log_ingest_event(
            device_id=device_id,
            source=source,
            payload=payload,
            status="ok",
            error_message=None,
            readings_count=count,
        )
        await self._repo._session.commit()
        return {"ok": True, "readings_ingested": count, "device_id": str(device_id), "farm_id": str(farm_id)}

    async def create_farm(self, user_id: str, request: CreateFarmRequest) -> dict:
        crop_schema = self._load_crop_schema(request.crop_type)
        lat, lng = request.latitude, request.longitude
        address = request.address
        maps_url = request.google_maps_url
        if address and (lat is None or lng is None):
            geo = await geocode_address(address)
            if geo:
                lat = geo["latitude"]
                lng = geo["longitude"]
                maps_url = maps_url or geo.get("google_maps_url")
        gateway_ips = gateway_ip_records([e.model_dump() for e in request.gateway_ips])
        farm = await self._repo.create_farm(
            user_id=user_id,
            name=request.name,
            crop_type=request.crop_type,
            timezone_name=request.timezone,
            auto_export_enabled=request.auto_export_enabled,
            auto_export_hours=request.auto_export_hours,
            metadata={"crop_schema": crop_schema} if crop_schema else {},
            organization_name=request.organization_name,
            address=address,
            latitude=lat,
            longitude=lng,
            google_maps_url=maps_url,
            gateway_ips=gateway_ips,
            weather_alerts_enabled=request.weather_alerts_enabled,
        )
        return self._farm_dict(farm)

    async def update_farm(self, user_id: str, farm_id: str, request: UpdateFarmRequest) -> dict:
        farm = await self._repo.get_farm(farm_id, user_id)
        if farm is None:
            raise ValueError("Farm not found")
        fields: dict = {}
        if request.name is not None:
            fields["name"] = request.name.strip()
        if request.organization_name is not None:
            fields["organization_name"] = request.organization_name.strip() or None
        if request.address is not None:
            fields["address"] = request.address.strip() or None
        if request.google_maps_url is not None:
            fields["google_maps_url"] = request.google_maps_url.strip() or None
        if request.latitude is not None:
            fields["latitude"] = request.latitude
        if request.longitude is not None:
            fields["longitude"] = request.longitude
        if request.weather_alerts_enabled is not None:
            fields["weather_alerts_enabled"] = request.weather_alerts_enabled
        if request.auto_export_enabled is not None:
            fields["auto_export_enabled"] = request.auto_export_enabled
        if request.auto_export_hours is not None:
            fields["auto_export_hours"] = request.auto_export_hours
        if request.gateway_ips is not None:
            fields["gateway_ips"] = gateway_ip_records([e.model_dump() for e in request.gateway_ips])
        addr = fields.get("address", farm.address)
        if addr and request.latitude is None and request.longitude is None and not farm.latitude:
            geo = await geocode_address(addr)
            if geo:
                fields["latitude"] = geo["latitude"]
                fields["longitude"] = geo["longitude"]
                if not fields.get("google_maps_url") and not farm.google_maps_url:
                    fields["google_maps_url"] = geo.get("google_maps_url")
        updated = await self._repo.update_farm(farm, **fields)
        return self._farm_dict(updated)

    async def get_farm_weather(self, user_id: str, farm_id: str) -> dict:
        farm = await self._repo.get_farm(farm_id, user_id)
        if farm is None:
            raise ValueError("Farm not found")
        if farm.latitude is None or farm.longitude is None:
            raise ValueError("Farm location not set — register address or coordinates first")
        weather = await fetch_weather(farm.latitude, farm.longitude, timezone=farm.timezone)
        alerts = build_weather_alerts(weather) if farm.weather_alerts_enabled else []
        return {"farm_id": str(farm.id), "weather": weather, "alerts": alerts}

    async def mqtt_whitelist_manifest(self) -> dict:
        ips = await self._repo.list_all_gateway_ips()
        return {
            "vps_host": settings.smart_farm_mqtt_public_host,
            "mqtt_tls_port": settings.smart_farm_mqtt_tls_port,
            "tencent_sg_note": "Add inbound TCP 8883 for each gateway IP below (not 0.0.0.0/0)",
            "gateway_ips": ips,
            "unique_ips": sorted({row["ip"] for row in ips}),
        }

    async def list_farms(self, user_id: str) -> list[dict]:
        farms = await self._repo.list_farms(user_id)
        return [self._farm_dict(f) for f in farms]

    async def get_farm_detail(self, user_id: str, farm_id: str) -> dict | None:
        farm = await self._repo.get_farm(farm_id, user_id)
        if farm is None:
            return None
        devices = await self._repo.list_devices(farm_id)
        packs = await self._repo.list_dataset_packs(farm_id)
        return {
            **self._farm_dict(farm),
            "devices": [self._device_dict(d) for d in devices],
            "datasets": [self._pack_dict(p) for p in packs],
        }

    async def create_device(self, user_id: str, farm_id: str, request: CreateDeviceRequest) -> dict:
        farm = await self._repo.get_farm(farm_id, user_id)
        if farm is None:
            raise ValueError("Farm not found")
        device, device_key = await self._repo.create_device(
            farm_id=farm_id,
            device_name=request.device_name,
            protocol=request.protocol,
        )
        mqtt_auth = register_device_mqtt_auth(
            device_id=device.id,
            farm_id=device.farm_id,
            device_key=device_key,
        )
        return {
            **self._device_dict(device),
            "device_key": device_key,
            "connect": self.build_connect_kit(
                farm_id=str(farm.id),
                device_key=device_key,
                device=device,
                mqtt_auth=mqtt_auth,
            ),
        }

    def build_connect_kit(
        self,
        *,
        farm_id: str,
        device_key: str,
        device,
        mqtt_auth: dict[str, str] | None = None,
    ) -> dict:
        public_base = "https://obolla.com/api/v1/smart-farm"
        mqtt_host = settings.smart_farm_mqtt_public_host
        mqtt_tls_port = settings.smart_farm_mqtt_tls_port
        topic = (mqtt_auth or {}).get("mqtt_topic") or device.mqtt_topic or f"obolla/farm/{farm_id}/telemetry"
        mqtt_user = (mqtt_auth or {}).get("mqtt_username") or str(device.id)
        mqtt_pass = (mqtt_auth or {}).get("mqtt_password") or device_key
        return {
            "recommended_transport": "https",
            "http_ingest_url": f"{public_base}/ingest",
            "http_headers": {"X-Device-Key": device_key, "Content-Type": "application/json"},
            "http_note": (
                "Recommended — HTTPS via obolla.com (port 443). "
                "Works through Cloudflare edge; no Tencent Security Group change required."
            ),
            "mqtt_topic": topic,
            "mqtt_broker": f"mqtts://{mqtt_host}:{mqtt_tls_port}",
            "mqtt_username": mqtt_user,
            "mqtt_password_hint": "same as device key (shown once at create)",
            "mqtt_tls": True,
            "mqtt_broker_hint": f"mqtts://{mqtt_host}:{mqtt_tls_port} — TLS + per-device auth",
            "mqtt_note": (
                "Advanced — requires Tencent Security Group inbound TCP 8883 to the VPS. "
                "If port 8883 is blocked, use HTTP ingest instead."
            ),
            "sample_payload": {
                "readings": [
                    {"channel": "temp_day_c", "value": 28.5, "unit": "celsius"},
                    {"channel": "humidity_pct", "value": 65, "unit": "percent"},
                    {"channel": "uv_index", "value": 4.2},
                ],
                "growth_stage": "fruiting",
                "harvest_cycle_day": 42,
            },
            "curl_example": (
                f'curl -X POST "{public_base}/ingest" '
                f'-H "X-Device-Key: {device_key}" -H "Content-Type: application/json" '
                f'-d \'{{"temp_day_c":28.5,"humidity_pct":65,"uv_index":4.2}}\''
            ),
        }

    async def latest_snapshot(self, user_id: str, farm_id: str) -> dict | None:
        farm = await self._repo.get_farm(farm_id, user_id)
        if farm is None:
            return None
        latest = await self._repo.latest_by_channel(farm_id)
        return {
            "farm_id": farm_id,
            "channels": [
                {
                    "channel": channel.channel_key,
                    "unit": channel.unit,
                    "device_name": device.device_name,
                    "value": reading.value_numeric if reading and reading.value_numeric is not None else (reading.value_json if reading else None),
                    "recorded_at": reading.recorded_at.isoformat() if reading else None,
                }
                for channel, reading, device in latest
            ],
        }

    async def export_dataset(
        self,
        user_id: str,
        farm_id: str,
        request: ExportDatasetRequest,
        *,
        auto_generated: bool = False,
    ) -> dict:
        farm = await self._repo.get_farm(farm_id, user_id if not auto_generated else None)
        if farm is None:
            raise ValueError("Farm not found")
        since = datetime.now(timezone.utc) - timedelta(hours=request.hours)
        rows = await self._repo.query_readings(farm_id, since=since, limit=50000)
        if not rows:
            raise ValueError("No readings in selected window")

        pack = await self._repo.create_dataset_pack(
            farm_id=farm_id,
            name=request.name or f"export-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M')}",
            fmt=request.format,
            file_path="",
            record_count=0,
            window_start=None,
            window_end=None,
            auto_generated=auto_generated,
        )
        file_path, count, window_start, window_end = export_rows_to_file(
            farm_id=farm_id,
            pack_id=str(pack.id),
            fmt=request.format,
            rows=rows,
        )
        pack.file_path = file_path
        pack.record_count = count
        pack.window_start = window_start
        pack.window_end = window_end
        await self._repo._session.commit()
        await self._repo._session.refresh(pack)
        pack_dict = self._pack_dict(pack)
        pack_dict["sha256"] = file_sha256(Path(file_path))
        return pack_dict

    async def export_schema_template(
        self,
        user_id: str,
        farm_id: str,
        *,
        name: str = "schema-template",
        auto_generated: bool = False,
    ) -> dict:
        farm = await self._repo.get_farm(farm_id, user_id if not auto_generated else None)
        if farm is None:
            raise ValueError("Farm not found")
        crop_schema = self._load_crop_schema(farm.crop_type) or {}
        pack = await self._repo.create_dataset_pack(
            farm_id=farm_id,
            name=name,
            fmt="json",
            file_path="",
            record_count=0,
            window_start=None,
            window_end=None,
            auto_generated=auto_generated,
        )
        file_path, count, sha256 = export_schema_template_to_file(
            farm_id=farm_id,
            pack_id=str(pack.id),
            crop_schema=crop_schema,
            farm_name=farm.name,
            crop_type=farm.crop_type,
        )
        pack.file_path = file_path
        pack.record_count = count
        await self._repo._session.commit()
        await self._repo._session.refresh(pack)
        pack_dict = self._pack_dict(pack)
        pack_dict["sha256"] = sha256
        pack_dict["schema_only"] = True
        return pack_dict

    async def import_file(self, user_id: str, farm_id: str, filename: str, content: bytes) -> dict:
        farm = await self._repo.get_farm(farm_id, user_id)
        if farm is None:
            raise ValueError("Farm not found")
        devices = await self._repo.list_devices(farm_id)
        if not devices:
            device_resp = await self.create_device(
                user_id,
                farm_id,
                CreateDeviceRequest(device_name="CSV Import", protocol="csv"),
            )
            device_key = device_resp["device_key"]
        else:
            device, device_key = await self._repo.create_device(
                farm_id=farm_id,
                device_name=f"Import {datetime.now(timezone.utc).strftime('%H%M')}",
                protocol="csv",
            )

        lower = filename.lower()
        if lower.endswith(".json"):
            payload = json.loads(content.decode("utf-8"))
            if isinstance(payload, list):
                total = 0
                for item in payload:
                    if isinstance(item, dict):
                        result = await self.ingest_device_payload(device_key=device_key, payload=item, source="upload")
                        total += int(result["readings_ingested"])
                return {"ok": True, "readings_ingested": total}
            if isinstance(payload, dict):
                return await self.ingest_device_payload(device_key=device_key, payload=payload, source="upload")
            raise ValueError("Invalid JSON payload")

        text = content.decode("utf-8-sig")
        reader = csv.DictReader(io.StringIO(text))
        total = 0
        for row in reader:
            channel = (row.get("channel") or row.get("sensor") or "").strip()
            value = row.get("value")
            if not channel or value in (None, ""):
                continue
            payload = {
                "readings": [
                    {
                        "channel": channel,
                        "value": value,
                        "unit": row.get("unit") or "",
                        "at": row.get("recorded_at") or row.get("timestamp"),
                    }
                ]
            }
            result = await self.ingest_device_payload(device_key=device_key, payload=payload, source="upload")
            total += int(result["readings_ingested"])
        return {"ok": True, "readings_ingested": total}

    async def get_dataset_download(self, user_id: str, pack_id: str) -> tuple[Path, str] | None:
        pack = await self._repo.get_dataset_pack(pack_id, user_id)
        if pack is None:
            return None
        path = Path(pack.file_path)
        if not path.is_file():
            return None
        media = "application/json" if pack.format == "json" else "text/csv"
        return path, media

    async def run_auto_exports(self) -> int:
        farms = await self._repo.farms_due_auto_export()
        exported = 0
        for farm in farms:
            last = await self._repo.last_auto_export_at(str(farm.id))
            due_hours = farm.auto_export_hours
            if last and last > datetime.now(timezone.utc) - timedelta(hours=due_hours):
                continue
            since = datetime.now(timezone.utc) - timedelta(hours=due_hours)
            if await self._repo.count_readings_since(str(farm.id), since) == 0:
                continue
            try:
                await self.export_dataset(
                    str(farm.user_id),
                    str(farm.id),
                    ExportDatasetRequest(
                        name=f"auto-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M')}",
                        format="json",
                        hours=due_hours,
                    ),
                    auto_generated=True,
                )
                exported += 1
            except ValueError:
                continue
        return exported

    def _load_crop_schema(self, crop_type: str) -> dict | None:
        schema_path = Path(__file__).resolve().parents[1] / "smart_farm" / "crop_schemas" / f"{crop_type}.json"
        if not schema_path.is_file():
            schema_path = Path(__file__).resolve().parents[1] / "smart_farm" / "crop_schemas" / "japanese_melon.json"
        if schema_path.is_file():
            return json.loads(schema_path.read_text(encoding="utf-8"))
        return None

    @staticmethod
    def _farm_dict(farm) -> dict:
        lat, lng = farm.latitude, farm.longitude
        maps_url = farm.google_maps_url
        if not maps_url and lat is not None and lng is not None:
            maps_url = f"https://www.google.com/maps/search/?api=1&query={lat},{lng}"
        return {
            "id": str(farm.id),
            "name": farm.name,
            "organization_name": farm.organization_name,
            "address": farm.address,
            "latitude": lat,
            "longitude": lng,
            "google_maps_url": maps_url,
            "gateway_ips": farm.gateway_ips or [],
            "weather_alerts_enabled": farm.weather_alerts_enabled,
            "crop_type": farm.crop_type,
            "timezone": farm.timezone,
            "auto_export_enabled": farm.auto_export_enabled,
            "auto_export_hours": farm.auto_export_hours,
            "metadata": farm.metadata_json,
            "created_at": farm.created_at.isoformat(),
            "updated_at": farm.updated_at.isoformat() if farm.updated_at else None,
            "mqtt_whitelist_hint": (
                "Register gateway public IP — add to Tencent Security Group inbound TCP 8883 "
                "for MQTT TLS (or use HTTPS ingest via obolla.com)."
            ),
        }

    @staticmethod
    def _device_dict(device) -> dict:
        return {
            "id": str(device.id),
            "device_name": device.device_name,
            "protocol": device.protocol,
            "mqtt_topic": device.mqtt_topic,
            "status": device.status,
            "last_seen_at": device.last_seen_at.isoformat() if device.last_seen_at else None,
            "created_at": device.created_at.isoformat(),
        }

    @staticmethod
    def _pack_dict(pack) -> dict:
        return {
            "id": str(pack.id),
            "farm_id": str(pack.farm_id),
            "name": pack.name,
            "format": pack.format,
            "record_count": pack.record_count,
            "window_start": pack.window_start.isoformat() if pack.window_start else None,
            "window_end": pack.window_end.isoformat() if pack.window_end else None,
            "status": pack.status,
            "auto_generated": pack.auto_generated,
            "download_url": normalize_buyer_download_url(dataset_download_url(str(pack.id))),
            "created_at": pack.created_at.isoformat(),
        }