from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.auth.dependencies import get_current_user, get_optional_user
from app.auth.models import User
from app.core.deps import get_agent_registry, get_portfolio_service
from app.models.portfolio import AgentProfile, PortfolioItem, PortfolioItemCreate, PortfolioItemUpdate
from app.services.agent_registry import AgentNotFoundError, AgentRegistry
from app.services.portfolio_service import PortfolioService

router = APIRouter()


@router.get("/{agent_id}/profile", response_model=AgentProfile)
async def get_agent_profile(
    agent_id: str,
    include_private: bool = Query(default=False),
    current_user: User | None = Depends(get_optional_user),
    registry: AgentRegistry = Depends(get_agent_registry),
    service: PortfolioService = Depends(get_portfolio_service),
) -> AgentProfile:
    try:
        agent = await registry.get_agent(agent_id)
    except AgentNotFoundError as exc:
        raise HTTPException(status_code=404, detail=f"Agent '{agent_id}' not found") from exc

    show_private = False
    if include_private and current_user and agent.owner_id == current_user.id:
        show_private = True

    return await service.get_profile(agent_id, include_private=show_private)


@router.post("/{agent_id}/portfolio", response_model=PortfolioItem, status_code=status.HTTP_201_CREATED)
async def add_portfolio_item(
    agent_id: str,
    payload: PortfolioItemCreate,
    current_user: User = Depends(get_current_user),
    service: PortfolioService = Depends(get_portfolio_service),
) -> PortfolioItem:
    try:
        return await service.create_from_workflow(agent_id, payload, current_user=current_user)
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.put("/{agent_id}/portfolio/{item_id}", response_model=PortfolioItem)
async def update_portfolio_item(
    agent_id: str,
    item_id: str,
    payload: PortfolioItemUpdate,
    current_user: User = Depends(get_current_user),
    service: PortfolioService = Depends(get_portfolio_service),
) -> PortfolioItem:
    try:
        return await service.update_item(agent_id, item_id, payload, current_user=current_user)
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.delete("/{agent_id}/portfolio/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_portfolio_item(
    agent_id: str,
    item_id: str,
    current_user: User = Depends(get_current_user),
    service: PortfolioService = Depends(get_portfolio_service),
) -> None:
    try:
        await service.delete_item(agent_id, item_id, current_user=current_user)
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc