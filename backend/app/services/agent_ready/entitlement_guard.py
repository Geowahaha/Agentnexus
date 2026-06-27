from __future__ import annotations

import uuid
from typing import Any

from app.core.checkpoint import get_checkpointer
from app.repositories.agent_ready_session_repository import AgentReadySessionRepository
from app.services.agent_ready.live_snapshot import host_slug
from app.services.agent_ready.url_utils import normalize_site_url

AGENT_READY_SKILL_ID = "33333333-3333-4333-8333-333333333310"


def hosts_match(url_a: str, url_b: str) -> bool:
    return host_slug(url_a) == host_slug(url_b)


async def is_entitled(repo: AgentReadySessionRepository, user_id: str | uuid.UUID, url: str) -> bool:
    uid = user_id if isinstance(user_id, uuid.UUID) else uuid.UUID(str(user_id))
    _, host = repo.normalize(url)
    row = await repo.get_for_user(uid, host)
    return row is not None and bool(row.entitled)


async def assert_entitled(repo: AgentReadySessionRepository, user_id: str | uuid.UUID, url: str) -> None:
    if not await is_entitled(repo, user_id, url):
        raise PermissionError(
            "No paid entitlement for this site — purchase Agent-Ready for this URL first, "
            "or use free re-scan on your purchased site only."
        )


async def verify_workflow_for_site(
    *,
    workflow_id: str,
    user_id: str | uuid.UUID,
    site_url: str,
) -> None:
    """Ensure workflow_id is a paid Agent-Ready run for this user + URL."""
    wid = (workflow_id or "").strip()
    if not wid:
        raise PermissionError("workflow_id required to bind purchase to this site")

    checkpointer = get_checkpointer()
    config = {"configurable": {"thread_id": wid}}
    checkpoint_tuple = await checkpointer.aget_tuple(config)
    if checkpoint_tuple is None:
        raise PermissionError("Invalid workflow — purchase not verified")

    state: dict[str, Any] = checkpoint_tuple.checkpoint.get("channel_values", {}) or {}
    owner = str(state.get("user_id") or "")
    if owner != str(user_id):
        raise PermissionError("Workflow does not belong to this user")

    ctx = state.get("task_context") or {}
    skill_id = str(ctx.get("expert_skill_id") or "")
    if skill_id != AGENT_READY_SKILL_ID:
        raise PermissionError("Workflow is not an Agent-Ready purchase")

    intermediate = state.get("intermediate_results") or {}
    target = (
        ctx.get("target_url")
        or intermediate.get("target_url")
        or state.get("task_description")
    )
    if not target or not hosts_match(site_url, str(target)):
        raise PermissionError("Workflow URL does not match this site — purchase is bound to one website")


async def assert_scan_allowed(
    repo: AgentReadySessionRepository,
    user_id: str | uuid.UUID,
    url: str,
    *,
    workflow_id: str | None = None,
) -> None:
    """Logged-in scan: entitled URL (free re-scan path) OR fresh paid workflow for this URL."""
    if await is_entitled(repo, user_id, url):
        return
    if workflow_id:
        await verify_workflow_for_site(workflow_id=workflow_id, user_id=user_id, site_url=url)
        return
    raise PermissionError(
        "This site is not purchased — pay $9.99 for a new URL, or use free re-scan on your purchased site only."
    )


def normalize_bound_url(url: str) -> str:
    return normalize_site_url(url)