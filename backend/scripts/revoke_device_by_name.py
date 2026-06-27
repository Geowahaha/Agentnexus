import asyncio
import selectors
import sys

from sqlalchemy import text

from app.core.database import async_session_maker

NAME = sys.argv[1] if len(sys.argv) > 1 else "HP_AL01"


async def main() -> None:
    async with async_session_maker() as session:
        result = await session.execute(
            text(
                """
                UPDATE bridge_devices
                SET status = 'revoked', revoked_at = NOW()
                WHERE device_name = :name AND status = 'active'
                """
            ),
            {"name": NAME},
        )
        await session.commit()
        print(f"revoked {result.rowcount} device(s) named {NAME}")


if __name__ == "__main__":
    asyncio.run(main(), loop_factory=lambda: asyncio.SelectorEventLoop(selectors.SelectSelector()))