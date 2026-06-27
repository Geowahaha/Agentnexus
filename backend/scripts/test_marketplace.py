"""Run after PostgreSQL is available and migration 003 is applied."""

import asyncio
import sys
import uuid
from decimal import Decimal

from httpx import ASGITransport, AsyncClient

from app.core.database import async_session_maker
from app.db.models.user import SYSTEM_USER_ID
from app.main import app
from app.models.custom_tool import CustomToolCreate
from app.models.mcp_server import MCPServerCreate
from app.repositories.agent_repository import AgentRepository
from app.repositories.custom_tool_repository import CustomToolRepository
from app.repositories.mcp_server_repository import MCPServerRepository
from app.services.agent_registry import AgentRegistry
from app.services.mcp_service import MCPService
from app.services.tool_resolver import ToolResolver


async def _auth_headers(client: AsyncClient) -> dict[str, str]:
    email = f"market-{uuid.uuid4().hex[:8]}@example.com"
    password = "SecurePass123"
    await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": password, "full_name": "Marketplace Tester"},
    )
    token = (
        await client.post("/api/v1/auth/login", json={"email": email, "password": password})
    ).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


async def test_repositories() -> None:
    owner_id = str(SYSTEM_USER_ID)
    async with async_session_maker() as session:
        custom_repo = CustomToolRepository(session)
        mcp_repo = MCPServerRepository(session)
        mcp_service = MCPService(mcp_repo)
        tool_resolver = ToolResolver(custom_repo, mcp_repo, mcp_service)
        registry = AgentRegistry(AgentRepository(session), tool_resolver)

        agents = await registry.list_marketplace_agents(category="research")
        assert agents, "Expected marketplace agents after migration 002"
        assert agents[0].price_usd_per_run >= Decimal("0")
        print(f"marketplace agents: {len(agents)}")

        custom_tool = await custom_repo.create(
            CustomToolCreate(
                name="echo_http",
                description="Echo test HTTP tool",
                tool_type="http",
                config={
                    "url": "https://httpbin.org/post",
                    "method": "POST",
                    "arg_mapping": "body",
                },
            ),
            owner_id=owner_id,
        )
        assert custom_tool.name == "echo_http"
        print("custom tool create: ok")

        catalog = await tool_resolver.list_catalog()
        assert any(item.name == "echo_http" and item.source == "custom" for item in catalog)
        await tool_resolver.validate_tool_names(["calculator", "echo_http"])
        print("tool resolver custom tool: ok")

        mcp_server = await mcp_repo.create_server(
            MCPServerCreate(
                name="demo_server",
                description="Demo MCP server entry",
                transport="sse",
                config={"url": "http://127.0.0.1:9999/sse"},
            ),
            owner_id=owner_id,
        )
        tools = await mcp_repo.replace_tools_for_server(
            mcp_server,
            [
                {
                    "tool_name": "ping",
                    "description": "Ping tool",
                    "input_schema": {"type": "object", "properties": {}},
                }
            ],
        )
        assert tools[0].qualified_name == "mcp.demo_server.ping"
        await tool_resolver.validate_tool_names(["mcp.demo_server.ping"])
        print("mcp tool registry: ok")

        await custom_repo.delete(custom_tool.id)
        await mcp_repo.delete_server(mcp_server.id)
        print("repository cleanup: ok")


async def test_api() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        headers = await _auth_headers(client)

        marketplace = await client.get("/api/v1/marketplace/agents", params={"category": "content"})
        assert marketplace.status_code == 200, marketplace.text
        assert len(marketplace.json()) >= 1
        print(f"marketplace api: {len(marketplace.json())} agents")

        tools = await client.get("/api/v1/tools")
        assert tools.status_code == 200, tools.text
        payload = tools.json()
        assert any(item["source"] == "builtin" for item in payload)
        print(f"tools api: {len(payload)} tools")

        custom = await client.post(
            "/api/v1/custom-tools",
            headers=headers,
            json={
                "name": "api_echo",
                "description": "API echo tool",
                "tool_type": "http",
                "config": {"url": "https://httpbin.org/post", "method": "POST"},
            },
        )
        assert custom.status_code == 201, custom.text
        custom_id = custom.json()["id"]

        mcp = await client.post(
            "/api/v1/mcp-servers",
            headers=headers,
            json={
                "name": "api_demo",
                "description": "API demo MCP server",
                "transport": "stdio",
                "config": {"command": "echo", "args": ["mcp-demo"]},
            },
        )
        assert mcp.status_code == 201, mcp.text
        server_id = mcp.json()["id"]

        listed = await client.get(f"/api/v1/mcp-servers/{server_id}/tools")
        assert listed.status_code == 200
        assert listed.json() == []

        await client.delete(f"/api/v1/custom-tools/{custom_id}", headers=headers)
        await client.delete(f"/api/v1/mcp-servers/{server_id}", headers=headers)
        print("marketplace api cleanup: ok")


async def main() -> None:
    await test_repositories()
    await test_api()
    print("marketplace: ok")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as exc:
        print(f"marketplace test failed: {exc}", file=sys.stderr)
        raise