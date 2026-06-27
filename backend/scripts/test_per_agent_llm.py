import asyncio

from langchain_core.messages import AIMessage

from app.agents.definitions import AgentDefinition, crew_agent_ids
from app.core.llm import LLMFactory
from app.graphs.multi_agent import create_multi_agent_graph, SupervisorDecision
from app.graphs.single_agent import create_single_agent_graph
from app.models.state import create_initial_state
from app.services.tool_resolver import BuiltinOnlyToolResolver


class MockLLM:
    def __init__(self, name: str = "mock") -> None:
        self.model_name = name
        self.step = 0

    async def ainvoke(self, messages):
        return AIMessage(content=f"from-{self.model_name}")

    def bind_tools(self, tools):
        return self

    def with_structured_output(self, schema):
        steps = [
            SupervisorDecision(next_agent="a1", reasoning="1"),
            SupervisorDecision(next_agent="a2", reasoning="2"),
            SupervisorDecision(next_agent="a3", reasoning="3"),
            SupervisorDecision(next_agent="FINISH", reasoning="done"),
        ]
        parent = self

        class Wrapper:
            async def ainvoke(self, messages):
                decision = steps[min(parent.step, len(steps) - 1)]
                parent.step += 1
                return decision

        return Wrapper()


class MockFactory(LLMFactory):
    def __init__(self) -> None:
        self._cache = {}

    def get(self, model=None):
        return MockLLM(model or "default")

    def get_supervisor(self):
        return MockLLM("supervisor")

    def get_default(self):
        return MockLLM("default")


async def main() -> None:
    factory = MockFactory()
    tool_resolver = BuiltinOnlyToolResolver()
    crew = [
        AgentDefinition("a1", "Researcher", "r", "d", "gpt-4o-mini", ("web_search",)),
        AgentDefinition("a2", "Writer", "r", "d", "gpt-4o", ()),
        AgentDefinition("a3", "Reviewer", "r", "d", "claude-3-5-haiku-20241022", ()),
    ]

    graph = create_multi_agent_graph(factory, crew, tool_resolver=tool_resolver)
    state = create_initial_state(
        user_id="u",
        task_description="t",
        workflow_type="multi_agent",
        task_context={"agents": crew_agent_ids(crew)},
    )
    result = await graph.ainvoke(state)
    assert result["status"] == "completed"
    print("multi_agent per-model: ok")

    graph = create_single_agent_graph(factory, crew[1], tool_resolver=tool_resolver)
    state = create_initial_state(user_id="u", task_description="hello", agent_id="a2")
    result = await graph.ainvoke(state)
    assert result["final_output"] == "from-gpt-4o"
    print("single_agent per-model: ok")


if __name__ == "__main__":
    asyncio.run(main())