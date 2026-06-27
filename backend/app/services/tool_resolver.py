from dataclasses import dataclass

from langchain_core.tools import BaseTool

from app.models.custom_tool import CustomTool
from app.models.mcp_server import MCPTool
from app.repositories.custom_tool_repository import CustomToolRepository
from app.repositories.mcp_server_repository import MCPServerRepository
from app.services.bridge_service import BridgeService
from app.services.mcp_service import MCPService
from app.tools.bridge_catalog import BRIDGE_TOOL_DEFINITIONS, BRIDGE_TOOL_NAMES
from app.tools.bridge_factory import build_bridge_langchain_tool
from app.tools.factories import build_http_custom_tool, build_mcp_langchain_tool, invoke_http_custom_tool
from app.tools.registry import TOOL_CATALOG


@dataclass(frozen=True)
class ResolvedToolInfo:
    name: str
    description: str
    source: str


class ToolResolver:
    def __init__(
        self,
        custom_tool_repository: CustomToolRepository,
        mcp_server_repository: MCPServerRepository,
        mcp_service: MCPService,
        bridge_service: BridgeService | None = None,
    ) -> None:
        self._custom_tools = custom_tool_repository
        self._mcp_tools = mcp_server_repository
        self._mcp_service = mcp_service
        self._bridge_service = bridge_service

    async def list_catalog(self) -> list[ResolvedToolInfo]:
        catalog = [
            ResolvedToolInfo(name=name, description=tool.description or "", source="builtin")
            for name, tool in sorted(TOOL_CATALOG.items())
        ]

        for name in BRIDGE_TOOL_NAMES:
            catalog.append(
                ResolvedToolInfo(
                    name=name,
                    description=BRIDGE_TOOL_DEFINITIONS[name]["description"],
                    source="bridge",
                )
            )

        for custom_tool in await self._custom_tools.list_all(active_only=True):
            if custom_tool.tool_type == "http":
                catalog.append(
                    ResolvedToolInfo(
                        name=custom_tool.name,
                        description=custom_tool.description,
                        source="custom",
                    )
                )

        for mcp_tool in await self._mcp_tools.list_tools(active_only=True):
            catalog.append(
                ResolvedToolInfo(
                    name=mcp_tool.qualified_name,
                    description=mcp_tool.description,
                    source="mcp",
                )
            )
        return catalog

    async def validate_tool_names(self, tool_names: list[str]) -> None:
        if not tool_names:
            return

        unknown: list[str] = []
        for name in tool_names:
            if name in TOOL_CATALOG or name in BRIDGE_TOOL_DEFINITIONS:
                continue
            custom_tool = await self._custom_tools.get_by_name(name)
            if custom_tool and custom_tool.is_active and custom_tool.tool_type == "http":
                continue
            mcp_tool = await self._mcp_tools.get_tool_by_qualified_name(name)
            if mcp_tool and mcp_tool.is_active:
                continue
            unknown.append(name)

        if unknown:
            available = ", ".join(item.name for item in await self.list_catalog())
            raise ValueError(f"Unknown tool(s): {', '.join(unknown)}. Available: {available}")

    async def resolve_tools(self, tool_names: list[str] | None) -> list[BaseTool]:
        if not tool_names:
            return []

        await self.validate_tool_names(tool_names)
        resolved: list[BaseTool] = []
        for name in tool_names:
            if name in TOOL_CATALOG:
                resolved.append(TOOL_CATALOG[name])
                continue

            if name in BRIDGE_TOOL_DEFINITIONS:
                if self._bridge_service is None:
                    raise ValueError("Bridge service is not configured")
                resolved.append(build_bridge_langchain_tool(name, self._bridge_service))
                continue

            custom_tool = await self._custom_tools.get_by_name(name)
            if custom_tool and custom_tool.is_active and custom_tool.tool_type == "http":
                resolved.append(self._build_custom_tool(custom_tool))
                continue

            mcp_tool = await self._mcp_tools.get_tool_by_qualified_name(name)
            if mcp_tool and mcp_tool.is_active:
                resolved.append(self._build_mcp_tool(mcp_tool))

        return resolved

    def _build_custom_tool(self, custom_tool: CustomTool) -> BaseTool:
        async def invoke(custom: CustomTool, arguments: dict) -> str:
            return await invoke_http_custom_tool(custom.config, arguments)

        return build_http_custom_tool(custom_tool, invoke)

    def _build_mcp_tool(self, mcp_tool: MCPTool) -> BaseTool:
        async def invoke(qualified_name: str, arguments: dict) -> str:
            return await self._mcp_service.invoke_tool(qualified_name, arguments)

        return build_mcp_langchain_tool(mcp_tool, invoke)


class BuiltinOnlyToolResolver(ToolResolver):
    """Resolves built-in tools only. Useful for unit tests without a database."""

    def __init__(self) -> None:
        pass

    async def list_catalog(self) -> list[ResolvedToolInfo]:
        return [
            ResolvedToolInfo(name=name, description=tool.description or "", source="builtin")
            for name, tool in sorted(TOOL_CATALOG.items())
        ]

    async def validate_tool_names(self, tool_names: list[str]) -> None:
        if not tool_names:
            return
        unknown = [name for name in tool_names if name not in TOOL_CATALOG]
        if unknown:
            available = ", ".join(sorted(TOOL_CATALOG))
            raise ValueError(f"Unknown tool(s): {', '.join(unknown)}. Available: {available}")

    async def resolve_tools(self, tool_names: list[str] | None) -> list[BaseTool]:
        if not tool_names:
            return []
        await self.validate_tool_names(tool_names)
        return [TOOL_CATALOG[name] for name in tool_names]