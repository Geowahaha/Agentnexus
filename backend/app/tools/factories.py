import json
from typing import Any

import httpx
from langchain_core.tools import BaseTool, StructuredTool
from pydantic import BaseModel, Field, create_model

from app.models.custom_tool import CustomTool
from app.models.mcp_server import MCPTool


def _json_type_to_python(prop: dict) -> type:
    raw = prop.get("type", "string")
    if isinstance(raw, list):
        raw = next((item for item in raw if item != "null"), "string")
    mapping = {
        "string": str,
        "integer": int,
        "number": float,
        "boolean": bool,
        "object": dict,
        "array": list,
    }
    return mapping.get(raw, str)


def schema_to_model(name: str, schema: dict) -> type[BaseModel]:
    properties = schema.get("properties", {})
    if not properties:
        return create_model(name)

    required = set(schema.get("required", []))
    fields: dict[str, tuple[Any, Any]] = {}
    for prop_name, prop_def in properties.items():
        py_type = _json_type_to_python(prop_def)
        if prop_name in required:
            fields[prop_name] = (py_type, Field(description=prop_def.get("description", "")))
        else:
            fields[prop_name] = (
                py_type | None,
                Field(default=None, description=prop_def.get("description", "")),
            )
    return create_model(name, **fields)


async def invoke_http_custom_tool(config: dict, arguments: dict) -> str:
    url = config.get("url")
    if not url:
        raise ValueError("HTTP custom tool config requires 'url'")

    method = str(config.get("method", "POST")).upper()
    headers = dict(config.get("headers") or {})
    timeout = float(config.get("timeout_seconds", 30))
    mapping = config.get("arg_mapping", "body")

    async with httpx.AsyncClient(timeout=timeout) as client:
        if mapping == "query":
            response = await client.request(method, url, params=arguments, headers=headers)
        else:
            response = await client.request(method, url, json=arguments, headers=headers)
        response.raise_for_status()
        content_type = response.headers.get("content-type", "")
        if "application/json" in content_type:
            return json.dumps(response.json())
        return response.text


def build_http_custom_tool(
    custom_tool: CustomTool,
    invoke_fn,
) -> BaseTool:
    schema = custom_tool.config.get("input_schema", {})
    args_schema = schema_to_model(f"{custom_tool.name}_args", schema) if schema else None

    async def _run(**kwargs) -> str:
        payload = {key: value for key, value in kwargs.items() if value is not None}
        return await invoke_fn(custom_tool, payload)

    return StructuredTool.from_function(
        coroutine=_run,
        name=custom_tool.name,
        description=custom_tool.description,
        args_schema=args_schema,
    )


def build_mcp_langchain_tool(
    mcp_tool: MCPTool,
    invoke_fn,
) -> BaseTool:
    args_schema = schema_to_model(
        f"{mcp_tool.qualified_name.replace('.', '_')}_args",
        mcp_tool.input_schema,
    )

    async def _run(**kwargs) -> str:
        payload = {key: value for key, value in kwargs.items() if value is not None}
        return await invoke_fn(mcp_tool.qualified_name, payload)

    return StructuredTool.from_function(
        coroutine=_run,
        name=mcp_tool.qualified_name,
        description=mcp_tool.description,
        args_schema=args_schema,
    )