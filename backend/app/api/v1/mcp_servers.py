from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.auth.dependencies import get_current_user, require_resource_owner
from app.auth.models import User
from app.core.deps import get_mcp_server_repository, get_mcp_service
from app.models.mcp_server import MCPServer, MCPServerCreate, MCPServerUpdate, MCPTool
from app.repositories.mcp_server_repository import MCPServerNotFoundError, MCPServerRepository
from app.services.mcp_service import MCPService

router = APIRouter()


@router.post("", response_model=MCPServer, status_code=status.HTTP_201_CREATED)
async def create_mcp_server(
    payload: MCPServerCreate,
    current_user: User = Depends(get_current_user),
    repository: MCPServerRepository = Depends(get_mcp_server_repository),
) -> MCPServer:
    existing = await repository.get_server_by_name(payload.name)
    if existing is not None:
        raise HTTPException(status_code=409, detail=f"MCP server '{payload.name}' already exists.")
    return await repository.create_server(payload, owner_id=current_user.id)


@router.get("", response_model=list[MCPServer])
async def list_mcp_servers(
    active_only: bool = Query(default=True),
    owner_id: str | None = Query(default=None),
    repository: MCPServerRepository = Depends(get_mcp_server_repository),
) -> list[MCPServer]:
    return await repository.list_servers(active_only=active_only, owner_id=owner_id)


@router.get("/{server_id}", response_model=MCPServer)
async def get_mcp_server(
    server_id: str,
    repository: MCPServerRepository = Depends(get_mcp_server_repository),
) -> MCPServer:
    server = await repository.get_server_by_id(server_id)
    if server is None:
        raise HTTPException(status_code=404, detail=f"MCP server '{server_id}' not found")
    return server


@router.put("/{server_id}", response_model=MCPServer)
async def update_mcp_server(
    server_id: str,
    payload: MCPServerUpdate,
    current_user: User = Depends(get_current_user),
    repository: MCPServerRepository = Depends(get_mcp_server_repository),
) -> MCPServer:
    server = await repository.get_server_by_id(server_id)
    if server is None:
        raise HTTPException(status_code=404, detail=f"MCP server '{server_id}' not found")
    require_resource_owner(server.owner_id, current_user)
    updated = await repository.update_server(server_id, payload)
    assert updated is not None
    return updated


@router.delete("/{server_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_mcp_server(
    server_id: str,
    current_user: User = Depends(get_current_user),
    repository: MCPServerRepository = Depends(get_mcp_server_repository),
) -> None:
    server = await repository.get_server_by_id(server_id)
    if server is None:
        raise HTTPException(status_code=404, detail=f"MCP server '{server_id}' not found")
    require_resource_owner(server.owner_id, current_user)
    await repository.delete_server(server_id)


@router.get("/{server_id}/tools", response_model=list[MCPTool])
async def list_mcp_server_tools(
    server_id: str,
    active_only: bool = Query(default=True),
    repository: MCPServerRepository = Depends(get_mcp_server_repository),
) -> list[MCPTool]:
    server = await repository.get_server_by_id(server_id)
    if server is None:
        raise HTTPException(status_code=404, detail=f"MCP server '{server_id}' not found")
    return await repository.list_tools(server_id=server_id, active_only=active_only)


@router.post("/{server_id}/sync-tools", response_model=list[MCPTool])
async def sync_mcp_server_tools(
    server_id: str,
    current_user: User = Depends(get_current_user),
    repository: MCPServerRepository = Depends(get_mcp_server_repository),
    mcp_service: MCPService = Depends(get_mcp_service),
) -> list[MCPTool]:
    server = await repository.get_server_by_id(server_id)
    if server is None:
        raise HTTPException(status_code=404, detail=f"MCP server '{server_id}' not found")
    require_resource_owner(server.owner_id, current_user)
    try:
        return await mcp_service.sync_tools(server_id)
    except MCPServerNotFoundError as exc:
        raise HTTPException(status_code=404, detail=f"MCP server '{server_id}' not found") from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"MCP sync failed: {exc}") from exc