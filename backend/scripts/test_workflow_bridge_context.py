"""Unit tests for bridge context setup used by workflow background execution."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.services.bridge_context import (
    get_bridge_tool_context,
    reset_bridge_tool_context,
    set_bridge_context_from_state,
)


def test_set_bridge_context_from_state() -> None:
    token = set_bridge_context_from_state(
        {
            "user_id": "user-1",
            "task_context": {"bridge_device_id": "device-abc"},
        }
    )
    ctx = get_bridge_tool_context()
    assert ctx is not None
    assert ctx.user_id == "user-1"
    assert ctx.device_id == "device-abc"
    reset_bridge_tool_context(token)
    assert get_bridge_tool_context() is None


def test_set_bridge_context_without_device_returns_none() -> None:
    token = set_bridge_context_from_state({"user_id": "user-1"})
    assert token is None
    assert get_bridge_tool_context() is None


if __name__ == "__main__":
    test_set_bridge_context_from_state()
    test_set_bridge_context_without_device_returns_none()
    print("workflow bridge context: PASS")