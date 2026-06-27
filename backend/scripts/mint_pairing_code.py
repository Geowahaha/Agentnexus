"""Mint a bridge pairing code (30 min TTL) for geowahaha@gmail.com."""

import asyncio
import secrets
import selectors
import string
import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import text

from app.core.database import async_session_maker

EMAIL = "geowahaha@gmail.com"
TTL_MINUTES = 30


def generate_code() -> str:
    return "".join(secrets.choice(string.digits) for _ in range(6))


async def main() -> None:
    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(minutes=TTL_MINUTES)
    code = generate_code()

    async with async_session_maker() as session:
        user = (
            await session.execute(
                text("SELECT id::text FROM users WHERE email = :email"),
                {"email": EMAIL},
            )
        ).first()
        if user is None:
            raise SystemExit(f"User not found: {EMAIL}")

        await session.execute(
            text(
                """
                INSERT INTO bridge_pairing_codes (id, user_id, code, expires_at, created_at)
                VALUES (:id, :user_id, :code, :expires_at, :created_at)
                """
            ),
            {
                "id": str(uuid.uuid4()),
                "user_id": user[0],
                "code": code,
                "expires_at": expires_at,
                "created_at": now,
            },
        )
        await session.commit()

    print(f"user: {EMAIL}")
    print(f"code: {code}")
    print(f"expires_at: {expires_at.isoformat()}")
    print(
        "customer command:\n"
        f'powershell -NoProfile -ExecutionPolicy Bypass -Command "irm \'https://obolla.com/bridge/install.ps1?force=1&code={code}\' | iex"'
    )


if __name__ == "__main__":
    asyncio.run(main(), loop_factory=lambda: asyncio.SelectorEventLoop(selectors.SelectSelector()))