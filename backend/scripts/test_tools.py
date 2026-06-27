import asyncio

from langchain_core.messages import AIMessage, HumanMessage, ToolMessage

from app.agents.definitions import AgentDefinition
from app.core.llm import LLMFactory
from app.graphs.agent_runner import invoke_agent_with_tools
from app.models.state import create_initial_state
from app.tools.registry import list_tool_catalog, resolve_tools, validate_tool_names
from app.services.tool_resolver import BuiltinOnlyToolResolver


class ToolCallingLLM:
    def __init__(self) -> None:
        self.calls = 0

    async def ainvoke(self, messages):
        self.calls += 1
        if self.calls == 1:
            return AIMessage(
                content="",
                tool_calls=[
                    {
                        "name": "calculator",
                        "args": {"expression": "2 + 2"},
                        "id": "call-1",
                        "type": "tool_call",
                    }
                ],
            )
        return AIMessage(content="The answer is 4")

    def bind_tools(self, tools):
        return self

    def with_structured_output(self, schema):
        return self


async def main() -> None:
    validate_tool_names(["calculator"])
    try:
        validate_tool_names(["unknown_tool"])
        raise AssertionError("expected validation error")
    except ValueError:
        pass

    catalog = list_tool_catalog()
    assert any(item.name == "web_search" for item in catalog)
    assert len(resolve_tools(["calculator", "word_count"])) == 2
    print(f"tool catalog: {len(catalog)} tools")

    tool_resolver = BuiltinOnlyToolResolver()
    state = create_initial_state(user_id="u1", task_description="test")
    response, emitted, metadata = await invoke_agent_with_tools(
        ToolCallingLLM(),
        [HumanMessage(content="What is 2+2?")],
        ["calculator"],
        model="gpt-4o-mini",
        state=state,
        tool_resolver=tool_resolver,
    )
    assert response.content == "The answer is 4"
    assert metadata["tool_calls"][0]["tool"] == "calculator"
    assert metadata["tool_calls"][0]["output"] in {"4", "4.0"}
    assert len(emitted) == 3
    print("tool execution loop: ok")

    agent = AgentDefinition(
        agent_id="a1",
        name="Researcher",
        role="Research role",
        description="desc",
        llm_model="gpt-4o-mini",
        tools=("calculator", "web_search"),
    )
    assert agent.tools == ("calculator", "web_search")
    print("agent definition tools: ok")


if __name__ == "__main__":
    asyncio.run(main())