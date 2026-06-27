from datetime import datetime, timezone
from uuid import UUID, uuid4

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.agent_portfolio import AgentPortfolioItemORM
from app.db.models.creator_earning import CreatorEarningORM
from app.models.portfolio import AgentStats, PortfolioItem, PortfolioItemCreate, PortfolioItemUpdate


class PortfolioRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    @staticmethod
    def _to_schema(row: AgentPortfolioItemORM) -> PortfolioItem:
        return PortfolioItem(
            id=str(row.id),
            agent_id=str(row.agent_id),
            workflow_id=row.workflow_id,
            title=row.title,
            summary=row.summary,
            task_preview=row.task_preview,
            output_preview=row.output_preview,
            workflow_type=row.workflow_type,
            is_public=row.is_public,
            sort_order=row.sort_order,
            created_at=row.created_at,
            updated_at=row.updated_at,
        )

    async def list_for_agent(
        self,
        agent_id: str,
        *,
        public_only: bool = True,
    ) -> list[PortfolioItem]:
        query = (
            select(AgentPortfolioItemORM)
            .where(AgentPortfolioItemORM.agent_id == UUID(agent_id))
            .order_by(AgentPortfolioItemORM.sort_order.asc(), AgentPortfolioItemORM.created_at.desc())
        )
        if public_only:
            query = query.where(AgentPortfolioItemORM.is_public.is_(True))
        result = await self._session.execute(query)
        return [self._to_schema(row) for row in result.scalars().all()]

    async def get_by_id(self, item_id: str) -> PortfolioItem | None:
        result = await self._session.execute(
            select(AgentPortfolioItemORM).where(AgentPortfolioItemORM.id == UUID(item_id))
        )
        row = result.scalar_one_or_none()
        return self._to_schema(row) if row else None

    async def get_by_agent_and_workflow(self, agent_id: str, workflow_id: str) -> PortfolioItem | None:
        result = await self._session.execute(
            select(AgentPortfolioItemORM).where(
                AgentPortfolioItemORM.agent_id == UUID(agent_id),
                AgentPortfolioItemORM.workflow_id == workflow_id,
            )
        )
        row = result.scalar_one_or_none()
        return self._to_schema(row) if row else None

    async def create(
        self,
        agent_id: str,
        data: PortfolioItemCreate,
        *,
        task_preview: str,
        output_preview: str,
        workflow_type: str,
    ) -> PortfolioItem:
        now = datetime.now(timezone.utc)
        row = AgentPortfolioItemORM(
            id=uuid4(),
            agent_id=UUID(agent_id),
            workflow_id=data.workflow_id,
            title=data.title or "Untitled work sample",
            summary=data.summary,
            task_preview=task_preview,
            output_preview=output_preview,
            workflow_type=workflow_type,
            is_public=data.is_public,
            sort_order=0,
            created_at=now,
            updated_at=now,
        )
        self._session.add(row)
        await self._session.commit()
        await self._session.refresh(row)
        return self._to_schema(row)

    async def update(self, item_id: str, data: PortfolioItemUpdate) -> PortfolioItem | None:
        result = await self._session.execute(
            select(AgentPortfolioItemORM).where(AgentPortfolioItemORM.id == UUID(item_id))
        )
        row = result.scalar_one_or_none()
        if row is None:
            return None
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(row, field, value)
        row.updated_at = datetime.now(timezone.utc)
        await self._session.commit()
        await self._session.refresh(row)
        return self._to_schema(row)

    async def delete(self, item_id: str) -> bool:
        result = await self._session.execute(
            delete(AgentPortfolioItemORM)
            .where(AgentPortfolioItemORM.id == UUID(item_id))
            .returning(AgentPortfolioItemORM.id)
        )
        if result.scalar_one_or_none() is None:
            return False
        await self._session.commit()
        return True

    async def get_stats(self, agent_id: str) -> AgentStats:
        portfolio_count = await self._session.scalar(
            select(func.count())
            .select_from(AgentPortfolioItemORM)
            .where(
                AgentPortfolioItemORM.agent_id == UUID(agent_id),
                AgentPortfolioItemORM.is_public.is_(True),
            )
        )
        total_hires = await self._session.scalar(
            select(func.count())
            .select_from(CreatorEarningORM)
            .where(CreatorEarningORM.agent_id == UUID(agent_id))
        )
        return AgentStats(
            portfolio_count=int(portfolio_count or 0),
            total_hires=int(total_hires or 0),
        )