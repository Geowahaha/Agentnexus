"""List bridge devices for a user email (uses DATABASE_URL from backend/.env)."""

import asyncio
import selectors
import sys

from sqlalchemy import text

from app.core.database import async_session_maker

EMAIL = sys.argv[1] if len(sys.argv) > 1 else "geowahaha@gmail.com"


async def main() -> None:
    async with async_session_maker() as session:
        user = (
            await session.execute(
                text("SELECT id::text, email FROM users WHERE email = :email"),
                {"email": EMAIL},
            )
        ).first()
        if user is None:
            raise SystemExit(f"User not found: {EMAIL}")
        print(f"user: {user[1]} ({user[0]})")

        rows = (
            await session.execute(
                text(
                    """
                    SELECT id::text, device_name, status, user_id::text, last_seen_at, created_at
                    FROM bridge_devices
                    WHERE user_id = :uid
                    ORDER BY created_at DESC
                    """
                ),
                {"uid": user[0]},
            )
        ).all()
        print(f"devices ({len(rows)}):")
        for row in rows:
            print(f"  {row[1]:30} {row[0]}  status={row[2]}  last_seen={row[4]}")

        hp = (
            await session.execute(
                text(
                    """
                    SELECT d.id::text, d.device_name, d.status, u.email, d.last_seen_at
                    FROM bridge_devices d
                    JOIN users u ON u.id = d.user_id
                    WHERE d.device_name ILIKE '%HP%' OR d.id::text = 'fe135ab6-8393-4e72-be06-45881cc07a01'
                    """
                )
            )
        ).all()
        print(f"HP_AL01 search ({len(hp)}):")
        for row in hp:
            print(f"  {row[1]} ({row[0]}) owner={row[3]} status={row[2]} last_seen={row[4]}")


if __name__ == "__main__":
    asyncio.run(main(), loop_factory=lambda: asyncio.SelectorEventLoop(selectors.SelectSelector()))