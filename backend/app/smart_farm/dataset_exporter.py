import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

from app.db.models.smart_farm import SmartFarmChannelORM, SmartFarmDeviceORM, SmartFarmReadingORM


def dataset_storage_root() -> Path:
    root = Path(__file__).resolve().parents[2] / "data" / "smart_farm_datasets"
    root.mkdir(parents=True, exist_ok=True)
    return root


def export_rows_to_file(
    *,
    farm_id: str,
    pack_id: str,
    fmt: str,
    rows: list[tuple[SmartFarmReadingORM, SmartFarmChannelORM, SmartFarmDeviceORM]],
) -> tuple[str, int, datetime | None, datetime | None]:
    farm_dir = dataset_storage_root() / farm_id
    farm_dir.mkdir(parents=True, exist_ok=True)
    ext = "json" if fmt == "json" else "csv"
    file_path = farm_dir / f"{pack_id}.{ext}"

    export_rows: list[dict] = []
    window_start: datetime | None = None
    window_end: datetime | None = None

    for reading, channel, device in rows:
        window_start = reading.recorded_at if window_start is None else min(window_start, reading.recorded_at)
        window_end = reading.recorded_at if window_end is None else max(window_end, reading.recorded_at)
        export_rows.append(
            {
                "recorded_at": reading.recorded_at.astimezone(timezone.utc).isoformat(),
                "device_id": str(device.id),
                "device_name": device.device_name,
                "channel": channel.channel_key,
                "unit": channel.unit,
                "value": reading.value_numeric if reading.value_numeric is not None else reading.value_json,
                "source": reading.source,
                "meta": reading.ingest_meta,
            }
        )

    if fmt == "json":
        file_path.write_text(json.dumps(export_rows, ensure_ascii=False, indent=2), encoding="utf-8")
    else:
        with file_path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(
                handle,
                fieldnames=["recorded_at", "device_name", "channel", "unit", "value", "source"],
            )
            writer.writeheader()
            for row in export_rows:
                writer.writerow(
                    {
                        "recorded_at": row["recorded_at"],
                        "device_name": row["device_name"],
                        "channel": row["channel"],
                        "unit": row["unit"],
                        "value": row["value"],
                        "source": row["source"],
                    }
                )

    return str(file_path), len(export_rows), window_start, window_end


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def export_schema_template_to_file(
    *,
    farm_id: str,
    pack_id: str,
    crop_schema: dict,
    farm_name: str,
    crop_type: str,
) -> tuple[str, int, str]:
    """Write schema-only pack (manifest JSON + empty CSV headers) when no readings exist."""
    farm_dir = dataset_storage_root() / farm_id
    farm_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = farm_dir / f"{pack_id}-manifest.json"
    csv_path = farm_dir / f"{pack_id}.csv"

    channels = crop_schema.get("channels") or []
    manifest = {
        "farm_id": farm_id,
        "farm_name": farm_name,
        "crop": crop_type,
        "schema": crop_schema,
        "record_count": 0,
        "note": "Schema template only — ingest telemetry via HTTP/MQTT then re-export for live data.",
    }
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

    headers = ["recorded_at", "device_name", "channel", "unit", "value", "source"]
    with csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=headers)
        writer.writeheader()
        for channel in channels:
            writer.writerow(
                {
                    "recorded_at": "",
                    "device_name": "",
                    "channel": channel.get("key", ""),
                    "unit": channel.get("unit", ""),
                    "value": "",
                    "source": "template",
                }
            )

    bundle_path = farm_dir / f"{pack_id}.json"
    bundle = {
        "manifest": manifest,
        "schema_channels": channels,
        "readings": [],
        "files": {
            "manifest": manifest_path.name,
            "csv_template": csv_path.name,
        },
    }
    bundle_path.write_text(json.dumps(bundle, ensure_ascii=False, indent=2), encoding="utf-8")
    return str(bundle_path), 0, file_sha256(bundle_path)