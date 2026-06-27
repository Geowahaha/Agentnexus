"""Run after PostgreSQL is available and migrations are applied."""

import asyncio
import sys

from httpx import ASGITransport, AsyncClient
from langchain_core.messages import AIMessage

from app.agents.definitions import resolve_crew
from app.core.database import async_session_maker
from app.core.llm import LLMFactory
from langgraph.checkpoint.memory import MemorySaver
from app.graphs.multi_agent import create_multi_agent_graph, SupervisorDecision
from app.main import app
from app.models.state import create_initial_state
from app.repositories.agent_repository import AgentRepository
from app.services.agent_registry import AgentRegistry
from app.services.tool_resolver import BuiltinOnlyToolResolver


class MockLLM:
    def __init__(self, crew_ids: list[str], model: str = "mock") -> None:
        self.crew = crew_ids
        self.model_name = model
        self.step = 0
        self.supervisor_steps = [
            SupervisorDecision(next_agent=crew_ids[0], reasoning="first"),
            SupervisorDecision(next_agent=crew_ids[1], reasoning="second"),
            SupervisorDecision(next_agent=crew_ids[2], reasoning="third"),
            SupervisorDecision(next_agent="FINISH", reasoning="done"),
        ]

    async def ainvoke(self, messages):
        text = messages[-1].content
        if "As the Researcher" in text:
            return AIMessage(content="Research complete")
        if "As the Writer" in text:
            return AIMessage(content="Draft complete")
        if "As the Reviewer" in text:
            return AIMessage(content="Review complete")
        return AIMessage(content="unknown")

    def bind_tools(self, tools):
        return self

    def with_structured_output(self, schema):
        parent = self

        class Wrapper:
            async def ainvoke(self, messages):
                decision = parent.supervisor_steps[min(parent.step, len(parent.supervisor_steps) - 1)]
                parent.step += 1
                return decision

        return Wrapper()


class MockFactory(LLMFactory):
    def __init__(self, crew_ids: list[str]) -> None:
        self._cache = {}
        self._crew_ids = crew_ids

    def get(self, model=None):
        return MockLLM(self._crew_ids, model or "default")

    def get_supervisor(self):
        return MockLLM(self._crew_ids, "supervisor")

    def get_default(self):
        return MockLLM(self._crew_ids, "default")


async def main() -> None:
    async with async_session_maker() as session:
        tool_resolver = BuiltinOnlyToolResolver()
        registry = AgentRegistry(AgentRepository(session), tool_resolver)
        agents = await registry.list_agents()
        assert len(agents) >= 3, "Expected seeded agents from migration"
        print(f"registry list: {len(agents)} agents")

        crew = await resolve_crew(None, registry)
        crew_ids = [agent.agent_id for agent in crew]
        checkpointer = MemorySaver()
        graph = create_multi_agent_graph(
            MockFactory(crew_ids),
            crew,
            tool_resolver=tool_resolver,
            checkpointer=checkpointer,
        )
        state = create_initial_state(
            user_id="test-user",
            task_description="Write a short summary",
            workflow_type="multi_agent",
            task_context={"agents": crew_ids},
        )
        config = {"configurable": {"thread_id": state["workflow_id"]}}
        result = await graph.ainvoke(state, config)
        assert result["status"] == "completed", result
        print("multi_agent workflow: ok")

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/agents")
        assert response.status_code == 200, response.text
        payload = response.json()
        assert len(payload) >= 3
        print(f"agents api list: {len(payload)} agents")

    print("integration: ok")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as exc:
        print(f"integration failed: {exc}", file=sys.stderr)
        raise