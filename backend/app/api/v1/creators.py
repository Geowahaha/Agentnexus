from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field

from app.auth.dependencies import get_current_user, require_resource_owner
from app.auth.models import User
from app.billing.service import BillingService
from app.core.config import settings
from app.core.deps import (
    get_billing_service,
    get_creator_repository,
    get_custom_tool_repository,
    get_expert_skill_repository,
    get_mcp_server_repository,
    get_showcase_service,
    get_workflow_service,
)
from app.models.showcase import ShowcaseFromWorkflowCreate, SkillShowcase
from app.services.pricing_ceiling import enforce_price_ceiling, merge_crew_preserve_ceiling, parse_price
from app.services.publish_insight_service import build_creator_test_task
from app.services.showcase_service import ShowcaseService
from app.services.workflow_service import WorkflowNotFoundError, WorkflowPermissionError, WorkflowService
from app.graphs.utils import assess_expert_skill_delivery
from app.models.creator import (
    CreatorAnalytics,
    CreatorPayouts,
    CreatorReviewsSummary,
    CreatorSkillItem,
    CreatorSummary,
    ExpertSkillCreate,
    ExpertSkillUpdate,
)
from app.models.custom_tool import CustomTool
from app.models.expert_skill import ExpertSkill
from app.models.mcp_server import MCPServer
from app.repositories.creator_repository import CreatorRepository
from app.repositories.custom_tool_repository import CustomToolRepository
from app.repositories.expert_skill_repository import ExpertSkillRepository
from app.repositories.mcp_server_repository import MCPServerRepository

router = APIRouter()


@router.get("/me/summary", response_model=CreatorSummary)
async def get_creator_summary(
    current_user: User = Depends(get_current_user),
    creator_repo: CreatorRepository = Depends(get_creator_repository),
    billing: BillingService = Depends(get_billing_service),
) -> CreatorSummary:
    wallet = await billing.get_wallet(
        current_user.id,
        initial_balance=Decimal(str(settings.signup_credits_usd)),
    )
    return await creator_repo.get_summary(
        current_user.id,
        earnings_balance_usd=wallet.earnings_balance_usd,
        platform_fee_percent=settings.platform_fee_percent,
    )


@router.get("/me/skills", response_model=list[CreatorSkillItem])
async def list_creator_skills(
    current_user: User = Depends(get_current_user),
    creator_repo: CreatorRepository = Depends(get_creator_repository),
) -> list[CreatorSkillItem]:
    return await creator_repo.list_skills(current_user.id)


@router.post("/me/skills", response_model=ExpertSkill, status_code=status.HTTP_201_CREATED)
async def create_creator_skill(
    payload: ExpertSkillCreate,
    current_user: User = Depends(get_current_user),
    skill_repo: ExpertSkillRepository = Depends(get_expert_skill_repository),
) -> ExpertSkill:
    existing = await skill_repo.get_by_slug(payload.slug)
    if existing is not None:
        raise HTTPException(status_code=409, detail=f"Slug '{payload.slug}' is already taken.")
    return await skill_repo.create(payload, owner_id=current_user.id)


@router.patch("/me/skills/{skill_id}", response_model=ExpertSkill)
async def update_creator_skill(
    skill_id: str,
    payload: ExpertSkillUpdate,
    current_user: User = Depends(get_current_user),
    skill_repo: ExpertSkillRepository = Depends(get_expert_skill_repository),
) -> ExpertSkill:
    skill = await skill_repo.get_by_id(skill_id)
    if skill is None:
        raise HTTPException(status_code=404, detail=f"Expert skill '{skill_id}' not found")
    require_resource_owner(skill.owner_id, current_user)
    if payload.price_usd_per_run is not None:
        enforce_price_ceiling(
            crew_config=skill.crew_config,
            new_price=payload.price_usd_per_run,
            locale=getattr(current_user, "locale", "en") or "en",
        )
    data = payload.model_dump(exclude_unset=True)
    crew_patch = data.get("crew_config")
    if crew_patch is not None:
        proposed = parse_price(crew_patch.get("pricing_ceiling_usd"))
        merged = merge_crew_preserve_ceiling(skill.crew_config, crew_patch, proposed_ceiling=proposed)
        data["crew_config"] = merged
        payload = ExpertSkillUpdate(**{**payload.model_dump(exclude_unset=True), "crew_config": merged})
    updated = await skill_repo.update(skill_id, payload)
    assert updated is not None
    return updated


class CreatorTestRunFinalizeRequest(BaseModel):
    workflow_id: str = Field(..., min_length=8, max_length=80)


def _assess_test_run(skill: ExpertSkill, workflow_state: dict) -> dict:
    crew_steps = None
    if isinstance(skill.crew_config, dict):
        crew_steps = skill.crew_config.get("steps")
        if not isinstance(crew_steps, list):
            crew_steps = None
    delivery = assess_expert_skill_delivery(workflow_state, crew_steps=crew_steps)
    status = str(workflow_state.get("status") or "")
    passed = status == "completed" and delivery["delivery_quality"] != "failed"
    return {"passed": passed, "delivery_quality": delivery["delivery_quality"], "status": status}


@router.post("/me/skills/{skill_id}/test-run")
async def creator_skill_test_run(
    skill_id: str,
    current_user: User = Depends(get_current_user),
    skill_repo: ExpertSkillRepository = Depends(get_expert_skill_repository),
    workflow_service: WorkflowService = Depends(get_workflow_service),
) -> dict:
    """Start pre-publish test run (background pipeline). Finalize when workflow completes."""
    from datetime import datetime, timezone

    skill = await skill_repo.get_by_id(skill_id)
    if skill is None:
        raise HTTPException(status_code=404, detail=f"Expert skill '{skill_id}' not found")
    require_resource_owner(skill.owner_id, current_user)

    task_description = build_creator_test_task(skill)
    try:
        result, _billing = await workflow_service.run(
            user_id=current_user.id,
            task_description=task_description,
            workflow_type="expert_skill",
            task_context={
                "expert_skill_id": skill.id,
                "expert_skill_slug": skill.slug,
                "creator_test_run": True,
            },
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Test run failed: {exc}") from exc

    workflow_id = str(result.get("workflow_id") or "")
    crew_config = dict(skill.crew_config or {})
    crew_config["publish_readiness"] = {
        "test_run_at": datetime.now(timezone.utc).isoformat(),
        "test_workflow_id": workflow_id,
        "passed": None,
        "status": "running",
        "delivery_quality": None,
        "task_preview": task_description[:240],
    }
    updated = await skill_repo.update(skill_id, ExpertSkillUpdate(crew_config=crew_config))
    assert updated is not None

    return {
        "workflow_id": workflow_id,
        "status": "running",
        "passed": None,
        "message_th": "เริ่มทดสอบแล้ว — ดูความคืบหน้าได้เลย เมื่อเสร็จกลับมาเปิดขายได้",
        "message_en": "Test started — watch progress. Come back to publish when it finishes.",
        "skill": updated,
    }


@router.post("/me/skills/{skill_id}/test-run/finalize")
async def finalize_creator_skill_test_run(
    skill_id: str,
    body: CreatorTestRunFinalizeRequest,
    current_user: User = Depends(get_current_user),
    skill_repo: ExpertSkillRepository = Depends(get_expert_skill_repository),
    workflow_service: WorkflowService = Depends(get_workflow_service),
) -> dict:
    """Record test-run pass/fail after background workflow completes."""
    from datetime import datetime, timezone

    skill = await skill_repo.get_by_id(skill_id)
    if skill is None:
        raise HTTPException(status_code=404, detail=f"Expert skill '{skill_id}' not found")
    require_resource_owner(skill.owner_id, current_user)

    try:
        workflow_state, _billing = await workflow_service.get_status(
            body.workflow_id, user_id=current_user.id
        )
    except WorkflowNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except WorkflowPermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc

    assessment = _assess_test_run(skill, dict(workflow_state))
    passed = assessment["passed"]
    delivery_quality = assessment["delivery_quality"]

    if passed:
        msg_th = "ทดสอบผ่านแล้ว — pipeline ส่งมอบได้จริง พร้อมเปิดขายเมื่อคุณพร้อม"
        msg_en = "Test passed — pipeline delivered. Publish when you are ready."
    elif delivery_quality == "degraded":
        msg_th = "ทดสอบเสร็จแต่บางขั้นยังอ่อน — ลองปรับ SKILL.md แล้วรันอีกครั้ง เราอยู่ข้างคุณ"
        msg_en = "Test finished with partial delivery — tweak SKILL.md and retry. We are beside you."
    elif assessment["status"] == "running":
        msg_th = "ยังรันอยู่ — รอสักครู่แล้วกลับมาอีกที"
        msg_en = "Still running — check back in a moment."
        passed = None
    else:
        msg_th = "ทดสอบยังไม่ผ่าน — ปรับคำอธิบายแล้วลองใหม่ ไม่เป็นไร ค่อยๆ ทำได้"
        msg_en = "Test did not pass yet — adjust and retry. No rush."

    crew_config = dict(skill.crew_config or {})
    crew_config["publish_readiness"] = {
        **(crew_config.get("publish_readiness") or {}),
        "finalized_at": datetime.now(timezone.utc).isoformat(),
        "test_workflow_id": body.workflow_id,
        "passed": passed,
        "status": assessment["status"],
        "delivery_quality": delivery_quality,
    }
    updated = await skill_repo.update(skill_id, ExpertSkillUpdate(crew_config=crew_config))
    assert updated is not None

    return {
        "workflow_id": body.workflow_id,
        "status": assessment["status"],
        "passed": passed,
        "delivery_quality": delivery_quality,
        "message_th": msg_th,
        "message_en": msg_en,
        "skill": updated,
    }


@router.delete("/me/skills/{skill_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_creator_skill(
    skill_id: str,
    current_user: User = Depends(get_current_user),
    skill_repo: ExpertSkillRepository = Depends(get_expert_skill_repository),
) -> None:
    skill = await skill_repo.get_by_id(skill_id)
    if skill is None:
        raise HTTPException(status_code=404, detail=f"Expert skill '{skill_id}' not found")
    require_resource_owner(skill.owner_id, current_user)
    await skill_repo.delete(skill_id)


@router.get("/me/analytics", response_model=CreatorAnalytics)
async def get_creator_analytics(
    period: str = Query(default="week", pattern="^(day|week|month)$"),
    current_user: User = Depends(get_current_user),
    creator_repo: CreatorRepository = Depends(get_creator_repository),
) -> CreatorAnalytics:
    return await creator_repo.get_analytics(current_user.id, period=period)


@router.get("/me/payouts", response_model=CreatorPayouts)
async def get_creator_payouts(
    current_user: User = Depends(get_current_user),
    creator_repo: CreatorRepository = Depends(get_creator_repository),
    billing: BillingService = Depends(get_billing_service),
) -> CreatorPayouts:
    wallet = await billing.get_wallet(
        current_user.id,
        initial_balance=Decimal(str(settings.signup_credits_usd)),
    )
    earnings = await billing.get_earnings_summary(current_user.id)
    return await creator_repo.get_payouts(
        current_user.id,
        earnings_balance_usd=wallet.earnings_balance_usd,
        total_earned_usd=earnings.total_earned_usd,
    )


@router.get("/me/reviews", response_model=CreatorReviewsSummary)
async def get_creator_reviews(
    current_user: User = Depends(get_current_user),
    creator_repo: CreatorRepository = Depends(get_creator_repository),
) -> CreatorReviewsSummary:
    return await creator_repo.get_reviews(current_user.id)


@router.post("/me/showcases/from-workflow", response_model=SkillShowcase, status_code=status.HTTP_201_CREATED)
async def create_showcase_from_workflow(
    payload: ShowcaseFromWorkflowCreate,
    current_user: User = Depends(get_current_user),
    skill_repo: ExpertSkillRepository = Depends(get_expert_skill_repository),
    showcase_service: ShowcaseService = Depends(get_showcase_service),
    workflow_service: WorkflowService = Depends(get_workflow_service),
) -> SkillShowcase:
    try:
        state, _billing = await workflow_service.get_status(
            payload.workflow_id,
            user_id=current_user.id,
        )
    except WorkflowNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except WorkflowPermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc

    task_context = state.get("task_context") or {}
    expert_skill_id = task_context.get("expert_skill_id")
    if not expert_skill_id:
        raise HTTPException(
            status_code=400,
            detail="Only expert-skill workflow runs can be published as case studies.",
        )

    skill = await skill_repo.get_by_id(str(expert_skill_id))
    if skill is None:
        raise HTTPException(status_code=404, detail="Expert skill for this workflow not found.")
    require_resource_owner(skill.owner_id, current_user)

    try:
        return await showcase_service.create_from_workflow(
            skill=skill,
            workflow_id=payload.workflow_id,
            workflow_state=dict(state),
            title=payload.title,
            site_name=payload.site_name,
            site_url=payload.site_url,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/me/tools", response_model=list[CustomTool])
async def list_creator_tools(
    current_user: User = Depends(get_current_user),
    tool_repo: CustomToolRepository = Depends(get_custom_tool_repository),
) -> list[CustomTool]:
    return await tool_repo.list_all(active_only=False, owner_id=current_user.id)


@router.get("/me/mcp-servers", response_model=list[MCPServer])
async def list_creator_mcp_servers(
    current_user: User = Depends(get_current_user),
    mcp_repo: MCPServerRepository = Depends(get_mcp_server_repository),
) -> list[MCPServer]:
    return await mcp_repo.list_servers(active_only=False, owner_id=current_user.id)