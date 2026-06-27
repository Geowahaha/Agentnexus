from datetime import datetime, timezone
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.agent import AgentORM
from app.models.agent import Agent, AgentCreate, AgentUpdate


class AgentRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    @staticmethod
    def _to_schema(row: AgentORM) -> Agent:
        return Agent(
            id=str(row.id),
            name=row.name,
            description=row.description,
            role=row.role,
            llm_model=row.llm_model,
            tools=list(row.tools or []),
            is_active=row.is_active,
            owner_id=str(row.owner_id),
            price_usd_per_run=Decimal(str(row.price_usd_per_run)),
            capabilities=list(row.capabilities or []),
            category=row.category,
            created_at=row.created_at,
            updated_at=row.updated_at,
        )

    async def create(self, data: AgentCreate, *, owner_id: str) -> Agent:
        now = datetime.now(timezone.utc)
        row = AgentORM(
            id=uuid4(),
            name=data.name,
            description=data.description,
            role=data.role,
            llm_model=data.llm_model,
            tools=data.tools,
            is_active=data.is_active,
            owner_id=UUID(owner_id),
            price_usd_per_run=data.price_usd_per_run,
            capabilities=data.capabilities,
            category=data.category,
            created_at=now,
            updated_at=now,
        )
        self._session.add(row)
        await self._session.commit()
        await self._session.refresh(row)
        return self._to_schema(row)

    async def get_by_id(self, agent_id: str) -> Agent | None:
        result = await self._session.execute(select(AgentORM).where(AgentORM.id == UUID(agent_id)))
        row = result.scalar_one_or_none()
        return self._to_schema(row) if row else None

    async def list_all(
        self,
        *,
        active_only: bool = True,
        owner_id: str | None = None,
        category: str | None = None,
        max_price: Decimal | None = None,
    ) -> list[Agent]:
        query = select(AgentORM).order_by(AgentORM.created_at.asc())
        if active_only:
            query = query.where(AgentORM.is_active.is_(True))
        if owner_id:
            query = query.where(AgentORM.owner_id == UUID(owner_id))
        if category:
            query = query.where(AgentORM.category == category)
        if max_price is not None:
            query = query.where(AgentORM.price_usd_per_run <= max_price)
        result = await self._session.execute(query)
        return [self._to_schema(row) for row in result.scalars().all()]

    async def update(self, agent_id: str, data: AgentUpdate) -> Agent | None:
        result = await self._session.execute(select(AgentORM).where(AgentORM.id == UUID(agent_id)))
        row = result.scalar_one_or_none()
        if row is None:
            return None
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(row, field, value)
        row.updated_at = datetime.now(timezone.utc)
        await self._session.commit()
        await self._session.refresh(row)
        return self._to_schema(row)

    async def delete(self, agent_id: str) -> bool:
        result = await self._session.execute(
            delete(AgentORM).where(AgentORM.id == UUID(agent_id)).returning(AgentORM.id)
        )
        if result.scalar_one_or_none() is None:
            return False
        await self._session.commit()
        return True