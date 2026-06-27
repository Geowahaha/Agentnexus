from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.agent_ready_session import AgentReadySessionORM
from app.services.agent_ready.url_utils import normalize_site_url
from app.services.agent_ready.live_snapshot import host_slug

AGENT_READY_AUTO_FIX_SKILL_ID = uuid.UUID("33333333-3333-4333-8333-333333333310")


class AgentReadySessionRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    @staticmethod
    def normalize(url: str) -> tuple[str, str]:
        site_url = normalize_site_url(url)
        return site_url, host_slug(site_url)

    async def get_for_user(self, user_id: uuid.UUID, site_host: str) -> AgentReadySessionORM | None:
        res = await self._session.execute(
            select(AgentReadySessionORM).where(
                AgentReadySessionORM.user_id == user_id,
                AgentReadySessionORM.site_host == site_host,
            )
        )
        return res.scalar_one_or_none()

    async def list_for_user(self, user_id: uuid.UUID, *, limit: int = 20) -> list[AgentReadySessionORM]:
        res = await self._session.execute(
            select(AgentReadySessionORM)
            .where(AgentReadySessionORM.user_id == user_id)
            .order_by(AgentReadySessionORM.last_scan_at.desc().nullslast(), AgentReadySessionORM.updated_at.desc())
            .limit(limit)
        )
        return list(res.scalars().all())

    async def upsert_scan(
        self,
        *,
        user_id: uuid.UUID,
        site_url: str,
        state: dict,
        coach_headline: str | None,
        entitled: bool,
        workflow_id: str | None = None,
        mark_first_paid: bool = False,
    ) -> AgentReadySessionORM:
        site_url, site_host = self.normalize(site_url)
        now = datetime.now(timezone.utc)
        row = await self.get_for_user(user_id, site_host)
        if row is None:
            row = AgentReadySessionORM(
                user_id=user_id,
                site_url=site_url,
                site_host=site_host,
                expert_skill_id=AGENT_READY_AUTO_FIX_SKILL_ID,
                entitled=entitled,
                first_paid_at=now if mark_first_paid else None,
                last_scan_at=now,
                scan_count=1,
                workflow_id=workflow_id,
                coach_headline=coach_headline,
                state=state,
            )
            self._session.add(row)
        else:
            row.site_url = site_url
            row.state = state
            row.coach_headline = coach_headline
            row.last_scan_at = now
            row.scan_count = (row.scan_count or 0) + 1
            if workflow_id:
                row.workflow_id = workflow_id
            if entitled:
                row.entitled = True
            if mark_first_paid and row.first_paid_at is None:
                row.first_paid_at = now
        await self._session.commit()
        await self._session.refresh(row)
        return row

    async def patch_progress(self, user_id: uuid.UUID, site_host: str, progress: dict) -> AgentReadySessionORM | None:
        row = await self.get_for_user(user_id, site_host)
        if row is None:
            return None
        state = dict(row.state or {})
        merged = {**(state.get("progress") or {}), **progress}
        state["progress"] = merged
        row.state = state
        await self._session.commit()
        await self._session.refresh(row)
        return row