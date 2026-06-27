import json

from langchain_core.tools import BaseTool, StructuredTool

from app.services.bridge_context import get_bridge_tool_context
from app.services.bridge_service import BridgeService
from app.tools.bridge_catalog import BRIDGE_TOOL_DEFINITIONS
from app.tools.factories import schema_to_model


def build_bridge_langchain_tool(name: str, bridge_service: BridgeService) -> BaseTool:
    definition = BRIDGE_TOOL_DEFINITIONS[name]
    schema = definition["schema"]
    args_model = schema_to_model(f"{name.replace('.', '_')}_args", schema)

    async def invoke(**kwargs) -> str:
        ctx = get_bridge_tool_context()
        if ctx is None:
            return json.dumps(
                {
                    "ok": False,
                    "error": "No local machine connected. Pair a device at /bridge and enable local hands for this run.",
                }
            )

        tool_id = name.removeprefix("bridge.")
        try:
            result = await bridge_service.invoke_tool(
                user_id=ctx.user_id,
                device_id=ctx.device_id,
                tool=tool_id,
                args=kwargs,
            )
        except KeyError:
            return json.dumps({"ok": False, "error": "Bridge device not found or revoked"})
        except ValueError as exc:
            return json.dumps({"ok": False, "error": str(exc)})
        except Exception as exc:
            return json.dumps({"ok": False, "error": str(exc)})
        return json.dumps(result)

    return StructuredTool.from_function(
        coroutine=invoke,
        name=name,
        description=definition["description"],
        args_schema=args_model,
    )