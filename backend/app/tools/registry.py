from dataclasses import dataclass

from langchain_core.tools import BaseTool

from app.tools.builtins import (
    calculator,
    current_datetime,
    keyword_extract,
    web_search,
    word_count,
)

TOOL_CATALOG: dict[str, BaseTool] = {
    "calculator": calculator,
    "current_datetime": current_datetime,
    "word_count": word_count,
    "keyword_extract": keyword_extract,
    "web_search": web_search,
}


@dataclass(frozen=True)
class ToolInfo:
    name: str
    description: str


def list_tool_catalog() -> list[ToolInfo]:
    return [
        ToolInfo(name=name, description=tool.description or "")
        for name, tool in sorted(TOOL_CATALOG.items())
    ]


def validate_tool_names(tool_names: list[str]) -> None:
    unknown = [name for name in tool_names if name not in TOOL_CATALOG]
    if unknown:
        available = ", ".join(sorted(TOOL_CATALOG))
        raise ValueError(f"Unknown tool(s): {', '.join(unknown)}. Available: {available}")


def resolve_tools(tool_names: list[str] | None) -> list[BaseTool]:
    if not tool_names:
        return []
    validate_tool_names(tool_names)
    return [TOOL_CATALOG[name] for name in tool_names]