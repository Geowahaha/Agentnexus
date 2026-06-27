from fastapi import APIRouter, Depends, HTTPException, Query

from app.auth.dependencies import get_current_user
from app.auth.models import User
from app.core.deps import get_expert_skill_repository, get_user_repository, get_workflow_service
from app.expert_skills.attribution import skill_attribution
from app.expert_skills.skill_locale import pick_locale_copy
from app.expert_skills.thai_copy import ensure_obolla_thai_i18n
from app.expert_skills.custom_defaults import resolve_crew_config
from app.expert_skills.pack_loader import load_skill_pack
from app.expert_skills.model_tiers import effective_marketplace_price_usd, runtime_tier_meta
from app.models.expert_skill import (
    ExpertSkill,
    ExpertSkillDetail,
    ModelTierRuntimeInfo,
    PipelineStepInfo,
    SkillAttribution,
    SkillAttributionLink,
)
from app.repositories.expert_skill_repository import ExpertSkillRepository
from app.repositories.user_repository import UserRepository
from app.services.workflow_service import WorkflowService

router = APIRouter()

SYSTEM_OWNER_LABEL = "AIBotAuth"


def _pipeline_steps(crew_config: dict) -> list[PipelineStepInfo]:
    steps: list[PipelineStepInfo] = []
    for step in crew_config.get("steps") or []:
        step_type = str(step.get("type") or "llm")
        if step_type == "mcp":
            tool = step.get("tool") or "mcp tool"
            steps.append(
                PipelineStepInfo(
                    id=str(step.get("id") or "scan"),
                    title=str(step.get("title") or "Scanner"),
                    step_type="tool",
                    tool_or_model=str(tool),
                )
            )
        elif step_type == "llm":
            steps.append(
                PipelineStepInfo(
                    id=str(step.get("id") or "llm"),
                    title=str(step.get("title") or "AI step"),
                    step_type="model",
                    tool_or_model=str(step.get("model") or "llm"),
                )
            )
        elif step_type == "agent_ready":
            action = str(step.get("action") or "analyze")
            steps.append(
                PipelineStepInfo(
                    id=str(step.get("id") or "agent_ready"),
                    title=str(step.get("title") or "Agent-Ready"),
                    step_type="tool",
                    tool_or_model=f"agent-ready/{action}",
                )
            )
        elif step_type == "media":
            provider = step.get("provider") or "media"
            steps.append(
                PipelineStepInfo(
                    id=str(step.get("id") or "render"),
                    title=str(step.get("title") or "Media render"),
                    step_type="tool",
                    tool_or_model=str(provider),
                )
            )
        elif step_type == "image_gen":
            model = step.get("model") or step.get("provider") or "image_gen"
            steps.append(
                PipelineStepInfo(
                    id=str(step.get("id") or "image_generate"),
                    title=str(step.get("title") or "Image generation"),
                    step_type="tool",
                    tool_or_model=str(model),
                )
            )
    return steps


async def _resolve_skill_locale(
    skill: ExpertSkill,
    lang: str | None,
    *,
    repository: ExpertSkillRepository | None = None,
    auto_translate: bool = False,
) -> ExpertSkill:
    name, description, display_locale = pick_locale_copy(skill, lang)
    if display_locale == "th" or lang != "th" or repository is None or not auto_translate:
        return skill.model_copy(update={"name": name, "description": description, "display_locale": display_locale})

    skill = await ensure_obolla_thai_i18n(repository, skill)
    name, description, display_locale = pick_locale_copy(skill, "th")

    return skill.model_copy(update={"name": name, "description": description, "display_locale": display_locale})


async def _to_detail(
    skill: ExpertSkill,
    *,
    user_repository: UserRepository | None = None,
) -> ExpertSkillDetail:
    resolved = resolve_crew_config(
        skill.pack_slug,
        skill.crew_config,
        category=skill.category,
        name=skill.name,
        description=skill.description,
    )
    inline_md = resolved.get("skill_md")
    try:
        pack = load_skill_pack(skill.pack_slug)
        pack_md = pack["skill_md"]
        preview_source = inline_md if isinstance(inline_md, str) and inline_md.strip() else pack_md
        preview = preview_source[:600] + "…" if len(preview_source) > 600 else preview_source
        ref_count = len(pack.get("references") or {})
    except FileNotFoundError:
        if isinstance(inline_md, str) and inline_md.strip():
            preview = inline_md[:600] + "…" if len(inline_md) > 600 else inline_md
        else:
            preview = None
        ref_count = 0

    owner_name = SYSTEM_OWNER_LABEL
    if user_repository is not None:
        resolved_name = await user_repository.get_full_name_by_id(skill.owner_id)
        if resolved_name:
            owner_name = resolved_name

    attr_raw = skill_attribution(
        pack_slug=skill.pack_slug,
        price_usd_per_run=float(skill.price_usd_per_run),
    )
    attribution = SkillAttribution(
        charter_summary=attr_raw["charter_summary"],
        pack_slug=attr_raw["pack_slug"],
        upstream=[SkillAttributionLink(**link) for link in attr_raw["upstream"]],
        obolla_layer=attr_raw["obolla_layer"],
        pricing_honesty=attr_raw["pricing_honesty"],
        credits_markdown=attr_raw.get("credits_markdown"),
    )

    tier_meta = runtime_tier_meta(resolved)
    effective_price = effective_marketplace_price_usd(
        listed_price_usd=skill.price_usd_per_run,
        crew_config=skill.crew_config,
    )
    tier_info = ModelTierRuntimeInfo(
        downgraded=bool(tier_meta.get("downgraded")),
        requested_tier_id=tier_meta.get("requested_tier_id"),
        effective_tier_id=tier_meta.get("effective_tier_id"),
        effective_price_usd=str(effective_price),
        listed_price_usd=str(skill.price_usd_per_run),
        note_en=resolved.get("runtime_note_en"),
        note_th=resolved.get("runtime_note_th"),
    )

    payload = skill.model_dump()
    payload["crew_config"] = resolved
    return ExpertSkillDetail(
        **payload,
        skill_preview=preview,
        reference_count=ref_count,
        owner_name=owner_name,
        pipeline_steps=_pipeline_steps(resolved),
        attribution=attribution,
        model_tier_runtime=tier_info if skill.pack_slug == "custom" else None,
    )


@router.get("", response_model=list[ExpertSkillDetail])
async def list_expert_skills(
    category: str | None = Query(default=None),
    lang: str | None = Query(default=None, description="th or en — localized name/description"),
    repository: ExpertSkillRepository = Depends(get_expert_skill_repository),
    user_repository: UserRepository = Depends(get_user_repository),
) -> list[ExpertSkillDetail]:
    skills = await repository.list_all(active_only=True, category=category)
    localized = [
        await _resolve_skill_locale(skill, lang, repository=repository, auto_translate=False)
        for skill in skills
    ]
    return [await _to_detail(skill, user_repository=user_repository) for skill in localized]


@router.get("/{skill_id}", response_model=ExpertSkillDetail)
async def get_expert_skill(
    skill_id: str,
    lang: str | None = Query(default=None, description="th or en — localized name/description"),
    repository: ExpertSkillRepository = Depends(get_expert_skill_repository),
    user_repository: UserRepository = Depends(get_user_repository),
) -> ExpertSkillDetail:
    skill = await repository.get_by_id(skill_id)
    if skill is None:
        skill = await repository.get_by_slug(skill_id)
    if skill is None:
        raise HTTPException(status_code=404, detail=f"Expert skill '{skill_id}' not found")
    skill = await _resolve_skill_locale(skill, lang, repository=repository, auto_translate=True)
    return await _to_detail(skill, user_repository=user_repository)


@router.post("/{skill_id}/run")
async def run_expert_skill(
    skill_id: str,
    payload: dict,
    current_user: User = Depends(get_current_user),
    repository: ExpertSkillRepository = Depends(get_expert_skill_repository),
    workflow_service: WorkflowService = Depends(get_workflow_service),
):
    skill = await repository.get_by_id(skill_id)
    if skill is None:
        skill = await repository.get_by_slug(skill_id)
    if skill is None:
        raise HTTPException(status_code=404, detail=f"Expert skill '{skill_id}' not found")

    task_description = str(payload.get("task_description") or "").strip()
    if not task_description:
        raise HTTPException(status_code=400, detail="task_description is required")

    try:
        result, billing = await workflow_service.run(
            user_id=current_user.id,
            task_description=task_description,
            workflow_type="expert_skill",
            task_context={
                "expert_skill_id": skill.id,
                "expert_skill_slug": skill.slug,
            },
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Workflow failed: {exc}") from exc

    from app.api.routes.workflows import _to_response

    return _to_response(result, billing)