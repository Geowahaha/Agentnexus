"""Verify smart-farm download URL resolution blocks marketplace.obolla.com hallucinations."""
from __future__ import annotations

import sys

from app.smart_farm.telemetry_context import (
    build_japanese_melon_deliverable,
    resolve_authoritative_download_url,
    sanitize_smart_farm_download_urls,
)

PACK = {
    "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "download_url": "https://obolla.com/api/v1/smart-farm/datasets/a1b2c3d4-e5f6-7890-abcd-ef1234567890/download",
    "record_count": 0,
    "format": "json",
    "sha256": "abc123",
    "schema_only": True,
}
META = {
    "farm_id": "308da5fd-08a0-415a-807f-62c35793a3d3",
    "farm_name": "สวนลุงหวิน เมล่อนฟาร์ม",
    "readings_count": 0,
    "dataset_pack": PACK,
}
STEPS = {
    "dataset_export": f"Download: {PACK['download_url']}",
    "deliver": (
        "Download URL: https://marketplace.obolla.com/datasets/japanese-melon/empty-pack.zip"
    ),
}


def main() -> None:
    url = resolve_authoritative_download_url(STEPS, META)
    assert url and url.startswith("https://obolla.com/api/v1/smart-farm/datasets/"), url

    cleaned = sanitize_smart_farm_download_urls(STEPS["deliver"], STEPS, META)
    assert "marketplace.obolla.com" not in cleaned, cleaned
    assert PACK["download_url"] in cleaned, cleaned

    deliver = build_japanese_melon_deliverable(step_id="deliver", smart_farm_meta=META, step_outputs=STEPS)
    assert "marketplace.obolla.com" not in deliver, deliver
    assert PACK["download_url"] in deliver, deliver
    assert "NEEDS_DATA" in deliver, deliver

    print("smart_farm_download_urls: ok")


if __name__ == "__main__":
    try:
        main()
    except AssertionError as exc:
        print(f"FAILED: {exc}", file=sys.stderr)
        sys.exit(1)