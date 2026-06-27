"""Grant demo wallet credits by email (no Stripe). Run on VPS:

  docker exec agentnexus-api python scripts/grant_demo_credits.py mrgeo888@gmail.com 100
"""

from __future__ import annotations

import asyncio
import sys
import uuid
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from app.billing.trial_credits import demo_topup_description
from app.core.config import settings


async def main() -> int:
    if len(sys.argv) < 3:
        print("Usage: grant_demo_credits.py <email> <amount_usd>", file=sys.stderr)
        return 1

    email = sys.argv[1].strip().lower()
    try:
        amount = Decimal(sys.argv[2])
    except Exception:
        print("Invalid amount_usd", file=sys.stderr)
        return 1
    if amount <= 0:
        print("amount_usd must be positive", file=sys.stderr)
        return 1

    engine = create_async_engine(settings.database_url, pool_pre_ping=True)
    now = datetime.now(timezone.utc)

    async with engine.begin() as conn:
        user_row = (
            await conn.execute(
                text("SELECT id::text FROM users WHERE lower(email) = :email LIMIT 1"),
                {"email": email},
            )
        ).first()
        if not user_row:
            print(f"User not found: {email}", file=sys.stderr)
            return 2
        user_id = user_row[0]

        wallet_row = (
            await conn.execute(
                text("SELECT id::text, balance_usd FROM wallets WHERE user_id = :uid LIMIT 1"),
                {"uid": user_id},
            )
        ).first()

        if wallet_row:
            wallet_id, balance = wallet_row[0], Decimal(str(wallet_row[1]))
            new_balance = balance + amount
            await conn.execute(
                text(
                    "UPDATE wallets SET balance_usd = :bal, updated_at = :now WHERE id = :wid"
                ),
                {"bal": new_balance, "now": now, "wid": wallet_id},
            )
        else:
            wallet_id = str(uuid.uuid4())
            new_balance = Decimal(str(settings.signup_credits_usd)) + amount
            await conn.execute(
                text(
                    """
                    INSERT INTO wallets (id, user_id, balance_usd, earnings_balance_usd, created_at, updated_at)
                    VALUES (:wid, :uid, :bal, 0, :now, :now)
                    """
                ),
                {"wid": wallet_id, "uid": user_id, "bal": new_balance, "now": now},
            )

        await conn.execute(
            text(
                """
                INSERT INTO billing_transactions (
                    id, user_id, workflow_id, transaction_type, amount_usd,
                    marketplace_cost_usd, llm_cost_usd, balance_after_usd,
                    description, agent_charges, created_at
                ) VALUES (
                    :tid, :uid, NULL, 'demo_topup', :amt,
                    0, 0, :bal_after,
                    :desc, '[]'::jsonb, :now
                )
                """
            ),
            {
                "tid": str(uuid.uuid4()),
                "uid": user_id,
                "amt": amount,
                "bal_after": new_balance,
                "desc": demo_topup_description(amount),
                "now": now,
            },
        )

    await engine.dispose()
    print(f"OK demo_topup ${amount:.2f} -> {email} (balance_usd=${new_balance:.2f})")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))