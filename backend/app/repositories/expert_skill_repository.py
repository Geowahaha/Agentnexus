from datetime import datetime, timezone
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.expert_skill import ExpertSkillORM
from app.expert_skills.custom_defaults import build_default_crew_config
from app.expert_skills.model_tiers import strip_runtime_crew_fields
from app.expert_skills.thai_copy import ensure_obolla_thai_i18n
from app.models.creator import ExpertSkillCreate, ExpertSkillUpdate
from app.models.expert_skill import ExpertSkill


class ExpertSkillNotFoundError(KeyError):
    pass


FEATURED_FIRST_SLUGS = ("fable5-coding-agent-premium", "fable5-coding-agent")


class ExpertSkillRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    @staticmethod
    def _featured_rank(slug: str) -> int:
        try:
            return FEATURED_FIRST_SLUGS.index(slug)
        except ValueError:
            return len(FEATURED_FIRST_SLUGS)

    @staticmethod
    def _to_schema(row: ExpertSkillORM) -> ExpertSkill:
        return ExpertSkill(
            id=str(row.id),
            slug=row.slug,
            name=row.name,
            description=row.description,
            i18n=dict(row.i18n or {}),
            category=row.category,
            pack_slug=row.pack_slug,
            crew_config=dict(row.crew_config or {}),
            capabilities=list(row.capabilities or []),
            price_usd_per_run=row.price_usd_per_run,
            owner_id=str(row.owner_id),
            is_active=row.is_active,
            created_at=row.created_at,
            updated_at=row.updated_at,
        )

    async def get_by_id(self, skill_id: str) -> ExpertSkill | None:
        try:
            skill_uuid = UUID(skill_id)
        except ValueError:
            return None
        result = await self._session.execute(
            select(ExpertSkillORM).where(ExpertSkillORM.id == skill_uuid)
        )
        row = result.scalar_one_or_none()
        return self._to_schema(row) if row else None

    async def get_by_slug(self, slug: str) -> ExpertSkill | None:
        result = await self._session.execute(
            select(ExpertSkillORM).where(ExpertSkillORM.slug == slug)
        )
        row = result.scalar_one_or_none()
        return self._to_schema(row) if row else None

    async def list_all(self, *, active_only: bool = True, category: str | None = None) -> list[ExpertSkill]:
        query = select(ExpertSkillORM).order_by(ExpertSkillORM.created_at.asc())
        if active_only:
            query = query.where(ExpertSkillORM.is_active.is_(True))
        if category:
            query = query.where(ExpertSkillORM.category == category)
        result = await self._session.execute(query)
        rows = list(result.scalars().all())
        rows.sort(key=lambda row: (self._featured_rank(row.slug), row.created_at))
        return [self._to_schema(row) for row in rows]

    async def list_by_owner(self, owner_id: str, *, active_only: bool = False) -> list[ExpertSkill]:
        query = (
            select(ExpertSkillORM)
            .where(ExpertSkillORM.owner_id == UUID(owner_id))
            .order_by(ExpertSkillORM.created_at.desc())
        )
        if active_only:
            query = query.where(ExpertSkillORM.is_active.is_(True))
        result = await self._session.execute(query)
        return [self._to_schema(row) for row in result.scalars().all()]

    async def create(self, payload: ExpertSkillCreate, *, owner_id: str) -> ExpertSkill:
        now = datetime.now(timezone.utc)
        crew_config = (
            build_default_crew_config(
                category=payload.category,
                name=payload.name,
                description=payload.description,
            )
            if payload.pack_slug == "custom"
            else {}
        )
        row = ExpertSkillORM(
            id=uuid4(),
            slug=payload.slug,
            name=payload.name,
            description=payload.description,
            category=payload.category,
            pack_slug=payload.pack_slug,
            crew_config=crew_config,
            capabilities=list(payload.capabilities),
            price_usd_per_run=Decimal(str(payload.price_usd_per_run)),
            owner_id=UUID(owner_id),
            is_active=True,
            created_at=now,
            updated_at=now,
        )
        self._session.add(row)
        await self._session.commit()
        await self._session.refresh(row)
        created = self._to_schema(row)
        return await ensure_obolla_thai_i18n(self, created)

    async def update(self, skill_id: str, payload: ExpertSkillUpdate) -> ExpertSkill | None:
        result = await self._session.execute(
            select(ExpertSkillORM).where(ExpertSkillORM.id == UUID(skill_id))
        )
        row = result.scalar_one_or_none()
        if row is None:
            return None

        data = payload.model_dump(exclude_unset=True)
        data.pop("name_th", None)
        data.pop("description_th", None)
        if "price_usd_per_run" in data and data["price_usd_per_run"] is not None:
            data["price_usd_per_run"] = Decimal(str(data["price_usd_per_run"]))
        crew_patch = data.pop("crew_config", None)
        if crew_patch is not None:
            merged = dict(row.crew_config or {})
            merged.update(crew_patch)
            if row.pack_slug == "custom" and payload.description and "skill_md" not in crew_patch:
                merged.setdefault(
                    "skill_md",
                    build_default_crew_config(
                        category=row.category,
                        name=row.name,
                        description=payload.description,
                        pipeline_label=merged.get("pipeline_label"),
                    )["skill_md"],
                )
            data["crew_config"] = strip_runtime_crew_fields(merged)
        for key, value in data.items():
            setattr(row, key, value)
        row.updated_at = datetime.now(timezone.utc)
        await self._session.commit()
        await self._session.refresh(row)
        updated = self._to_schema(row)
        return await ensure_obolla_thai_i18n(self, updated)

    async def save_i18n_locale(self, skill_id: str, locale: str, patch: dict[str, str]) -> ExpertSkill | None:
        result = await self._session.execute(
            select(ExpertSkillORM).where(ExpertSkillORM.id == UUID(skill_id))
        )
        row = result.scalar_one_or_none()
        if row is None:
            return None
        from app.expert_skills.skill_locale import merge_i18n_locale

        row.i18n = merge_i18n_locale(row.i18n, locale, patch)
        row.updated_at = datetime.now(timezone.utc)
        await self._session.commit()
        await self._session.refresh(row)
        return self._to_schema(row)

    async def delete(self, skill_id: str) -> bool:
        result = await self._session.execute(
            select(ExpertSkillORM).where(ExpertSkillORM.id == UUID(skill_id))
        )
        row = result.scalar_one_or_none()
        if row is None:
            return False
        await self._session.delete(row)
        await self._session.commit()
        return True