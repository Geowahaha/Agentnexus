from mcp import ClientSession
from mcp.client.sse import sse_client
from mcp.client.stdio import StdioServerParameters, stdio_client

from app.core.mcp_http import HttpMcpClient

from app.core.config import settings
from app.models.mcp_server import MCPServer, MCPTool
from app.repositories.mcp_server_repository import (
    MCPServerNotFoundError,
    MCPServerRepository,
    MCPToolNotFoundError,
)


class MCPService:
    def __init__(self, repository: MCPServerRepository) -> None:
        self._repository = repository

    async def sync_tools(self, server_id: str) -> list[MCPTool]:
        server = await self._repository.get_server_by_id(server_id)
        if server is None:
            raise MCPServerNotFoundError(server_id)
        if not server.is_active:
            raise ValueError(f"MCP server '{server.name}' is inactive")

        remote_tools = await self._list_remote_tools(server)
        return await self._repository.replace_tools_for_server(server, remote_tools)

    async def invoke_tool(self, qualified_name: str, arguments: dict) -> str:
        pair = await self._repository.get_tool_with_server(qualified_name)
        if pair is None:
            raise MCPToolNotFoundError(qualified_name)

        tool, server = pair
        if not tool.is_active or not server.is_active:
            raise ValueError(f"MCP tool '{qualified_name}' is inactive")

        if server.transport == "http":
            url = server.config.get("url")
            if not url:
                raise ValueError(f"MCP server '{server.name}' http config requires 'url'")
            headers = dict(server.config.get("headers") or {})
            if settings.aibotauth_mcp_api_key and "aibotauth" in server.name.lower():
                headers["Authorization"] = f"Bearer {settings.aibotauth_mcp_api_key}"
            client = HttpMcpClient(url, headers=headers or None)
            return await client.call_tool(tool.tool_name, arguments)

        result = await self._with_session(server, lambda session: session.call_tool(tool.tool_name, arguments))
        return self._format_call_result(result)

    async def _list_remote_tools(self, server: MCPServer) -> list[dict]:
        if server.transport == "http":
            return await self._list_remote_tools_http(server)

        list_result = await self._with_session(server, lambda session: session.list_tools())
        return [
            {
                "tool_name": item.name,
                "description": item.description or "",
                "input_schema": item.inputSchema or {},
            }
            for item in list_result.tools
        ]

    async def _with_session(self, server: MCPServer, callback):
        if server.transport == "stdio":
            command = server.config.get("command")
            if not command:
                raise ValueError(f"MCP server '{server.name}' stdio config requires 'command'")
            params = StdioServerParameters(
                command=command,
                args=list(server.config.get("args") or []),
                env=server.config.get("env"),
            )
            async with stdio_client(params) as (read, write):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    return await callback(session)

        if server.transport == "sse":
            url = server.config.get("url")
            if not url:
                raise ValueError(f"MCP server '{server.name}' sse config requires 'url'")
            headers = server.config.get("headers")
            async with sse_client(url, headers=headers) as (read, write):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    return await callback(session)

        if server.transport == "http":
            raise ValueError("Use invoke_tool/list via HTTP transport directly")

        raise ValueError(f"Unsupported MCP transport: {server.transport}")

    async def _list_remote_tools_http(self, server: MCPServer) -> list[dict]:
        url = server.config.get("url")
        if not url:
            raise ValueError(f"MCP server '{server.name}' http config requires 'url'")
        headers = dict(server.config.get("headers") or {})
        if settings.aibotauth_mcp_api_key and "aibotauth" in server.name.lower():
            headers["Authorization"] = f"Bearer {settings.aibotauth_mcp_api_key}"
        client = HttpMcpClient(url, headers=headers or None)
        tools = await client.list_tools()
        return [
            {
                "tool_name": item["name"],
                "description": item.get("description") or "",
                "input_schema": item.get("inputSchema") or {},
            }
            for item in tools
        ]

    @staticmethod
    def _format_call_result(result) -> str:
        if result.isError:
            chunks = []
            for item in result.content or []:
                text = getattr(item, "text", None)
                if text:
                    chunks.append(text)
            message = "\n".join(chunks) if chunks else "MCP tool returned an error"
            raise RuntimeError(message)

        chunks: list[str] = []
        for item in result.content or []:
            text = getattr(item, "text", None)
            if text:
                chunks.append(text)
            elif getattr(item, "type", None) == "text":
                chunks.append(str(item))
        if chunks:
            return "\n".join(chunks)
        if result.structuredContent is not None:
            return str(result.structuredContent)
        return ""