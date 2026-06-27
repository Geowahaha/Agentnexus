"""Load smart-farm sensor readings for expert-skill pipelines."""

from __future__ import annotations

import json
import re
from datetime import datetime, timedelta, timezone

from app.core.database import async_session_maker
from app.repositories.smart_farm_repository import SmartFarmRepository
from app.smart_farm.public_urls import dataset_download_url
from app.smart_farm.weather_service import build_weather_alerts, fetch_weather

SMART_FARM_PACKS = frozenset({"quality-check-smart-farm", "japanese-melon-dataset"})
SMART_FARM_SLUGS = frozenset(
    {
        "quality-check-flow-smart-famers",
        "japanese-melon-dataset-pack",
    }
)

_FAKE_MARKETPLACE_URL = re.compile(
    r"https?://marketplace\.obolla\.com[^\s)>\"]*",
    re.I,
)
_OBOLLA_DOWNLOAD_URL = re.compile(
    r"https://(?:www\.)?obolla\.com/api/v1/smart-farm/datasets/[0-9a-f-]{36}/download",
    re.I,
)
_RELATIVE_DATASET_PATH = re.compile(
    r"/api/v1/smart-farm/datasets/([0-9a-f-]{36})/download",
    re.I,
)
_FAKE_DOWNLOAD_URL = re.compile(
    r"https?://(?!(?:www\.)?obolla\.com/api/v1/smart-farm/datasets/)[^\s)>\"]+",
    re.I,
)
_JAPANESE_MELON_DATASET_STEPS = frozenset({"review", "deliver"})

_FARM_ID_RE = re.compile(
    r"(?:farm[_-]?id|smart[_-]?farm[_-]?id)\s*[:=]\s*"
    r"([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})",
    re.I,
)


def parse_farm_id(task_description: str, task_context: dict | None) -> str | None:
    if task_context:
        raw = task_context.get("smart_farm_id") or task_context.get("farm_id")
        if raw:
            return str(raw)
    match = _FARM_ID_RE.search(task_description or "")
    return match.group(1) if match else None


def format_dataset_export_markdown(export_pack: dict) -> str:
    download_url = export_pack.get("download_url") or ""
    record_count = int(export_pack.get("record_count") or 0)
    name = export_pack.get("name") or "dataset-pack"
    fmt = export_pack.get("format") or "json"
    sha256 = export_pack.get("sha256") or ""
    schema_only = bool(export_pack.get("schema_only"))
    lines = [
        "## Dataset pack (auto-exported by OBOLLA)",
        f"- **Download:** [Download {name}]({download_url})",
        f"- **URL (copy):** {download_url}",
        f"- **Rows:** {record_count}",
        f"- **Format:** {fmt}",
    ]
    if sha256:
        lines.append(f"- **SHA-256:** `{sha256}`")
    if schema_only or record_count == 0:
        lines.append(
            "- **Status:** Schema template only — no telemetry readings in the selected window. "
            "Ingest sensors via HTTP/MQTT at /smart-farm, then re-run for a live dataset."
        )
    return "\n".join(lines)


def is_japanese_melon_dataset_pack(*, pack_slug: str, skill_slug: str | None = None) -> bool:
    if pack_slug == "japanese-melon-dataset":
        return True
    return skill_slug == "japanese-melon-dataset-pack"


def resolve_authoritative_download_url(
    step_outputs: dict[str, str],
    smart_farm_meta: dict | None = None,
) -> str | None:
    meta = smart_farm_meta or {}
    pack = meta.get("dataset_pack")
    if isinstance(pack, dict):
        raw = str(pack.get("download_url") or "")
        if raw.startswith("http"):
            return raw
        match = _RELATIVE_DATASET_PATH.search(raw)
        if match:
            return dataset_download_url(match.group(1))
        pack_id = pack.get("id")
        if pack_id:
            return dataset_download_url(str(pack_id))

    export_md = step_outputs.get("dataset_export") or ""
    match = _OBOLLA_DOWNLOAD_URL.search(export_md)
    if match:
        return match.group(0)
    match = _RELATIVE_DATASET_PATH.search(export_md)
    if match:
        return dataset_download_url(match.group(1))

    blob = "\n".join(step_outputs.values())
    match = _OBOLLA_DOWNLOAD_URL.search(blob)
    if match:
        return match.group(0)
    match = _RELATIVE_DATASET_PATH.search(blob)
    return dataset_download_url(match.group(1)) if match else None


def sanitize_smart_farm_download_urls(
    content: str,
    step_outputs: dict[str, str],
    smart_farm_meta: dict | None = None,
) -> str:
    """Replace hallucinated or third-party download URLs with the real OBOLLA export URL."""
    real_url = resolve_authoritative_download_url(step_outputs, smart_farm_meta)
    cleaned = _FAKE_MARKETPLACE_URL.sub(real_url or "https://obolla.com/smart-farm", content)
    if real_url:
        cleaned = re.sub(
            r"(?i)(\*{0,2}Download URL:\*{0,2})\s*https?://\S+",
            rf"\1 [Download dataset pack]({real_url})",
            cleaned,
        )
        cleaned = re.sub(
            r"\[([^\]]*)\]\((https?://(?!(?:www\.)?obolla\.com/api/v1/smart-farm/datasets)[^)]+)\)",
            rf"[\1]({real_url})",
            cleaned,
        )
        if "empty-pack.zip" in cleaned:
            cleaned = cleaned.replace("empty-pack.zip", real_url.split("/")[-2] + ".json")
    return cleaned


def build_japanese_melon_deliverable(
    *,
    step_id: str,
    smart_farm_meta: dict,
    step_outputs: dict[str, str],
) -> str:
    """Deterministic review/deliver markdown — never hallucinates download hosts."""
    export_pack = smart_farm_meta.get("dataset_pack") if isinstance(smart_farm_meta.get("dataset_pack"), dict) else {}
    download_url = resolve_authoritative_download_url(step_outputs, smart_farm_meta)
    record_count = int(export_pack.get("record_count") or 0)
    fmt = export_pack.get("format") or "json"
    sha256 = export_pack.get("sha256") or ""
    schema_only = bool(export_pack.get("schema_only")) or record_count == 0
    farm_id = smart_farm_meta.get("farm_id") or "—"
    farm_name = smart_farm_meta.get("farm_name") or "Smart Farm"
    readings = int(smart_farm_meta.get("readings_count") or 0)
    verdict = "NEEDS_DATA" if schema_only else "READY"

    lines = [
        "# Japanese Melon Greenhouse Dataset Pack",
        "",
        f"**Farm:** {farm_name} (`{farm_id}`)",
        f"**Crop:** japanese-melon",
        f"**Window:** last 48h · **{readings}** readings",
        "",
        "## Dataset pack (official OBOLLA export)",
    ]
    if download_url:
        lines.extend(
            [
                f"- **Download:** [Download dataset pack]({download_url})",
                f"- **URL (copy):** `{download_url}`",
            ]
        )
    else:
        lines.extend(
            [
                "- **Download:** _Export pending — open [Smart Farm](https://obolla.com/smart-farm) and run **Export dataset**._",
                "- **URL:** `https://obolla.com/smart-farm`",
            ]
        )
    lines.extend(
        [
            f"- **Format:** {fmt}",
            f"- **Rows:** {record_count}",
        ]
    )
    if sha256:
        lines.append(f"- **SHA-256:** `{sha256}`")
    if schema_only:
        lines.extend(
            [
                "- **Status:** Schema template only — ingest telemetry via HTTP/MQTT, then re-run for live rows.",
                "",
                "### Connect sensors",
                "1. Open https://obolla.com/smart-farm",
                "2. Copy your device key and POST readings to `https://obolla.com/api/v1/smart-farm/ingest`",
                "3. Re-run this skill to refresh the dataset pack",
            ]
        )
    else:
        lines.extend(
            [
                "",
                "### Import into another system",
                "1. Download the JSON pack (link above while logged in to OBOLLA)",
                "2. Use `manifest` + `readings` arrays for channel mapping",
                "3. Map channels: temp, humidity, EC, pH, soil moisture, UV, light",
            ]
        )
    if step_id == "review":
        lines.extend(
            [
                "",
                "## QA verdict",
                f"**{verdict}** — "
                + (
                    "no telemetry in window; schema template exported for wiring sensors first."
                    if schema_only
                    else "dataset pack exported from live OBOLLA DB readings."
                ),
            ]
        )
    else:
        lines.extend(
            [
                "",
                f"**Verdict:** {verdict}",
                "",
                "_Download link is served only from obolla.com — marketplace.obolla.com is not a valid host._",
            ]
        )
    return "\n".join(lines)


def is_smart_farm_skill(*, pack_slug: str, skill_slug: str | None = None) -> bool:
    if pack_slug in SMART_FARM_PACKS:
        return True
    return bool(skill_slug and skill_slug in SMART_FARM_SLUGS)


async def load_telemetry_markdown(
    *,
    user_id: str,
    task_description: str,
    task_context: dict | None,
    hours: int = 48,
) -> tuple[str, dict]:
    farm_id = parse_farm_id(task_description, task_context)
    since = datetime.now(timezone.utc) - timedelta(hours=hours)

    async with async_session_maker() as session:
        repo = SmartFarmRepository(session)
        if farm_id:
            farm = await repo.get_farm(farm_id, user_id)
            farms = [farm] if farm else []
        else:
            farms = await repo.list_farms(user_id)

        if not farms:
            return (
                "## Smart Farm telemetry\n\n"
                "_No farm linked. Create a farm at /smart-farm or pass `farm_id: <uuid>` in your task._\n",
                {"farm_id": None, "readings_count": 0},
            )

        farm = farms[0]
        rows = await repo.query_readings(str(farm.id), since=since, limit=2000)
        latest = await repo.latest_by_channel(str(farm.id))
        packs = await repo.list_dataset_packs(str(farm.id))

        meta = {
            "farm_id": str(farm.id),
            "farm_name": farm.name,
            "crop_type": farm.crop_type,
            "readings_count": len(rows),
            "dataset_packs": [
                {"id": str(p.id), "name": p.name, "download_url": dataset_download_url(str(p.id))}
                for p in packs[:5]
            ],
        }

        lines = [
            "## Smart Farm telemetry (from OBOLLA DB)",
            f"- Farm: **{farm.name}** (`{farm.id}`)",
        ]
        if farm.organization_name:
            lines.append(f"- Organization: **{farm.organization_name}**")
        if farm.address:
            lines.append(f"- Location: {farm.address}")
        lines.extend(
            [
                f"- Crop: `{farm.crop_type}`",
                f"- Window: last {hours}h · {len(rows)} readings",
                "",
                "### Latest per channel",
            ]
        )

        if farm.latitude is not None and farm.longitude is not None and farm.weather_alerts_enabled:
            try:
                weather = await fetch_weather(farm.latitude, farm.longitude, timezone=farm.timezone)
                alerts = build_weather_alerts(weather)
                cur = weather.get("current") or {}
                lines.extend(
                    [
                        "",
                        "### Weather (Open-Meteo)",
                        f"- Now: {cur.get('temperature_c')}°C · humidity {cur.get('humidity_pct')}% · "
                        f"wind {cur.get('wind_speed_kmh')} km/h",
                    ]
                )
                if alerts:
                    lines.append("")
                    lines.append("### Weather alerts")
                    for alert in alerts[:5]:
                        lines.append(f"- **[{alert['level'].upper()}]** {alert['message']}")
                meta["weather_alerts"] = alerts[:5]
            except Exception:
                pass

        if latest:
            for channel, reading, device in latest:
                val = reading.value_numeric if reading and reading.value_numeric is not None else (
                    reading.value_json if reading else None
                )
                at = reading.recorded_at.isoformat() if reading else "—"
                lines.append(
                    f"- `{channel.channel_key}` ({channel.unit or '—'}) = {val} · {device.device_name} · {at}"
                )
        else:
            lines.append("_No channels yet — ingest via HTTP/MQTT or upload CSV._")

        if rows:
            lines.extend(["", "### Recent readings (sample)", "```json"])
            sample = []
            for reading, channel, device in rows[:40]:
                sample.append(
                    {
                        "at": reading.recorded_at.isoformat(),
                        "channel": channel.channel_key,
                        "unit": channel.unit,
                        "value": reading.value_numeric if reading.value_numeric is not None else reading.value_json,
                        "device": device.device_name,
                        "meta": reading.ingest_meta,
                    }
                )
            lines.append(json.dumps(sample, ensure_ascii=False, indent=2))
            lines.append("```")

        if packs:
            lines.extend(["", "### Dataset packs available for download"])
            for pack in packs[:5]:
                url = dataset_download_url(str(pack.id))
                lines.append(
                    f"- {pack.name} ({pack.format}, {pack.record_count} rows) → "
                    f"[Download]({url}) · `{url}`"
                )

        return "\n".join(lines), meta