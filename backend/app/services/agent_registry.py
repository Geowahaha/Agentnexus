from decimal import Decimal

from app.models.agent import Agent, AgentCreate, AgentUpdate
from app.repositories.agent_repository import AgentRepository
from app.services.tool_resolver import ToolResolver


class AgentNotFoundError(KeyError):
    """Raised when an agent ID does not exist in the registry."""


class AgentRegistry:
    """Agent registry backed by PostgreSQL via repository layer."""

    def __init__(self, repository: AgentRepository, tool_resolver: ToolResolver) -> None:
        self._repository = repository
        self._tool_resolver = tool_resolver

    async def create_agent(self, agent_data: AgentCreate, *, owner_id: str) -> Agent:
        await self._tool_resolver.validate_tool_names(agent_data.tools)
        return await self._repository.create(agent_data, owner_id=owner_id)

    async def get_agent(self, agent_id: str) -> Agent:
        agent = await self._repository.get_by_id(agent_id)
        if agent is None:
            raise AgentNotFoundError(agent_id)
        return agent

    async def list_agents(self, active_only: bool = True) -> list[Agent]:
        return await self._repository.list_all(active_only=active_only)

    async def list_marketplace_agents(
        self,
        *,
        active_only: bool = True,
        owner_id: str | None = None,
        category: str | None = None,
        max_price: Decimal | None = None,
    ) -> list[Agent]:
        return await self._repository.list_all(
            active_only=active_only,
            owner_id=owner_id,
            category=category,
            max_price=max_price,
        )

    async def update_agent(self, agent_id: str, update_data: AgentUpdate) -> Agent:
        if update_data.tools is not None:
            await self._tool_resolver.validate_tool_names(update_data.tools)
        agent = await self._repository.update(agent_id, update_data)
        if agent is None:
            raise AgentNotFoundError(agent_id)
        return agent

    async def delete_agent(self, agent_id: str) -> None:
        deleted = await self._repository.delete(agent_id)
        if not deleted:
            raise AgentNotFoundError(agent_id)


