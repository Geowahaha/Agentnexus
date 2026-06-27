"""Create public AIBotAuth proof badges for OBOLLA marketplace deliverables."""

from __future__ import annotations

import logging
from typing import Any
from uuid import UUID

import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.services.moat_service import record_visibility_event

logger = logging.getLogger(__name__)


def _proof_base_url() -> str:
    base = (settings.aibotauth_base_url or "https://aibotauth.com").rstrip("/")
    return base


def build_embed_snippet(share_id: str, theme: str = "dark") -> str:
    base = _proof_base_url()
    return (
        f'<script src="{base}/embed/badge.js" '
        f'data-proof="{share_id}" data-theme="{theme}" async></script>'
    )


async def create_proof_from_scan(
    url: str,
    scan: dict[str, Any],
    *,
    lang: str = "en",
    account: str = "obolla",
    session: AsyncSession | None = None,
    workflow_id: str | None = None,
    linked_skill_id: str | UUID | None = None,
) -> dict[str, Any] | None:
    """Persist a partner proof record on aibotauth.com from an existing MCP scan.
    If session provided, also record to moat visibility_events (non-blocking).
    """
    api_key = settings.aibotauth_mcp_api_key
    if not api_key:
        logger.info("AIBOTAUTH_MCP_API_KEY not set — skipping proof badge")
        return None

    base = _proof_base_url()
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    body = {
        "url": url,
        "account": account,
        "lang": lang,
        "include_citation_probe": False,
        "include_screenshot": False,
        "unbranded": True,
        "monitor": True,
    }

    proof_result: dict[str, Any] | None = None
    try:
        async with httpx.AsyncClient(timeout=90.0) as client:
            response = await client.post(f"{base}/api/proof", json=body, headers=headers)
            data = response.json()
            if response.status_code >= 400 or data.get("error"):
                logger.warning(
                    "AIBotAuth proof failed status=%s error=%s",
                    response.status_code,
                    data.get("error"),
                )
                return None
            share_id = data.get("share_id") or ""
            proof_url = data.get("proof_url") or (f"{base}/proof/{share_id}" if share_id else "")
            embed = data.get("embed_snippet") or (build_embed_snippet(share_id) if share_id else "")
            latest = data.get("latest") or {}
            iar = latest.get("isitagentready") or {}
            psi = latest.get("pagespeed") or {}
            proof_result = {
                "share_id": share_id,
                "proof_url": proof_url,
                "embed_snippet": embed,
                "headline": data.get("headline") or data.get("report", {}).get("headline_en"),
                "overall": latest.get("overall") or scan.get("overall"),
                "grade": latest.get("grade") or scan.get("grade"),
                "isitagentready_percent": iar.get("percent"),
                "pagespeed_score": psi.get("performanceScore"),
                "first_run": data.get("first_run", True),
            }
    except Exception as exc:
        logger.warning("AIBotAuth proof request failed: %s", exc)
        return None

    # Moat capture (best effort)
    if session is not None and proof_result:
        try:
            overall = proof_result.get("overall")
            if isinstance(overall, (int, float)):
                overall = float(overall)
            percent = proof_result.get("isitagentready_percent")
            if isinstance(percent, (int, float)):
                percent = float(percent)
            await record_visibility_event(
                session=session,
                url=url,
                source="aibotauth_proof",
                overall=overall,
                grade=proof_result.get("grade"),
                percent=percent,
                details={"scan": scan, "latest": latest},
                proof_share_id=proof_result.get("share_id"),
                proof_url=proof_result.get("proof_url"),
                workflow_id=workflow_id,
                linked_skill_id=linked_skill_id,
            )
        except Exception as exc:  # noqa: BLE001
            logger.warning("moat visibility record after proof failed (non-fatal): %s", exc)

    return proof_result


def format_proof_deliverable(proof: dict[str, Any], lang: str = "en") -> str:
    if lang == "th":
        title = "## Agent-Ready Proof Badge"
        link = f"- **ลิงก์ proof สาธารณะ:** {proof.get('proof_url', '')}"
        score = f"- **คะแนน AIBotAuth:** {proof.get('overall', '—')}/100 ({proof.get('grade', '')})"
        if proof.get("isitagentready_percent") is not None:
            score += f"\n- **isitagentready.com:** {proof['isitagentready_percent']}%"
        if proof.get("pagespeed_score") is not None:
            score += f"\n- **PageSpeed mobile:** {proof['pagespeed_score']}/100"
        embed = f"- **Embed badge:**\n```html\n{proof.get('embed_snippet', '')}\n```"
        note = "- แชร์ลิงก์นี้กับลูกค้าหรือวาง embed ใน proposal — พิสูจน์จากสัญญาณสาธารณะจริง ไม่รับประกันอันดับหรือ citation\n- ใช้ Agent-Ready Auto Fix Pro บน OBOLLA เพื่อแก้ไขจริง + re-verify อัตโนมัติ"
    else:
        title = "## Agent-Ready Proof Badge (Closed-Loop)"
        link = f"- **Public proof URL:** {proof.get('proof_url', '')}"
        score = f"- **AIBotAuth score:** {proof.get('overall', '—')}/100 ({proof.get('grade', '')})"
        if proof.get("isitagentready_percent") is not None:
            score += f"\n- **isitagentready.com:** {proof['isitagentready_percent']}%"
        if proof.get("pagespeed_score") is not None:
            score += f"\n- **PageSpeed mobile:** {proof['pagespeed_score']}/100"
        embed = f"- **Embed badge:**\n```html\n{proof.get('embed_snippet', '')}\n```"
        action = f"- **Take action:** Run Agent-Ready Auto Fix Pro on OBOLLA for this URL → real files + Bridge apply + automatic re-verify + updated proof. https://obolla.com/agent-ready"
        note = "- Share this link with the buyer or paste the embed — observed public signals + execution data from OBOLLA. Full closed loop (scan → fix → prove lift). Not just another static badge.\n- Revenue attribution available in Creator Dashboard on OBOLLA."
    return "\n".join([title, link, score, embed, action, note])