"""Sync per-device MQTT credentials to shared passwd + ACL files."""

from __future__ import annotations

import logging
import subprocess
from pathlib import Path
from uuid import UUID

logger = logging.getLogger(__name__)

PASSWD_PATH = Path("/app/data/mosquitto/passwd")
ACL_PATH = Path("/app/data/mosquitto/acl")
INGEST_USERNAME = "obolla-ingest"
INGEST_TOPIC_READ = "obolla/farm/+/telemetry"


def _ensure_dirs() -> None:
    PASSWD_PATH.parent.mkdir(parents=True, exist_ok=True)


def _write_passwd(username: str, password: str) -> None:
    try:
        subprocess.run(
            ["/usr/bin/mosquitto_passwd", "-b", str(PASSWD_PATH), username, password],
            check=True,
            capture_output=True,
            text=True,
        )
    except FileNotFoundError as exc:
        raise RuntimeError("mosquitto_passwd is required for MQTT device auth") from exc
    PASSWD_PATH.chmod(0o600)


def _upsert_acl(username: str, lines: list[str]) -> None:
    acl_lines: list[str] = []
    if ACL_PATH.is_file():
        acl_lines = [
            line
            for line in ACL_PATH.read_text(encoding="utf-8").splitlines()
            if line.strip() and not line.startswith(f"user {username}")
        ]
    acl_lines.extend(lines)
    ACL_PATH.write_text("\n".join(acl_lines), encoding="utf-8")
    ACL_PATH.chmod(0o600)


def ensure_ingest_service_account(password: str) -> None:
    """Register internal API subscriber credentials (read all farm telemetry topics)."""
    if not password:
        return
    _ensure_dirs()
    _write_passwd(INGEST_USERNAME, password)
    _upsert_acl(
        INGEST_USERNAME,
        [
            f"user {INGEST_USERNAME}",
            f"topic read {INGEST_TOPIC_READ}",
            "",
        ],
    )


def register_device_mqtt_auth(*, device_id: UUID, farm_id: UUID, device_key: str) -> dict[str, str]:
    """Register device username/password and topic ACL. Returns MQTT connection hints."""
    _ensure_dirs()
    username = str(device_id)
    password = device_key
    topic = f"obolla/farm/{farm_id}/telemetry"

    _write_passwd(username, password)
    _upsert_acl(
        username,
        [
            f"user {username}",
            f"topic write {topic}",
            "",
        ],
    )

    return {
        "mqtt_username": username,
        "mqtt_password": password,
        "mqtt_topic": topic,
    }