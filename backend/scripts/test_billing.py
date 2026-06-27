"""Run after PostgreSQL is available and migration 004 is applied."""

import asyncio
import sys
import uuid

from httpx import ASGITransport, AsyncClient

from app.main import app


async def main() -> None:
    email = f"billing-{uuid.uuid4().hex[:8]}@example.com"
    password = "SecurePass123"

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        await client.post(
            "/api/v1/auth/register",
            json={"email": email, "password": password, "full_name": "Billing Tester"},
        )
        token = (
            await client.post("/api/v1/auth/login", json={"email": email, "password": password})
        ).json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        wallet = await client.get("/api/v1/billing/wallet", headers=headers)
        assert wallet.status_code == 200, wallet.text
        balance = float(wallet.json()["balance_usd"])
        assert balance >= 5.0
        print(f"signup wallet: ${balance:.2f}")

        agents = await client.get("/api/v1/marketplace/agents")
        agent = agents.json()[0]

        estimate = await client.post(
            "/api/v1/billing/estimate",
            headers=headers,
            json={"workflow_type": "single_agent", "agent_id": agent["id"]},
        )
        assert estimate.status_code == 200, estimate.text
        est = estimate.json()
        assert float(est["marketplace_cost_usd"]) > 0
        print(f"estimate marketplace: ${float(est['marketplace_cost_usd']):.4f}")

        topup = await client.post(
            "/api/v1/billing/topup",
            headers=headers,
            json={"amount_usd": "10.00"},
        )
        assert topup.status_code == 200, topup.text
        print(f"topup balance: ${float(topup.json()['balance_usd']):.2f}")

        txs = await client.get("/api/v1/billing/transactions", headers=headers)
        assert txs.status_code == 200
        assert len(txs.json()) >= 2
        print(f"transactions: {len(txs.json())}")

        invalid = await client.post(
            "/api/v1/billing/topup",
            headers=headers,
            json={"amount_usd": "-1"},
        )
        assert invalid.status_code == 422
        print("topup validation: ok")

    print("billing: ok")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as exc:
        print(f"billing test failed: {exc}", file=sys.stderr)
        raise