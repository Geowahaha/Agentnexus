"""Create pairing code for geowahaha@gmail.com and pair local machine."""

import asyncio
import secrets
import selectors
import string
import subprocess
import sys
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

from sqlalchemy import text

from app.core.database import async_session_maker

ROOT = Path(__file__).resolve().parents[2]
BRIDGE_CLI = ROOT / "packages" / "bridge" / "index.mjs"
API_BASE = "https://agentnexus.mrgeo888.workers.dev"
EMAIL = "geowahaha@gmail.com"
DEVICE_NAME = "George-PC"


def _generate_code() -> str:
    return "".join(secrets.choice(string.digits) for _ in range(6))


async def create_code_for_user() -> str:
    async with async_session_maker() as session:
        result = await session.execute(
            text("SELECT id::text FROM users WHERE email = :email"),
            {"email": EMAIL},
        )
        row = result.first()
        if row is None:
            raise SystemExit(f"User not found: {EMAIL}")
        user_id = row[0]
        code = _generate_code()
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=5)
        await session.execute(
            text(
                """
                INSERT INTO bridge_pairing_codes (id, user_id, code, expires_at, created_at)
                VALUES (:id, :user_id, :code, :expires_at, :created_at)
                """
            ),
            {
                "id": str(uuid.uuid4()),
                "user_id": user_id,
                "code": code,
                "expires_at": expires_at,
                "created_at": datetime.now(timezone.utc),
            },
        )
        await session.commit()
        print(f"user: {EMAIL} ({user_id})")
        print(f"pairing code: {code} (expires {expires_at.isoformat()})")
        return code


def pair_and_connect(code: str) -> None:
    pair = subprocess.run(
        [
            "node",
            str(BRIDGE_CLI),
            "pair",
            code,
            "--name",
            DEVICE_NAME,
            "--allow-write",
            "--api",
            API_BASE,
        ],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        check=False,
    )
    print(pair.stdout.strip())
    if pair.stderr.strip():
        print(pair.stderr.strip(), file=sys.stderr)
    if pair.returncode != 0:
        raise SystemExit(f"pair failed ({pair.returncode})")

    print("Starting bridge connect (background)...")
    subprocess.Popen(
        ["node", str(BRIDGE_CLI), "connect", "--api", API_BASE],
        cwd=str(ROOT),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    print("Bridge connect started for", DEVICE_NAME)


async def main() -> None:
    code = await create_code_for_user()
    pair_and_connect(code)


if __name__ == "__main__":
    asyncio.run(main(), loop_factory=lambda: asyncio.SelectorEventLoop(selectors.SelectSelector()))