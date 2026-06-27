"""Workflow integration test with bridge_device_id."""

import asyncio
import json
import selectors

from httpx import AsyncClient

EMAIL = "bridge-e2e-2fdb7dfe@example.com"
PASSWORD = "SecurePass123"


async def main() -> None:
    async with AsyncClient(base_url="http://127.0.0.1:8000", timeout=120.0) as client:
        login = await client.post("/api/v1/auth/login", json={"email": EMAIL, "password": PASSWORD})
        login.raise_for_status()
        headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

        devices = (await client.get("/api/v1/bridge/devices", headers=headers)).json()
        device_id = devices[-1]["id"]
        agents = (await client.get("/api/v1/agents")).json()
        agent_id = agents[0]["id"]

        run = await client.post(
            "/api/v1/workflows/run",
            headers=headers,
            json={
                "task_description": (
                    'Use bridge.list_dir on path "." and tell me how many entries you see.'
                ),
                "workflow_type": "single_agent",
                "agent_id": agent_id,
                "bridge_device_id": device_id,
            },
        )
        run.raise_for_status()
        workflow_id = run.json()["workflow_id"]
        print(f"workflow: {workflow_id}")

        for _ in range(30):
            await asyncio.sleep(2)
            status_resp = await client.get(f"/api/v1/workflows/{workflow_id}", headers=headers)
            data = status_resp.json()
            status = data.get("status")
            tools = data.get("intermediate_results", {}).get("tool_calls", [])
            if status in ("completed", "failed"):
                print(f"status: {status}")
                print("tools:", json.dumps(tools, indent=2)[:1200])
                print("output:", str(data.get("final_output"))[:600])
                if status == "completed" and tools and '"ok": true' in tools[0].get("output", ""):
                    print("workflow bridge e2e: PASS")
                else:
                    raise SystemExit("workflow bridge e2e: FAIL")
                return

    raise SystemExit("workflow timed out")


if __name__ == "__main__":
    asyncio.run(main(), loop_factory=lambda: asyncio.SelectorEventLoop(selectors.SelectSelector()))