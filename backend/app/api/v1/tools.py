from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.core.deps import get_tool_resolver
from app.services.tool_resolver import ToolResolver

router = APIRouter()


class ToolResponse(BaseModel):
    name: str
    description: str
    source: str


@router.get("", response_model=list[ToolResponse])
async def list_tools(
    tool_resolver: ToolResolver = Depends(get_tool_resolver),
) -> list[ToolResponse]:
    return [
        ToolResponse(name=item.name, description=item.description, source=item.source)
        for item in await tool_resolver.list_catalog()
    ]