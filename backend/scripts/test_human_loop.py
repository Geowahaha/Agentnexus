import asyncio

from langchain_core.messages import AIMessage
from langgraph.checkpoint.memory import MemorySaver
from langgraph.types import Command

from app.agents.definitions import AgentDefinition
from app.core.llm import LLMFactory
from app.graphs.single_agent import create_single_agent_graph
from app.models.state import create_initial_state
from app.services.tool_resolver import BuiltinOnlyToolResolver


class MockLLM:
    def __init__(self, model: str = "gpt-4o-mini") -> None:
        self.model_name = model

    async def ainvoke(self, messages):
        return AIMessage(content="Draft output for human review")

    def bind_tools(self, tools):
        return self

    def with_structured_output(self, schema):
        return self


class MockFactory(LLMFactory):
    def __init__(self) -> None:
        self._cache = {}

    def get(self, model=None):
        return MockLLM(model or "gpt-4o-mini")

    def get_supervisor(self):
        return self.get()

    def get_default(self):
        return self.get()


class MockRegistry:
    async def get_agent(self, agent_id: str):
        raise NotImplementedError

    async def list_agents(self, active_only: bool = True):
        return []


async def main() -> None:
    checkpointer = MemorySaver()
    tool_resolver = BuiltinOnlyToolResolver()

    graph = create_single_agent_graph(MockFactory(), tool_resolver=tool_resolver, checkpointer=checkpointer)
    state = create_initial_state(
        user_id="user-1",
        task_description="Write a tagline",
        workflow_type="single_agent",
        task_context={"require_human_approval": True},
    )
    workflow_id = state["workflow_id"]
    config = {"configurable": {"thread_id": workflow_id}}

    await graph.ainvoke(state, config)
    snapshot = await graph.aget_state(config)
    assert snapshot.tasks and snapshot.tasks[0].interrupts, "Expected interrupt"
    print("interrupt created: ok")

    resumed = await graph.ainvoke(Command(resume="approve"), config)
    assert resumed["status"] == "completed"
    assert resumed["final_output"] == "Draft output for human review"
    print("resume approve: ok")

    state2 = create_initial_state(
        user_id="user-2",
        task_description="Write a headline",
        workflow_type="single_agent",
        task_context={"require_human_approval": True},
    )
    workflow_id2 = state2["workflow_id"]
    config2 = {"configurable": {"thread_id": workflow_id2}}
    await graph.ainvoke(state2, config2)
    revised = await graph.ainvoke(Command(resume="Make it shorter and bolder"), config2)
    assert revised["status"] == "running"
    print("resume revision: ok")

    final = await graph.ainvoke(Command(resume="approve"), config2)
    assert final["status"] == "completed"
    print("revision then approve: ok")


if __name__ == "__main__":
    asyncio.run(main())