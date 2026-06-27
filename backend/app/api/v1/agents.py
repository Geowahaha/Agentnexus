from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.auth.dependencies import get_current_user, require_resource_owner
from app.auth.models import User
from app.core.deps import get_agent_registry, get_user_repository
from app.models.agent import Agent, AgentCreate, AgentDetail, AgentUpdate
from app.repositories.user_repository import UserRepository
from app.services.agent_registry import AgentNotFoundError, AgentRegistry

router = APIRouter()


@router.post("", response_model=Agent, status_code=status.HTTP_201_CREATED)
async def create_agent(
    payload: AgentCreate,
    current_user: User = Depends(get_current_user),
    registry: AgentRegistry = Depends(get_agent_registry),
) -> Agent:
    return await registry.create_agent(payload, owner_id=current_user.id)


@router.get("", response_model=list[Agent])
async def list_agents(
    active_only: bool = Query(default=True),
    registry: AgentRegistry = Depends(get_agent_registry),
) -> list[Agent]:
    return await registry.list_agents(active_only=active_only)


@router.get("/{agent_id}", response_model=AgentDetail)
async def get_agent(
    agent_id: str,
    registry: AgentRegistry = Depends(get_agent_registry),
    user_repository: UserRepository = Depends(get_user_repository),
) -> AgentDetail:
    try:
        agent = await registry.get_agent(agent_id)
    except AgentNotFoundError as exc:
        raise HTTPException(status_code=404, detail=f"Agent '{agent_id}' not found") from exc

    owner_name = await user_repository.get_full_name_by_id(agent.owner_id)

    return AgentDetail(**agent.model_dump(), owner_name=owner_name)


@router.put("/{agent_id}", response_model=Agent)
async def update_agent(
    agent_id: str,
    payload: AgentUpdate,
    current_user: User = Depends(get_current_user),
    registry: AgentRegistry = Depends(get_agent_registry),
) -> Agent:
    try:
        agent = await registry.get_agent(agent_id)
        require_resource_owner(agent.owner_id, current_user)
        return await registry.update_agent(agent_id, payload)
    except AgentNotFoundError as exc:
        raise HTTPException(status_code=404, detail=f"Agent '{agent_id}' not found") from exc


@router.delete("/{agent_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_agent(
    agent_id: str,
    current_user: User = Depends(get_current_user),
    registry: AgentRegistry = Depends(get_agent_registry),
) -> None:
    try:
        agent = await registry.get_agent(agent_id)
        require_resource_owner(agent.owner_id, current_user)
        await registry.delete_agent(agent_id)
    except AgentNotFoundError as exc:
        raise HTTPException(status_code=404, detail=f"Agent '{agent_id}' not found") from exc