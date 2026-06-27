from datetime import datetime, timezone
from uuid import UUID, uuid4

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.custom_tool import CustomToolORM
from app.models.custom_tool import CustomTool, CustomToolCreate, CustomToolUpdate


class CustomToolNotFoundError(KeyError):
    pass


class CustomToolRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    @staticmethod
    def _to_schema(row: CustomToolORM) -> CustomTool:
        return CustomTool(
            id=str(row.id),
            name=row.name,
            description=row.description,
            owner_id=str(row.owner_id),
            tool_type=row.tool_type,
            config=dict(row.config or {}),
            is_active=row.is_active,
            created_at=row.created_at,
            updated_at=row.updated_at,
        )

    async def create(self, data: CustomToolCreate, *, owner_id: str) -> CustomTool:
        now = datetime.now(timezone.utc)
        row = CustomToolORM(
            id=uuid4(),
            name=data.name,
            description=data.description,
            owner_id=UUID(owner_id),
            tool_type=data.tool_type,
            config=data.config,
            is_active=data.is_active,
            created_at=now,
            updated_at=now,
        )
        self._session.add(row)
        await self._session.commit()
        await self._session.refresh(row)
        return self._to_schema(row)

    async def get_by_id(self, tool_id: str) -> CustomTool | None:
        result = await self._session.execute(select(CustomToolORM).where(CustomToolORM.id == UUID(tool_id)))
        row = result.scalar_one_or_none()
        return self._to_schema(row) if row else None

    async def get_by_name(self, name: str) -> CustomTool | None:
        result = await self._session.execute(select(CustomToolORM).where(CustomToolORM.name == name))
        row = result.scalar_one_or_none()
        return self._to_schema(row) if row else None

    async def list_all(self, *, active_only: bool = True, owner_id: str | None = None) -> list[CustomTool]:
        query = select(CustomToolORM).order_by(CustomToolORM.created_at.asc())
        if active_only:
            query = query.where(CustomToolORM.is_active.is_(True))
        if owner_id:
            query = query.where(CustomToolORM.owner_id == UUID(owner_id))
        result = await self._session.execute(query)
        return [self._to_schema(row) for row in result.scalars().all()]

    async def update(self, tool_id: str, data: CustomToolUpdate) -> CustomTool | None:
        result = await self._session.execute(select(CustomToolORM).where(CustomToolORM.id == UUID(tool_id)))
        row = result.scalar_one_or_none()
        if row is None:
            return None
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(row, field, value)
        row.updated_at = datetime.now(timezone.utc)
        await self._session.commit()
        await self._session.refresh(row)
        return self._to_schema(row)

    async def delete(self, tool_id: str) -> bool:
        result = await self._session.execute(
            delete(CustomToolORM).where(CustomToolORM.id == UUID(tool_id)).returning(CustomToolORM.id)
        )
        if result.scalar_one_or_none() is None:
            return False
        await self._session.commit()
        return True