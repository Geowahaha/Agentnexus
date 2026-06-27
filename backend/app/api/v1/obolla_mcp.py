"""OBOLLA public MCP HTTP transport (JSON-RPC) — apply_agent_ready_fix without local Bridge."""

from __future__ import annotations

import json
from typing import Any

from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_session
from app.services.agent_ready.mcp_tools import APPLY_AGENT_READY_FIX_TOOL
from app.services.agent_ready.orchestrator import AgentReadyOrchestrator
from app.services.moat_service import log_revenue_sale_from_outreach

router = APIRouter()
_orchestrator = AgentReadyOrchestrator()

MCP_PROTOCOL_VERSION = "2024-11-05"

def _mcp_tool_listing(tool: dict[str, Any]) -> dict[str, Any]:
    listing = {"name": tool["name"], "description": tool["description"]}
    schema = tool.get("inputSchema") or tool.get("input_schema")
    if schema:
        listing["inputSchema"] = schema
    return listing


SITE_DISCOVERY_TOOL = {
    "name": "site_discovery",
    "description": "Read public OBOLLA discovery and contact information.",
    "inputSchema": {
        "type": "object",
        "properties": {
            "topic": {"type": "string", "description": "Optional focus: marketplace, agent-ready, smart-farm"},
        },
    },
}

MCP_TOOLS = [_mcp_tool_listing(SITE_DISCOVERY_TOOL), _mcp_tool_listing(APPLY_AGENT_READY_FIX_TOOL)]


def _mcp_result(request_id: Any, result: Any) -> JSONResponse:
    return JSONResponse({"jsonrpc": "2.0", "id": request_id, "result": result})


def _mcp_error(request_id: Any, code: int, message: str) -> JSONResponse:
    return JSONResponse(
        {"jsonrpc": "2.0", "id": request_id, "error": {"code": code, "message": message}}
    )


def _tool_text_content(payload: Any) -> dict[str, Any]:
    return {
        "content": [{"type": "text", "text": json.dumps(payload, indent=2) if isinstance(payload, dict) else str(payload)}],
        "isError": False,
    }


async def _handle_site_discovery(arguments: dict[str, Any]) -> dict[str, Any]:
    topic = (arguments.get("topic") or "general").strip().lower()
    discovery = {
        "origin": "https://obolla.com",
        "topic": topic,
        "agents_txt": "https://obolla.com/agents.txt",
        "api_catalog": "https://obolla.com/.well-known/api-catalog",
        "openapi": "https://obolla.com/openapi.json",
        "auth_md": "https://obolla.com/auth.md",
        "agent_card": "https://obolla.com/.well-known/agent-card.json",
        "mcp_server_card": "https://obolla.com/.well-known/mcp/server-card.json",
        "agent_ready_apply": "POST https://obolla.com/mcp  (or /api/v1/mcp)  tools/call apply_agent_ready_fix",
        "agent_ready_api": "POST https://obolla.com/api/v1/agent-ready/apply",
    }
    if topic in ("agent-ready", "agent_ready", "fix"):
        discovery["flagship_skill"] = "agent-ready-auto-fix"
        discovery["workflow"] = "Scan → fix pack → apply_agent_ready_fix → re-verify at isitagentready.com"
    return _tool_text_content(discovery)


async def _handle_apply_agent_ready_fix(
    arguments: dict[str, Any],
    session: AsyncSession,
) -> dict[str, Any]:
    url = (arguments.get("url") or "").strip()
    if not url:
        return {"content": [{"type": "text", "text": "url is required"}], "isError": True}

    fix_pack = arguments.get("fix_pack")
    if not fix_pack:
        fix_pack = _orchestrator.build_fix_pack(url)

    apply_result = await _orchestrator.apply_agent_ready_fix(
        url=url,
        fix_pack=fix_pack,
        github_token=arguments.get("github_token"),
        repo=arguments.get("repo"),
        cf_project_name=arguments.get("cf_project_name"),
        cf_api_token=arguments.get("cf_api_token"),
        cf_worker_name=arguments.get("cf_worker_name"),
        cf_account_id=arguments.get("cf_account_id"),
    )

    sale = await log_revenue_sale_from_outreach(
        session=session,
        skill_slug="agent-ready-auto-fix",
        amount_usd=9.99,
        source="obolla_mcp_apply",
    )
    await session.commit()

    payload = {
        "result": apply_result,
        "sale": sale,
        "revenue_logged": True,
        "message": apply_result.get("message", "apply_agent_ready_fix executed"),
    }
    return _tool_text_content(payload)


@router.post("/mcp")
async def obolla_mcp_jsonrpc(
    request: Request,
    session: AsyncSession = Depends(get_session),
) -> JSONResponse:
    """Streamable HTTP MCP endpoint at https://obolla.com/mcp and https://obolla.com/api/v1/mcp.

    Supports standard MCP JSON-RPC for apply_agent_ready_fix (no local Bridge).
    """
    try:
        body = await request.json()
    except Exception:
        return _mcp_error(None, -32700, "Parse error")

    if isinstance(body, list):
        body = body[0] if body else {}

    request_id = body.get("id")
    method = body.get("method")
    params = body.get("params") or {}

    if method == "initialize":
        return _mcp_result(
            request_id,
            {
                "protocolVersion": MCP_PROTOCOL_VERSION,
                "capabilities": {"tools": {}},
                "serverInfo": {"name": "OBOLLA MCP", "version": "1.0.0"},
            },
        )

    if method == "notifications/initialized":
        return _mcp_result(request_id, {})

    if method == "tools/list":
        return _mcp_result(request_id, {"tools": MCP_TOOLS})

    if method == "tools/call":
        name = params.get("name")
        arguments = params.get("arguments") or {}
        try:
            if name == "site_discovery":
                return _mcp_result(request_id, await _handle_site_discovery(arguments))
            if name == "apply_agent_ready_fix":
                return _mcp_result(request_id, await _handle_apply_agent_ready_fix(arguments, session))
            return _mcp_error(request_id, -32601, f"Unknown tool: {name}")
        except Exception as exc:  # noqa: BLE001
            return _mcp_result(
                request_id,
                {"content": [{"type": "text", "text": str(exc)}], "isError": True},
            )

    return _mcp_error(request_id, -32601, f"Method not found: {method}")