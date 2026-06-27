from decimal import Decimal

from fastapi import APIRouter, Depends, Query

from app.core.deps import get_agent_registry
from app.models.agent import Agent
from app.services.agent_registry import AgentRegistry

router = APIRouter()


@router.get("/agents", response_model=list[Agent])
async def list_marketplace_agents(
    active_only: bool = Query(default=True),
    owner_id: str | None = Query(default=None),
    category: str | None = Query(default=None),
    max_price: Decimal | None = Query(default=None, ge=0),
    registry: AgentRegistry = Depends(get_agent_registry),
) -> list[Agent]:
    return await registry.list_marketplace_agents(
        active_only=active_only,
        owner_id=owner_id,
        category=category,
        max_price=max_price,
    )