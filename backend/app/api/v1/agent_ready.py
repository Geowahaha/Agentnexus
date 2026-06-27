from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field

from app.auth.dependencies import get_current_user
from app.auth.models import User
from app.repositories.agent_ready_session_repository import AgentReadySessionRepository
from app.services.agent_ready.orchestrator import AgentReadyOrchestrator
from app.services.agent_ready.run_archive import AgentReadyRunArchive
from app.services.agent_ready.session_service import AgentReadySessionService
from app.services.agent_ready.smart_scorecard import build_smart_scorecard
from app.core.deps import get_session
from app.services.moat_service import log_revenue_sale_from_outreach
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()
_orchestrator = AgentReadyOrchestrator()
_archive = AgentReadyRunArchive()


class AnalyzeRequest(BaseModel):
    url: str = Field(..., description="Site URL to analyze")


class SmartScanRequest(BaseModel):
    url: str = Field(..., description="Site URL to analyze")
    aibotauth_deep_scan: dict | None = Field(
        None,
        description="Optional paid AIBotAuth.com deep scan JSON export (customer special offer)",
    )


class ApplyAgentReadyFixRequest(BaseModel):
    """Matches the MCP tool input_schema for apply_agent_ready_fix."""
    url: str
    fix_pack: dict | None = None
    github_token: str | None = Field(None, description="For GitHub PR apply")
    repo: str | None = Field(None, description="GitHub owner/repo (e.g. user/my-site)")
    cf_project_name: str | None = None
    cf_api_token: str | None = None
    cf_worker_name: str | None = Field(None, description="Cloudflare Worker name (e.g. agentnexus)")
    cf_account_id: str | None = Field(None, description="Cloudflare account id for Workers deploy")


class VerifyRequest(BaseModel):
    url: str
    target_percent: int = Field(95, ge=0, le=100)
    max_attempts: int = Field(3, ge=1, le=10)
    purge_between: bool = True


class PurgeRequest(BaseModel):
    url: str
    zone_id: str | None = None


class GitHubPrDeployRequest(BaseModel):
    url: str
    repo: str = Field(..., description="GitHub repo owner/name or full URL")
    base_branch: str = "main"
    github_token: str | None = Field(None, description="Optional; falls back to GITHUB_TOKEN env")
    strategy: str | None = Field(None, description="Override deploy strategy (nextjs_app_router, static, etc.)")


class CloudflarePagesDeployRequest(BaseModel):
    url: str
    project_name: str
    branch: str = "main"
    account_id: str | None = None
    api_token: str | None = Field(None, description="Optional; falls back to CLOUDFLARE_API_TOKEN env")
    wait: bool = True


class CoachSyncRequest(BaseModel):
    url: str
    workflow_id: str | None = None
    analyze: dict | None = None
    fix_pack: dict | None = None
    progress: dict | None = None


class CoachProgressRequest(BaseModel):
    url: str
    progress: dict = Field(default_factory=dict)


class CoachRescanRequest(BaseModel):
    url: str


@router.post("/smart-scan")
async def smart_scan_site(body: SmartScanRequest):
    """OBOLLA Smart Score: paid AIBotAuth deep scan + 8-bot probe + isitagentready + SEO/AEO/AAIO."""
    try:
        return await build_smart_scorecard(
            body.url.strip(),
            aibotauth_deep_scan=body.aibotauth_deep_scan,
        )
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@router.post("/analyze")
async def analyze_site(body: AnalyzeRequest):
    """Stack fingerprint + isitagentready scan + deploy plan.
    Returns partial result on error to avoid hard failures in UI.
    """
    try:
        return await _orchestrator.analyze(body.url.strip())
    except Exception as exc:  # noqa: BLE001
        # Last resort: try verify-only scan so UI never shows a fake 0% when the scanner works.
        try:
            verify = await _orchestrator.verify_loop(body.url.strip(), max_attempts=1, purge_between=False)
            final = verify.get("final") or {}
            if final.get("percent") is not None:
                return {
                    "url": body.url.strip(),
                    "error": str(exc),
                    "partial": True,
                    "summary": final,
                    "scan": {
                        "level": final.get("level"),
                        "level_name": final.get("level_name"),
                    },
                    "note": "Analyze partial; score from live isitagentready verify.",
                }
        except Exception:
            pass
        return {
            "url": body.url.strip(),
            "error": str(exc),
            "partial": True,
            "summary": {"percent": 0, "fail": 1},
            "note": "Analyze had issues (scanner or network). Basic mode.",
        }


@router.post("/verify")
async def verify_site(body: VerifyRequest):
    """Post-deploy re-scan loop with optional Cloudflare cache purge."""
    try:
        return await _orchestrator.verify_loop(
            body.url.strip(),
            target_percent=body.target_percent,
            max_attempts=body.max_attempts,
            purge_between=body.purge_between,
        )
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@router.post("/deploy/github-pr")
async def deploy_github_pr(body: GitHubPrDeployRequest):
    """Create a branch + PR with agent-ready fix pack files (requires GITHUB_TOKEN)."""
    try:
        return await _orchestrator.deploy_github_pr(
            url=body.url.strip(),
            repo=body.repo.strip(),
            base_branch=body.base_branch,
            github_token=body.github_token,
            strategy=body.strategy,
        )
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@router.post("/deploy/cloudflare-pages")
async def deploy_cloudflare_pages(body: CloudflarePagesDeployRequest):
    """Direct Upload API for Cloudflare Pages (requires CLOUDFLARE_API_TOKEN + ACCOUNT_ID)."""
    try:
        return await _orchestrator.deploy_cloudflare_pages(
            url=body.url.strip(),
            project_name=body.project_name.strip(),
            branch=body.branch,
            account_id=body.account_id,
            api_token=body.api_token,
            wait=body.wait,
        )
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@router.post("/cloudflare/purge")
async def purge_agent_paths(body: PurgeRequest):
    """Purge agent-ready paths on Cloudflare (requires CLOUDFLARE_API_TOKEN)."""
    cf = _orchestrator.cf
    if not cf.configured:
        raise HTTPException(status_code=503, detail="CLOUDFLARE_API_TOKEN not configured on server")
    try:
        zone_id = body.zone_id or await cf.resolve_zone_id(body.url)
        if not zone_id:
            raise HTTPException(status_code=404, detail="Cloudflare zone not found for URL")
        urls = cf.agent_ready_purge_urls(body.url)
        result = await cf.purge_urls(urls, zone_id=zone_id)
        return {"zone_id": zone_id, **result, "urls": urls}
    except HTTPException:
        raise
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=502, detail=str(exc)) from exc


def _coach_service(session: AsyncSession = Depends(get_session)) -> AgentReadySessionService:
    return AgentReadySessionService(AgentReadySessionRepository(session))


@router.get("/coach/sites")
async def list_coach_sites(
    current_user: User = Depends(get_current_user),
    coach: AgentReadySessionService = Depends(_coach_service),
):
    """Sites this user has paid-scanned — enables resume + free re-scan."""
    sites = await coach.list_sites(current_user.id)
    return {"sites": sites, "count": len(sites)}


@router.get("/coach/session")
async def get_coach_session(
    url: str,
    current_user: User = Depends(get_current_user),
    coach: AgentReadySessionService = Depends(_coach_service),
):
    if not url.strip():
        raise HTTPException(status_code=400, detail="url query param required")
    record = await coach.get_session(current_user.id, url.strip())
    if not record:
        raise HTTPException(status_code=404, detail="No saved session for this site")
    return record


@router.post("/coach/sync")
async def sync_coach_after_paid_scan(
    body: CoachSyncRequest,
    current_user: User = Depends(get_current_user),
    coach: AgentReadySessionService = Depends(_coach_service),
):
    """Persist coach state after paid workflow — unlocks free re-scans for this URL."""
    try:
        return await coach.sync_after_paid_run(
            current_user.id,
            url=body.url.strip(),
            workflow_id=body.workflow_id,
            analyze=body.analyze,
            fix_pack=body.fix_pack,
            progress=body.progress,
        )
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@router.post("/coach/rescan")
async def coach_free_rescan(
    body: CoachRescanRequest,
    current_user: User = Depends(get_current_user),
    coach: AgentReadySessionService = Depends(_coach_service),
):
    """Re-scan live site for entitled users — no additional charge."""
    try:
        return await coach.rescan(current_user.id, body.url.strip())
    except PermissionError as exc:
        raise HTTPException(status_code=402, detail=str(exc)) from exc
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@router.post("/coach/progress")
async def coach_update_progress(
    body: CoachProgressRequest,
    current_user: User = Depends(get_current_user),
    coach: AgentReadySessionService = Depends(_coach_service),
):
    record = await coach.update_progress(current_user.id, body.url.strip(), body.progress)
    if not record:
        raise HTTPException(status_code=404, detail="No saved session for this site")
    return record


@router.get("/archive/sites")
async def list_archive_sites():
    """List per-site archive boxes (SITE.json index for each host)."""
    return {
        "archive_root": str(_archive.root),
        "sites": _archive.list_sites(),
    }


@router.get("/archive/runs")
async def list_archive_runs(url: str, limit: int = 20):
    """List archived runs for one website (newest first)."""
    if not url.strip():
        raise HTTPException(status_code=400, detail="url query param required")
    runs = _archive.list_runs(url.strip(), limit=min(max(limit, 1), 100))
    return {"url": url.strip(), "runs": runs, "count": len(runs)}


@router.get("/archive/runs/{host}/{run_id}")
async def get_archive_run(host: str, run_id: str):
    """Fetch RUN.json metadata for a single archived run."""
    record = _archive.get_run(host, run_id)
    if not record:
        raise HTTPException(status_code=404, detail="run not found")
    return record


@router.post("/fix-pack")
async def build_fix_pack(body: AnalyzeRequest):
    """Build the agent-ready fix pack (real files, diffs, SEO/AEO/AAIO content from page text)."""
    try:
        return _orchestrator.build_fix_pack(body.url.strip())
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@router.post("/apply")
async def apply_fix_and_log_revenue(
    body: ApplyAgentReadyFixRequest,
    session: AsyncSession = Depends(get_session),
):
    """
    MCP-compatible apply endpoint for apply_agent_ready_fix.

    - Builds or accepts fix_pack
    - Calls orchestrator.apply_agent_ready_fix (real deploys when tokens provided)
    - Always logs revenue to moat (Billing + CreatorEarning)
    """
    try:
        apply_result = await _orchestrator.apply_agent_ready_fix(
            url=body.url.strip(),
            fix_pack=body.fix_pack,
            github_token=body.github_token,
            repo=body.repo,
            cf_project_name=body.cf_project_name,
            cf_api_token=body.cf_api_token,
            cf_worker_name=body.cf_worker_name,
            cf_account_id=body.cf_account_id,
        )

        # Auto log revenue for the flagship Pro skill (closed-loop moat)
        sale = await log_revenue_sale_from_outreach(
            session=session,
            skill_slug="agent-ready-auto-fix",
            amount_usd=9.99,
            source="agent_ready_mcp_apply",
        )

        return {
            "result": apply_result,
            "sale": sale,
            "message": "apply_agent_ready_fix executed. " + apply_result.get("message", ""),
            "revenue_logged": True,
            "moat": "BillingTransaction + CreatorEarning created",
        }
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=502, detail=str(exc)) from exc