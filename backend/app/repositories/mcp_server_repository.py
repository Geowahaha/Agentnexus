from datetime import datetime, timezone
from uuid import UUID, uuid4

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.mcp_server import MCPServerORM, MCPToolORM
from app.models.mcp_server import MCPServer, MCPServerCreate, MCPServerUpdate, MCPTool


class MCPServerNotFoundError(KeyError):
    pass


class MCPToolNotFoundError(KeyError):
    pass


class MCPServerRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    @staticmethod
    def _server_to_schema(row: MCPServerORM) -> MCPServer:
        return MCPServer(
            id=str(row.id),
            name=row.name,
            description=row.description,
            owner_id=str(row.owner_id),
            transport=row.transport,
            config=dict(row.config or {}),
            is_active=row.is_active,
            created_at=row.created_at,
            updated_at=row.updated_at,
        )

    @staticmethod
    def _tool_to_schema(row: MCPToolORM) -> MCPTool:
        return MCPTool(
            id=str(row.id),
            mcp_server_id=str(row.mcp_server_id),
            tool_name=row.tool_name,
            qualified_name=row.qualified_name,
            description=row.description,
            input_schema=dict(row.input_schema or {}),
            is_active=row.is_active,
            created_at=row.created_at,
            updated_at=row.updated_at,
        )

    @staticmethod
    def qualified_name(server_name: str, tool_name: str) -> str:
        return f"mcp.{server_name}.{tool_name}"

    async def create_server(self, data: MCPServerCreate, *, owner_id: str) -> MCPServer:
        now = datetime.now(timezone.utc)
        row = MCPServerORM(
            id=uuid4(),
            name=data.name,
            description=data.description,
            owner_id=UUID(owner_id),
            transport=data.transport,
            config=data.config,
            is_active=data.is_active,
            created_at=now,
            updated_at=now,
        )
        self._session.add(row)
        await self._session.commit()
        await self._session.refresh(row)
        return self._server_to_schema(row)

    async def get_server_by_id(self, server_id: str) -> MCPServer | None:
        result = await self._session.execute(
            select(MCPServerORM).where(MCPServerORM.id == UUID(server_id))
        )
        row = result.scalar_one_or_none()
        return self._server_to_schema(row) if row else None

    async def get_server_by_name(self, name: str) -> MCPServer | None:
        result = await self._session.execute(select(MCPServerORM).where(MCPServerORM.name == name))
        row = result.scalar_one_or_none()
        return self._server_to_schema(row) if row else None

    async def list_servers(
        self,
        *,
        active_only: bool = True,
        owner_id: str | None = None,
    ) -> list[MCPServer]:
        query = select(MCPServerORM).order_by(MCPServerORM.created_at.asc())
        if active_only:
            query = query.where(MCPServerORM.is_active.is_(True))
        if owner_id:
            query = query.where(MCPServerORM.owner_id == UUID(owner_id))
        result = await self._session.execute(query)
        return [self._server_to_schema(row) for row in result.scalars().all()]

    async def update_server(self, server_id: str, data: MCPServerUpdate) -> MCPServer | None:
        result = await self._session.execute(
            select(MCPServerORM).where(MCPServerORM.id == UUID(server_id))
        )
        row = result.scalar_one_or_none()
        if row is None:
            return None
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(row, field, value)
        row.updated_at = datetime.now(timezone.utc)
        await self._session.commit()
        await self._session.refresh(row)
        return self._server_to_schema(row)

    async def delete_server(self, server_id: str) -> bool:
        result = await self._session.execute(
            delete(MCPServerORM).where(MCPServerORM.id == UUID(server_id)).returning(MCPServerORM.id)
        )
        if result.scalar_one_or_none() is None:
            return False
        await self._session.commit()
        return True

    async def list_tools(
        self,
        *,
        server_id: str | None = None,
        active_only: bool = True,
    ) -> list[MCPTool]:
        query = select(MCPToolORM).order_by(MCPToolORM.qualified_name.asc())
        if server_id:
            query = query.where(MCPToolORM.mcp_server_id == UUID(server_id))
        if active_only:
            query = query.where(MCPToolORM.is_active.is_(True))
        result = await self._session.execute(query)
        return [self._tool_to_schema(row) for row in result.scalars().all()]

    async def get_tool_by_qualified_name(self, qualified_name: str) -> MCPTool | None:
        result = await self._session.execute(
            select(MCPToolORM).where(MCPToolORM.qualified_name == qualified_name)
        )
        row = result.scalar_one_or_none()
        return self._tool_to_schema(row) if row else None

    async def get_tool_with_server(self, qualified_name: str) -> tuple[MCPTool, MCPServer] | None:
        result = await self._session.execute(
            select(MCPToolORM, MCPServerORM)
            .join(MCPServerORM, MCPToolORM.mcp_server_id == MCPServerORM.id)
            .where(MCPToolORM.qualified_name == qualified_name)
        )
        row = result.one_or_none()
        if row is None:
            return None
        tool_row, server_row = row
        return self._tool_to_schema(tool_row), self._server_to_schema(server_row)

    async def replace_tools_for_server(
        self,
        server: MCPServer,
        remote_tools: list[dict],
    ) -> list[MCPTool]:
        server_uuid = UUID(server.id)
        await self._session.execute(
            delete(MCPToolORM).where(MCPToolORM.mcp_server_id == server_uuid)
        )

        now = datetime.now(timezone.utc)
        rows: list[MCPToolORM] = []
        for item in remote_tools:
            tool_name = item["tool_name"]
            row = MCPToolORM(
                id=uuid4(),
                mcp_server_id=server_uuid,
                tool_name=tool_name,
                qualified_name=self.qualified_name(server.name, tool_name),
                description=item.get("description", ""),
                input_schema=item.get("input_schema", {}),
                is_active=True,
                created_at=now,
                updated_at=now,
            )
            self._session.add(row)
            rows.append(row)

        await self._session.commit()
        for row in rows:
            await self._session.refresh(row)
        return [self._tool_to_schema(row) for row in rows]