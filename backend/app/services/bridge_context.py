from contextvars import ContextVar
from dataclasses import dataclass


@dataclass(frozen=True)
class BridgeToolContext:
    user_id: str
    device_id: str


bridge_tool_context: ContextVar[BridgeToolContext | None] = ContextVar(
    "bridge_tool_context",
    default=None,
)


def get_bridge_tool_context() -> BridgeToolContext | None:
    return bridge_tool_context.get()


def set_bridge_tool_context(context: BridgeToolContext | None):
    if context is None:
        return bridge_tool_context.set(None)
    return bridge_tool_context.set(context)


def reset_bridge_tool_context(token) -> None:
    bridge_tool_context.reset(token)


def set_bridge_context_from_state(state: dict):
    device_id = (state.get("task_context") or {}).get("bridge_device_id")
    if not device_id:
        return None
    return set_bridge_tool_context(
        BridgeToolContext(user_id=state["user_id"], device_id=str(device_id))
    )