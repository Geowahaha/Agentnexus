"""Create a bridge pairing code on production DB (run on VPS or with prod DATABASE_URL)."""

import asyncio
import selectors
import sys

from sqlalchemy import text

from app.core.database import async_session_maker


async def main() -> None:
    email = sys.argv[1] if len(sys.argv) > 1 else "geowahaha@gmail.com"
    async with async_session_maker() as session:
        row = (
            await session.execute(
                text("SELECT id::text FROM users WHERE email = :email"),
                {"email": email},
            )
        ).first()
        if row is None:
            raise SystemExit(f"User not found: {email}")

        from app.repositories.bridge_repository import BridgeRepository

        repo = BridgeRepository(session)
        code, expires_at = await repo.create_pairing_code(row[0])
        await session.commit()
        print(f"user: {email}")
        print(f"code: {code}")
        print(f"expires_at: {expires_at.isoformat()}")


if __name__ == "__main__":
    asyncio.run(main(), loop_factory=lambda: asyncio.SelectorEventLoop(selectors.SelectSelector()))