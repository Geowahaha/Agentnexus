from dataclasses import dataclass

from app.models.agent import Agent
from app.services.agent_registry import AgentNotFoundError, AgentRegistry

FINISH_AGENT = "FINISH"
MAX_SUPERVISOR_STEPS = 10


@dataclass(frozen=True)
class AgentDefinition:
    agent_id: str
    name: str
    role: str
    description: str
    llm_model: str
    tools: tuple[str, ...] = ()


def agent_to_definition(agent: Agent) -> AgentDefinition:
    return AgentDefinition(
        agent_id=agent.id,
        name=agent.name,
        role=agent.role,
        description=agent.description,
        llm_model=agent.llm_model,
        tools=tuple(agent.tools),
    )


async def resolve_crew(
    agent_ids: list[str] | None,
    registry: AgentRegistry,
) -> list[AgentDefinition]:
    if agent_ids:
        missing: list[str] = []
        crew: list[AgentDefinition] = []
        for agent_id in agent_ids:
            try:
                agent = await registry.get_agent(agent_id)
                crew.append(agent_to_definition(agent))
            except AgentNotFoundError:
                missing.append(agent_id)
        if missing:
            raise ValueError(f"Unknown agent(s): {', '.join(missing)}")
        return crew

    agents = await registry.list_agents(active_only=True)
    return [agent_to_definition(agent) for agent in agents]


def crew_agent_ids(crew: list[AgentDefinition]) -> list[str]:
    return [agent.agent_id for agent in crew]