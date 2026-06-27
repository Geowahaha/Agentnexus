from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.auth.dependencies import get_current_user, require_resource_owner
from app.auth.models import User
from app.core.deps import get_custom_tool_repository
from app.models.custom_tool import CustomTool, CustomToolCreate, CustomToolUpdate
from app.repositories.custom_tool_repository import CustomToolRepository

router = APIRouter()


@router.post("", response_model=CustomTool, status_code=status.HTTP_201_CREATED)
async def create_custom_tool(
    payload: CustomToolCreate,
    current_user: User = Depends(get_current_user),
    repository: CustomToolRepository = Depends(get_custom_tool_repository),
) -> CustomTool:
    if payload.tool_type != "http":
        raise HTTPException(status_code=400, detail="Only HTTP custom tools are supported via this endpoint.")
    existing = await repository.get_by_name(payload.name)
    if existing is not None:
        raise HTTPException(status_code=409, detail=f"Custom tool '{payload.name}' already exists.")
    return await repository.create(payload, owner_id=current_user.id)


@router.get("", response_model=list[CustomTool])
async def list_custom_tools(
    active_only: bool = Query(default=True),
    owner_id: str | None = Query(default=None),
    repository: CustomToolRepository = Depends(get_custom_tool_repository),
) -> list[CustomTool]:
    return await repository.list_all(active_only=active_only, owner_id=owner_id)


@router.get("/{tool_id}", response_model=CustomTool)
async def get_custom_tool(
    tool_id: str,
    repository: CustomToolRepository = Depends(get_custom_tool_repository),
) -> CustomTool:
    tool = await repository.get_by_id(tool_id)
    if tool is None:
        raise HTTPException(status_code=404, detail=f"Custom tool '{tool_id}' not found")
    return tool


@router.put("/{tool_id}", response_model=CustomTool)
async def update_custom_tool(
    tool_id: str,
    payload: CustomToolUpdate,
    current_user: User = Depends(get_current_user),
    repository: CustomToolRepository = Depends(get_custom_tool_repository),
) -> CustomTool:
    tool = await repository.get_by_id(tool_id)
    if tool is None:
        raise HTTPException(status_code=404, detail=f"Custom tool '{tool_id}' not found")
    require_resource_owner(tool.owner_id, current_user)
    updated = await repository.update(tool_id, payload)
    assert updated is not None
    return updated


@router.delete("/{tool_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_custom_tool(
    tool_id: str,
    current_user: User = Depends(get_current_user),
    repository: CustomToolRepository = Depends(get_custom_tool_repository),
) -> None:
    tool = await repository.get_by_id(tool_id)
    if tool is None:
        raise HTTPException(status_code=404, detail=f"Custom tool '{tool_id}' not found")
    require_resource_owner(tool.owner_id, current_user)
    await repository.delete(tool_id)