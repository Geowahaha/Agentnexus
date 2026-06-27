"""End-to-end Local Agent Bridge test: pair -> connect -> invoke list_dir."""

import asyncio
import json
import selectors
import subprocess
import sys
import time
import uuid
from pathlib import Path

from httpx import ASGITransport, AsyncClient

from app.main import app

ROOT = Path(__file__).resolve().parents[2]
BRIDGE_CLI = ROOT / "packages" / "bridge" / "index.mjs"


async def main() -> None:
    email = f"bridge-e2e-{uuid.uuid4().hex[:8]}@example.com"
    password = "SecurePass123"

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test", timeout=60.0) as client:
        reg = await client.post(
            "/api/v1/auth/register",
            json={"email": email, "password": password, "full_name": "Bridge E2E"},
        )
        assert reg.status_code == 201, reg.text
        user_id = reg.json()["id"]
        print(f"user: {email} ({user_id})")

        login = await client.post("/api/v1/auth/login", json={"email": email, "password": password})
        assert login.status_code == 200, login.text
        token = login.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        code_resp = await client.post("/api/v1/bridge/pairing-codes", headers=headers)
        assert code_resp.status_code == 200, code_resp.text
        code = code_resp.json()["code"]
        print(f"pairing code: {code}")

    api_base = "https://agentnexus.mrgeo888.workers.dev"
    pair_proc = subprocess.run(
        [
            "node",
            str(BRIDGE_CLI),
            "pair",
            code,
            "--name",
            "E2E-Test-PC",
            "--api",
            api_base,
        ],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        check=False,
    )
    print(pair_proc.stdout.strip())
    if pair_proc.returncode != 0:
        print(pair_proc.stderr.strip(), file=sys.stderr)
        raise SystemExit(f"pair failed ({pair_proc.returncode})")

    connect_proc = subprocess.Popen(
        ["node", str(BRIDGE_CLI), "connect", "--api", api_base],
        cwd=str(ROOT),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    print("bridge connect started (background)")

    device_id = None
    deadline = time.time() + 20
    while time.time() < deadline:
        line = connect_proc.stdout.readline() if connect_proc.stdout else ""
        if line:
            print(f"  bridge: {line.rstrip()}")
            if "Bridge online" in line:
                break
        elif connect_proc.poll() is not None:
            break
        await asyncio.sleep(0.3)

    async with AsyncClient(base_url="http://127.0.0.1:8000", timeout=60.0) as client:
        login = await client.post("/api/v1/auth/login", json={"email": email, "password": password})
        assert login.status_code == 200, login.text
        token = login.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        devices = await client.get("/api/v1/bridge/devices", headers=headers)
        assert devices.status_code == 200, devices.text
        device_list = devices.json()
        assert device_list, "expected paired device"
        device_id = device_list[0]["id"]
        print(f"device: {device_list[0]['device_name']} ({device_id})")

        invoke = await client.post(
            f"/api/v1/bridge/devices/{device_id}/invoke",
            headers=headers,
            json={"tool": "list_dir", "args": {"path": "."}},
        )
        print(f"invoke status: {invoke.status_code}")
        payload = invoke.json()
        print(json.dumps(payload, indent=2)[:2000])

        if not payload.get("ok"):
            connect_proc.terminate()
            raise SystemExit(f"invoke failed: {payload.get('error')}")

        entries = payload.get("result", {}).get("entries", [])
        print(f"list_dir ok — {len(entries)} entries in cwd")
        for entry in entries[:8]:
            print(f"  - {entry['name']} ({entry['type']})")

    connect_proc.terminate()
    print("bridge e2e: PASS")


if __name__ == "__main__":
    asyncio.run(main(), loop_factory=lambda: asyncio.SelectorEventLoop(selectors.SelectSelector()))