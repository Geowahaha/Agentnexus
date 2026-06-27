"""Run after PostgreSQL is available and migration 003 is applied."""

import asyncio
import sys
import uuid

from httpx import ASGITransport, AsyncClient

from app.core.config import settings
from app.core.database import async_session_maker
from app.db.models.user import SYSTEM_USER_ID
from app.main import app
from app.repositories.agent_repository import AgentRepository
from app.services.agent_registry import AgentRegistry
from app.services.tool_resolver import BuiltinOnlyToolResolver


async def main() -> None:
    email = f"tester-{uuid.uuid4().hex[:8]}@example.com"
    password = "SecurePass123"

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        register = await client.post(
            "/api/v1/auth/register",
            json={"email": email, "password": password, "full_name": "Test User"},
        )
        assert register.status_code == 201, register.text
        user = register.json()
        print(f"register: {user['email']}")

        login = await client.post(
            "/api/v1/auth/login",
            json={"email": email, "password": password},
        )
        assert login.status_code == 200, login.text
        token = login.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        me = await client.get("/api/v1/auth/me", headers=headers)
        assert me.status_code == 200
        assert me.json()["id"] == user["id"]
        print("auth me: ok")

        create = await client.post(
            "/api/v1/agents",
            headers=headers,
            json={
                "name": f"Owned Agent {uuid.uuid4().hex[:6]}",
                "description": "Owned by authenticated user",
                "role": "You are helpful.",
                "llm_model": "gpt-4o-mini",
                "tools": ["calculator"],
            },
        )
        assert create.status_code == 201, create.text
        agent = create.json()
        assert agent["owner_id"] == user["id"]
        print("create owned agent: ok")

        other = await client.post(
            "/api/v1/auth/register",
            json={
                "email": f"other-{uuid.uuid4().hex[:8]}@example.com",
                "password": password,
                "full_name": "Other User",
            },
        )
        other_token = (
            await client.post("/api/v1/auth/login", json={"email": other.json()["email"], "password": password})
        ).json()["access_token"]
        other_headers = {"Authorization": f"Bearer {other_token}"}

        forbidden = await client.put(
            f"/api/v1/agents/{agent['id']}",
            headers=other_headers,
            json={"description": "Hijack attempt"},
        )
        assert forbidden.status_code == 403, forbidden.text
        print("ownership protection: ok")

        marketplace = await client.get("/api/v1/marketplace/agents")
        assert marketplace.status_code == 200
        assert len(marketplace.json()) >= 1
        print("public marketplace: ok")

        unauthenticated = await client.post(
            "/api/v1/workflows/run",
            json={"task_description": "Say hello", "workflow_type": "single_agent"},
        )
        assert unauthenticated.status_code == 401
        print("workflow auth required: ok")

        if (
            settings.openai_api_key
            or settings.anthropic_api_key
            or settings.google_api_key
            or settings.gemini_api_key
            or settings.xai_api_key
        ):
            workflow = await client.post(
                "/api/v1/workflows/run",
                headers=headers,
                json={"task_description": "Say hello", "workflow_type": "single_agent"},
            )
            assert workflow.status_code == 200, workflow.text
            workflow_id = workflow.json()["workflow_id"]

            denied = await client.get(f"/api/v1/workflows/{workflow_id}", headers=other_headers)
            assert denied.status_code == 403
            print("workflow ownership: ok")
        else:
            print("workflow ownership: skipped (no LLM API key)")

        await client.delete(f"/api/v1/agents/{agent['id']}", headers=headers)

    async with async_session_maker() as session:
        registry = AgentRegistry(AgentRepository(session), BuiltinOnlyToolResolver())
        system_agents = await registry.list_marketplace_agents(owner_id=str(SYSTEM_USER_ID))
        assert len(system_agents) >= 3
        print(f"system seeded agents: {len(system_agents)}")

    print("auth: ok")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as exc:
        print(f"auth test failed: {exc}", file=sys.stderr)
        raise