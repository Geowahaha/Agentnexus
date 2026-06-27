from datetime import datetime, timezone
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.expert_skill import ExpertSkillORM
from app.db.models.skill_showcase import SkillShowcaseORM
from app.models.showcase import ShowcaseBeforeAfter, SkillShowcase, SkillShowcaseSkillSummary


class ShowcaseRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    @staticmethod
    def _skill_summary(row: ExpertSkillORM | None) -> SkillShowcaseSkillSummary | None:
        if row is None:
            return None
        return SkillShowcaseSkillSummary(
            id=str(row.id),
            slug=row.slug,
            name=row.name,
            category=row.category,
            price_usd_per_run=str(row.price_usd_per_run),
        )

    @staticmethod
    def _to_schema(row: SkillShowcaseORM, skill: ExpertSkillORM | None = None) -> SkillShowcase:
        ba = row.before_after or {}
        try:
            before_after = ShowcaseBeforeAfter.model_validate(ba)
        except Exception:
            before_after = ShowcaseBeforeAfter()
        return SkillShowcase(
            id=str(row.id),
            expert_skill_id=str(row.expert_skill_id),
            title=row.title,
            site_name=row.site_name,
            site_url=row.site_url,
            summary=row.summary,
            metric_label=row.metric_label,
            metric_value=row.metric_value,
            highlights=list(row.highlights or []),
            sort_order=row.sort_order,
            is_featured=row.is_featured,
            is_active=row.is_active,
            workflow_id=str(row.workflow_id) if row.workflow_id else None,
            sample_output=row.sample_output,
            deliverables=list(row.deliverables or []),
            stats=dict(row.stats or {}),
            before_after=before_after,
            created_at=row.created_at,
            updated_at=row.updated_at,
            skill=ShowcaseRepository._skill_summary(skill),
        )

    async def list_all(
        self,
        *,
        active_only: bool = True,
        category: str | None = None,
        featured_only: bool = False,
        expert_skill_id: str | None = None,
    ) -> list[SkillShowcase]:
        query = (
            select(SkillShowcaseORM, ExpertSkillORM)
            .join(ExpertSkillORM, ExpertSkillORM.id == SkillShowcaseORM.expert_skill_id)
            .order_by(SkillShowcaseORM.is_featured.desc(), SkillShowcaseORM.sort_order.asc())
        )
        if active_only:
            query = query.where(
                SkillShowcaseORM.is_active.is_(True),
                ExpertSkillORM.is_active.is_(True),
            )
        if featured_only:
            query = query.where(SkillShowcaseORM.is_featured.is_(True))
        if category:
            query = query.where(ExpertSkillORM.category == category)
        if expert_skill_id:
            query = query.where(SkillShowcaseORM.expert_skill_id == UUID(expert_skill_id))
        result = await self._session.execute(query)
        return [self._to_schema(showcase, skill) for showcase, skill in result.all()]

    async def get_by_id(self, showcase_id: str) -> SkillShowcase | None:
        result = await self._session.execute(
            select(SkillShowcaseORM, ExpertSkillORM)
            .join(ExpertSkillORM, ExpertSkillORM.id == SkillShowcaseORM.expert_skill_id)
            .where(SkillShowcaseORM.id == UUID(showcase_id))
        )
        row = result.one_or_none()
        if row is None:
            return None
        showcase, skill = row
        return self._to_schema(showcase, skill)

    async def create(
        self,
        *,
        expert_skill_id: str,
        title: str,
        site_name: str,
        site_url: str,
        summary: str,
        workflow_id: str | None = None,
        sample_output: str | None = None,
        metric_label: str | None = None,
        metric_value: str | None = None,
        highlights: list[str] | None = None,
        deliverables: list[str] | None = None,
        stats: dict | None = None,
        is_featured: bool = False,
    ) -> SkillShowcase:
        now = datetime.now(timezone.utc)
        row = SkillShowcaseORM(
            id=uuid4(),
            expert_skill_id=UUID(expert_skill_id),
            title=title[:200],
            site_name=site_name[:120],
            site_url=site_url[:500] or "https://obolla.com",
            summary=summary,
            metric_label=metric_label,
            metric_value=metric_value,
            highlights=list(highlights or []),
            sort_order=10,
            is_featured=is_featured,
            is_active=True,
            workflow_id=UUID(workflow_id) if workflow_id else None,
            sample_output=sample_output,
            deliverables=list(deliverables or []),
            stats=dict(stats or {}),
            before_after={},
            created_at=now,
            updated_at=now,
        )
        self._session.add(row)
        await self._session.commit()
        await self._session.refresh(row)
        skill_result = await self._session.execute(
            select(ExpertSkillORM).where(ExpertSkillORM.id == row.expert_skill_id)
        )
        skill = skill_result.scalar_one_or_none()
        return self._to_schema(row, skill)