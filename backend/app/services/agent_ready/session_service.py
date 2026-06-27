from __future__ import annotations

import asyncio
import logging
import uuid
from datetime import datetime, timezone
from typing import Any

from app.core.database import async_session_maker
from app.repositories.agent_ready_session_repository import AgentReadySessionRepository
from app.repositories.user_repository import UserRepository
from app.services.agent_ready.coach import build_coach_brief_async, build_session_state
from app.services.agent_ready.coach_notify import notify_rescan_complete
from app.services.agent_ready.entitlement_guard import assert_entitled, verify_workflow_for_site
from app.services.agent_ready.orchestrator import AgentReadyOrchestrator

logger = logging.getLogger(__name__)
_background_rescans: set[str] = set()


class AgentReadySessionService:
    AGENT_READY_SKILL_ID = "33333333-3333-4333-8333-333333333310"

    def __init__(self, repo: AgentReadySessionRepository, users: UserRepository | None = None) -> None:
        self._repo = repo
        self._users = users
        self._orchestrator = AgentReadyOrchestrator()

    @staticmethod
    def _uid(user_id: str | uuid.UUID) -> uuid.UUID:
        return user_id if isinstance(user_id, uuid.UUID) else uuid.UUID(str(user_id))

    async def list_sites(self, user_id: str | uuid.UUID) -> list[dict[str, Any]]:
        rows = await self._repo.list_for_user(self._uid(user_id))
        return [self._row_summary(r) for r in rows]

    async def get_session(self, user_id: str | uuid.UUID, url: str) -> dict[str, Any] | None:
        _, host = self._repo.normalize(url)
        row = await self._repo.get_for_user(self._uid(user_id), host)
        if row is None:
            return None
        return self._row_detail(row)

    async def sync_after_paid_run(
        self,
        user_id: str | uuid.UUID,
        *,
        url: str,
        workflow_id: str | None = None,
        analyze: dict[str, Any] | None = None,
        fix_pack: dict[str, Any] | None = None,
        progress: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        site_url, _ = self._repo.normalize(url)
        uid = self._uid(user_id)
        _, host = self._repo.normalize(site_url)
        existing = await self._repo.get_for_user(uid, host)
        if existing and existing.entitled:
            raise PermissionError(
                "This site is already purchased — use free re-scan only; "
                "enter a different URL and pay again for another website."
            )
        if not workflow_id:
            raise PermissionError("workflow_id required to bind purchase to scanned website")
        await verify_workflow_for_site(workflow_id=workflow_id, user_id=uid, site_url=site_url)

        scan = analyze or await self._orchestrator.analyze(site_url)
        scan["recorded_at"] = datetime.now(timezone.utc).isoformat()
        pack = fix_pack
        if pack is None:
            pack = self._orchestrator.build_fix_pack(site_url)
        initial = (existing.state or {}).get("initial_scan") if existing else None
        if not initial:
            initial = scan

        prev = (existing.state or {}).get("latest_scan") if existing else None
        coach = await build_coach_brief_async(scan, previous=prev, is_rescan=False)
        state = build_session_state(
            analyze=scan,
            coach=coach,
            fix_pack=pack,
            progress=progress or {"scanned": True, "fix_pack_ready": True, "mcp_applied": False, "reverified": False},
            initial_analyze=initial if isinstance(initial, dict) else scan,
        )
        row = await self._repo.upsert_scan(
            user_id=uid,
            site_url=site_url,
            state=state,
            coach_headline=coach.get("headline_en"),
            entitled=True,
            workflow_id=workflow_id,
            mark_first_paid=True,
        )
        return self._row_detail(row)

    async def rescan(
        self,
        user_id: str | uuid.UUID,
        url: str,
        *,
        notify_email: bool = True,
    ) -> dict[str, Any]:
        uid = self._uid(user_id)
        _, host = self._repo.normalize(url)
        await assert_entitled(self._repo, uid, url)
        row = await self._repo.get_for_user(uid, host)
        if row is None:
            raise PermissionError("No paid entitlement for this site — run a paid scan first")

        site_url, _ = self._repo.normalize(url)
        previous_latest = (row.state or {}).get("latest_scan")
        scan = await self._orchestrator.analyze(site_url)
        scan["recorded_at"] = datetime.now(timezone.utc).isoformat()
        coach = await build_coach_brief_async(scan, previous=previous_latest, is_rescan=True)
        initial = (row.state or {}).get("initial_scan") or previous_latest
        progress = dict((row.state or {}).get("progress") or {})
        progress["reverified"] = True
        progress["last_rescan_at"] = scan["recorded_at"]

        state = build_session_state(
            analyze=scan,
            coach=coach,
            fix_pack=(row.state or {}).get("fix_pack"),
            progress=progress,
            initial_analyze=initial if isinstance(initial, dict) else None,
        )
        updated = await self._repo.upsert_scan(
            user_id=uid,
            site_url=site_url,
            state=state,
            coach_headline=coach.get("headline_en"),
            entitled=True,
        )
        out = self._row_detail(updated)
        out["rescan"] = True
        out["free"] = True

        if self._users and notify_email:
            user = await self._users.get_by_id(str(user_id))
            if user and user.email:
                notify_result = await notify_rescan_complete(
                    user_id=str(user_id),
                    user_email=user.email,
                    user_name=user.full_name,
                    site_url=site_url,
                    site_host=host,
                    coach=coach,
                    send_email=notify_email,
                )
                out["notification"] = notify_result

        return out

    async def queue_rescan(
        self,
        user_id: str | uuid.UUID,
        url: str,
        *,
        notify_email: bool = True,
    ) -> dict[str, Any]:
        """Queue live re-scan in background — user can leave; email/push when done."""
        uid = self._uid(user_id)
        _, host = self._repo.normalize(url)
        await assert_entitled(self._repo, uid, url)
        row = await self._repo.get_for_user(uid, host)
        if row is None:
            raise PermissionError("No paid entitlement for this site — run a paid scan first")

        key = f"{uid}:{host}"
        if key in _background_rescans:
            return {
                "status": "already_queued",
                "site_url": row.site_url,
                "site_host": host,
                "notify_email": notify_email,
            }

        site_url, _ = self._repo.normalize(url)
        _background_rescans.add(key)
        asyncio.create_task(
            self._rescan_background(str(user_id), site_url, notify_email=notify_email, queue_key=key)
        )
        return {
            "status": "queued",
            "site_url": site_url,
            "site_host": host,
            "notify_email": notify_email,
            "message_th": "กำลัง re-scan ในพื้นหลัง — เราจะส่ง email เมื่อเสร็จ ปิดหน้าได้เลย",
            "message_en": "Re-scan queued in the background — we'll email you when it's done.",
        }

    @staticmethod
    async def _rescan_background(
        user_id: str,
        url: str,
        *,
        notify_email: bool,
        queue_key: str,
    ) -> None:
        try:
            async with async_session_maker() as session:
                svc = AgentReadySessionService(
                    AgentReadySessionRepository(session),
                    UserRepository(session),
                )
                await svc.rescan(user_id, url, notify_email=notify_email)
        except Exception as exc:  # noqa: BLE001
            logger.exception("background rescan failed for %s: %s", url, exc)
        finally:
            _background_rescans.discard(queue_key)

    async def update_progress(self, user_id: str | uuid.UUID, url: str, progress: dict[str, Any]) -> dict[str, Any] | None:
        await assert_entitled(self._repo, self._uid(user_id), url)
        _, host = self._repo.normalize(url)
        row = await self._repo.patch_progress(self._uid(user_id), host, progress)
        return self._row_detail(row) if row else None

    def _row_summary(self, row: Any) -> dict[str, Any]:
        coach = (row.state or {}).get("coach") or {}
        scores = coach.get("scores") or {}
        return {
            "site_url": row.site_url,
            "site_host": row.site_host,
            "entitled": row.entitled,
            "scan_count": row.scan_count,
            "last_scan_at": row.last_scan_at.isoformat() if row.last_scan_at else None,
            "coach_headline": row.coach_headline,
            "growth_percent": scores.get("growth_percent"),
            "protocol_percent": scores.get("protocol_percent"),
        }

    def _row_detail(self, row: Any) -> dict[str, Any]:
        state = row.state or {}
        return {
            **self._row_summary(row),
            "workflow_id": row.workflow_id,
            "first_paid_at": row.first_paid_at.isoformat() if row.first_paid_at else None,
            "coach": state.get("coach"),
            "latest_scan": state.get("latest_scan"),
            "initial_scan": state.get("initial_scan"),
            "fix_pack_meta": state.get("fix_pack_meta"),
            "fix_pack": state.get("fix_pack"),
            "progress": state.get("progress"),
            "free_rescan_available": bool(row.entitled),
        }