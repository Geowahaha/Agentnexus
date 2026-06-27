"""JSON-RPC MCP client for HTTP transport (e.g. AIBotAuth POST /api/mcp)."""

from __future__ import annotations

import json
from typing import Any

import httpx

PROTOCOL_VERSION = "2024-11-05"
REQUEST_ID = 1


class HttpMcpError(RuntimeError):
    pass


class HttpMcpClient:
    def __init__(self, endpoint: str, *, timeout: float = 120.0, headers: dict | None = None) -> None:
        self._endpoint = endpoint.rstrip("/")
        self._timeout = timeout
        self._headers = {"content-type": "application/json", **(headers or {})}
        self._session_id = 0

    async def _rpc(self, method: str, params: dict | None = None) -> Any:
        self._session_id += 1
        payload = {
            "jsonrpc": "2.0",
            "id": self._session_id,
            "method": method,
            "params": params or {},
        }
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            response = await client.post(self._endpoint, json=payload, headers=self._headers)
            response.raise_for_status()
            data = response.json()

        if isinstance(data, list):
            data = data[0] if data else {}

        if "error" in data:
            err = data["error"]
            raise HttpMcpError(f"MCP {method} failed: {err.get('message', err)}")

        return data.get("result")

    async def initialize(self) -> dict:
        return await self._rpc(
            "initialize",
            {
                "protocolVersion": PROTOCOL_VERSION,
                "capabilities": {},
                "clientInfo": {"name": "agentnexus", "version": "0.1.0"},
            },
        )

    async def list_tools(self) -> list[dict]:
        await self.initialize()
        result = await self._rpc("tools/list")
        return list((result or {}).get("tools") or [])

    async def call_tool(self, name: str, arguments: dict) -> str:
        await self.initialize()
        result = await self._rpc("tools/call", {"name": name, "arguments": arguments})
        chunks: list[str] = []
        for item in (result or {}).get("content") or []:
            if isinstance(item, dict) and item.get("type") == "text":
                chunks.append(str(item.get("text", "")))
        if chunks:
            return "\n".join(chunks)
        if result is not None:
            return json.dumps(result)
        return ""