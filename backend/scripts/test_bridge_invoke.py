import asyncio
import json
import selectors

from httpx import AsyncClient

EMAIL = "bridge-e2e-2fdb7dfe@example.com"
PASSWORD = "SecurePass123"


async def main() -> None:
    async with AsyncClient(base_url="http://127.0.0.1:8000", timeout=60.0) as client:
        login = await client.post("/api/v1/auth/login", json={"email": EMAIL, "password": PASSWORD})
        headers = {"Authorization": f"Bearer {login.json()['access_token']}"}
        device = (await client.get("/api/v1/bridge/devices", headers=headers)).json()[-1]
        invoke = await client.post(
            f"/api/v1/bridge/devices/{device['id']}/invoke",
            headers=headers,
            json={"tool": "list_dir", "args": {"path": "."}},
        )
        print(json.dumps(invoke.json(), indent=2)[:600])


if __name__ == "__main__":
    asyncio.run(main(), loop_factory=lambda: asyncio.SelectorEventLoop(selectors.SelectSelector()))