"""Run after migration 005 is applied."""

import asyncio
import sys
import uuid
from decimal import Decimal

from httpx import ASGITransport, AsyncClient

from app.core.database import async_session_maker
from app.main import app
from app.repositories.agent_repository import AgentRepository
from app.repositories.wallet_repository import WalletRepository
from app.services.agent_registry import AgentRegistry
from app.services.tool_resolver import BuiltinOnlyToolResolver


async def main() -> None:
    email = f"creator-{uuid.uuid4().hex[:8]}@example.com"
    password = "SecurePass123"

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        reg = await client.post(
            "/api/v1/auth/register",
            json={"email": email, "password": password, "full_name": "Creator User"},
        )
        assert reg.status_code == 201, reg.text
        creator = reg.json()
        token = (
            await client.post("/api/v1/auth/login", json={"email": email, "password": password})
        ).json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        agent = await client.post(
            "/api/v1/agents",
            headers=headers,
            json={
                "name": f"Payout Agent {uuid.uuid4().hex[:6]}",
                "description": "Paid agent for payout test",
                "role": "You are helpful.",
                "llm_model": "gpt-4o-mini",
                "tools": [],
                "price_usd_per_run": "0.50",
                "category": "research",
            },
        )
        assert agent.status_code == 201, agent.text
        agent_row = agent.json()
        print(f"created agent: {agent_row['id']}")

        buyer_email = f"buyer-{uuid.uuid4().hex[:8]}@example.com"
        buyer_reg = await client.post(
            "/api/v1/auth/register",
            json={"email": buyer_email, "password": password, "full_name": "Buyer User"},
        )
        buyer_id = buyer_reg.json()["id"]
        buyer_token = (
            await client.post("/api/v1/auth/login", json={"email": buyer_email, "password": password})
        ).json()["access_token"]
        buyer_headers = {"Authorization": f"Bearer {buyer_token}"}

        print("buyer registered: ok")

    async with async_session_maker() as session:
        wallet_repo = WalletRepository(session)
        await wallet_repo.add_credits(
            buyer_id,
            Decimal("10"),
            transaction_type="stripe_topup",
            description="Stripe payment test_session",
        )
        print("buyer stripe top-up: ok")
        await wallet_repo.charge_workflow(
            user_id=buyer_id,
            workflow_id=str(uuid.uuid4()),
            marketplace_cost=Decimal("0.50"),
            llm_cost=Decimal("0.01"),
            agent_charges=[
                {
                    "agent_id": agent_row["id"],
                    "agent_name": agent_row["name"],
                    "owner_id": creator["id"],
                    "price_usd_per_run": "0.50",
                }
            ],
            platform_fee_percent=Decimal("20"),
        )
        print("workflow charge with payout: ok")

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        earnings = await client.get("/api/v1/billing/earnings", headers=headers)
        assert earnings.status_code == 200, earnings.text
        summary = earnings.json()
        assert float(summary["earnings_balance_usd"]) == 0.4
        assert len(summary["recent_earnings"]) == 1
        print(f"creator earnings: ${float(summary['earnings_balance_usd']):.2f}")

        transfer = await client.post("/api/v1/billing/earnings/transfer", headers=headers, json={})
        assert transfer.status_code == 200, transfer.text
        assert float(transfer.json()["earnings_balance_usd"]) == 0
        print("earnings transfer: ok")

        config = await client.get("/api/v1/billing/config", headers=headers)
        assert config.status_code == 200
        assert config.json()["platform_fee_percent"] == 20.0
        print("billing config: ok")

    async with async_session_maker() as session:
        registry = AgentRegistry(AgentRepository(session), BuiltinOnlyToolResolver())
        agents = await registry.list_marketplace_agents()
        assert agents
        print(f"marketplace agents: {len(agents)}")

    print("creator payouts: ok")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as exc:
        print(f"creator payout test failed: {exc}", file=sys.stderr)
        raise