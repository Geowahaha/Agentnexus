"""Grant platform admin role to configured emails. Run on VPS:

  docker exec agentnexus-postgres psql -U agentnexus -d agentnexus -c \\
    "UPDATE users SET role = 'admin' WHERE lower(email) IN ('mrgeo888@gmail.com','geowahaha@gmail.com');"

Or: docker exec agentnexus-api python scripts/set_platform_admins.py
"""

from __future__ import annotations

import asyncio
import sys

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from app.core.config import settings

DEFAULT_ADMIN_EMAILS = ("mrgeo888@gmail.com", "geowahaha@gmail.com")


def configured_admin_emails() -> list[str]:
    raw = settings.platform_admin_emails or ""
    emails = [part.strip().lower() for part in raw.split(",") if part.strip()]
    return emails or list(DEFAULT_ADMIN_EMAILS)


async def main() -> int:
    emails = configured_admin_emails()
    engine = create_async_engine(settings.database_url, pool_pre_ping=True)
    async with engine.begin() as conn:
        for email in emails:
            result = await conn.execute(
                text(
                    """
                    UPDATE users
                    SET role = 'admin', updated_at = NOW()
                    WHERE lower(email) = :email
                    RETURNING email, role
                    """
                ),
                {"email": email},
            )
            row = result.first()
            if row:
                print(f"OK admin -> {row[0]}")
            else:
                print(f"SKIP not found: {email}", file=sys.stderr)

    await engine.dispose()
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))