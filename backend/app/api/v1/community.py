import re
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, UploadFile
from pydantic import BaseModel, Field
from sqlalchemy import func, select

from app.core.deps import get_expert_skill_repository, get_session, get_user_repository
from app.db.models.creator_earning import CreatorEarningORM
from app.repositories.expert_skill_repository import ExpertSkillRepository
from app.repositories.user_repository import UserRepository
from app.expert_skills.model_tiers import (
    apply_model_tier_to_crew_config,
    garden_model_tiers as get_garden_model_tiers_payload,
    suggested_price_usd,
)
from app.core.obolla_dna import vision_payload
from app.services.creator_garden_service import coach_creator_garden, compose_creator_garden
from app.services.publish_insight_service import generate_publish_insight
from app.services.dna_audit_service import run_dna_audit
from app.services.pdf_skill_import_service import import_skill_from_pdf

router = APIRouter()


class CreatorGardenCoachRequest(BaseModel):
    step: str = Field(..., min_length=1, max_length=40)
    answers: dict[str, str | int | float | bool | None] = Field(default_factory=dict)


class CreatorGardenComposeRequest(BaseModel):
    raw_story: str = Field(..., min_length=1, max_length=8000)
    locale: str = Field(default="th", min_length=2, max_length=5)
    model_tier_id: str = Field(default="standard", min_length=1, max_length=40)


class CreatorGardenApplyTierRequest(BaseModel):
    model_tier_id: str = Field(..., min_length=1, max_length=40)
    crew_config: dict[str, Any] = Field(default_factory=dict)


class CreatorGardenValueInsightRequest(BaseModel):
    raw_story: str = Field(default="", max_length=8000)
    locale: str = Field(default="th", min_length=2, max_length=5)
    workflow_name: str = Field(..., min_length=1, max_length=200)
    description: str = Field(default="", max_length=2000)
    category: str = Field(default="quality", max_length=40)
    identity: str = Field(default="", max_length=500)
    audience: str = Field(default="", max_length=300)
    problem: str = Field(default="", max_length=500)
    model_tier_id: str = Field(default="standard", min_length=1, max_length=40)


@router.get("/leaderboard")
async def community_leaderboard(
    skill_repo: ExpertSkillRepository = Depends(get_expert_skill_repository),
    user_repo: UserRepository = Depends(get_user_repository),
    session=Depends(get_session),
) -> list[dict]:
    skills = await skill_repo.list_all(active_only=True)
    by_owner: dict[str, dict] = {}

    for skill in skills:
        owner = skill.owner_id
        entry = by_owner.setdefault(
            owner,
            {
                "owner_id": owner,
                "owner_name": None,
                "flow_count": 0,
                "categories": [],
                "featured_flow": None,
            },
        )
        entry["flow_count"] += 1
        cats = set(entry["categories"])
        if skill.category:
            cats.add(skill.category)
        entry["categories"] = sorted(cats)
        price = float(skill.price_usd_per_run)
        featured = entry["featured_flow"]
        if featured is None or price > float(featured.get("price_usd_per_run") or 0):
            entry["featured_flow"] = {
                "id": skill.id,
                "name": skill.name,
                "slug": skill.slug,
                "price_usd_per_run": str(skill.price_usd_per_run),
            }

    earning_counts: dict[str, int] = {}
    if by_owner:
        owner_ids = [UUID(oid) for oid in by_owner]
        result = await session.execute(
            select(CreatorEarningORM.creator_id, func.count())
            .where(CreatorEarningORM.creator_id.in_(owner_ids))
            .group_by(CreatorEarningORM.creator_id)
        )
        earning_counts = {str(row[0]): int(row[1]) for row in result.all()}

    rows: list[dict] = []
    for entry in by_owner.values():
        name = await user_repo.get_full_name_by_id(entry["owner_id"])
        entry["owner_name"] = name or "Creator"
        entry["earning_runs"] = earning_counts.get(entry["owner_id"], 0)
        rows.append(entry)

    rows.sort(
        key=lambda row: (
            -row["earning_runs"],
            -row["flow_count"],
            row["owner_name"],
        )
    )
    return rows[:12]


@router.get("/vision")
async def community_vision() -> dict:
    return vision_payload()


@router.get("/dna-audit")
async def community_dna_audit() -> dict:
    """Provable DNA alignment report — every platform claim backed by evidence."""
    return run_dna_audit()


@router.post("/creator-garden/coach")
async def creator_garden_coach(body: CreatorGardenCoachRequest) -> dict:
    """Free companion coach for new creators — always $0, no auth required."""
    step = re.sub(r"[^a-z0-9_-]", "", body.step.lower()) or "identity"
    return coach_creator_garden(step, body.answers)


@router.get("/creator-garden/model-tiers")
async def creator_garden_model_tiers() -> dict:
    """Model tier catalog for Creator Garden — price adds on top of base $0.99."""
    return get_garden_model_tiers_payload()


@router.post("/creator-garden/apply-tier")
async def creator_garden_apply_tier(body: CreatorGardenApplyTierRequest) -> dict:
    """Re-price and re-wire pipeline models without re-running the composer LLM."""
    tier_id = re.sub(r"[^a-z0-9_-]", "", body.model_tier_id.lower()) or "standard"
    crew = apply_model_tier_to_crew_config(body.crew_config, tier_id)
    return {
        "model_tier_id": tier_id,
        "suggested_price_usd": suggested_price_usd(tier_id),
        "pipeline_label": crew.get("pipeline_label"),
        "crew_config": crew,
    }


@router.post("/creator-garden/compose")
async def creator_garden_compose(body: CreatorGardenComposeRequest) -> dict:
    """Free LLM composer — polish rough story into agent-flow draft ($0, no auth)."""
    locale = "th" if body.locale.lower().startswith("th") else "en"
    tier_id = re.sub(r"[^a-z0-9_-]", "", body.model_tier_id.lower()) or "standard"
    return await compose_creator_garden(
        raw_story=body.raw_story,
        locale=locale,
        model_tier_id=tier_id,
    )


@router.post("/creator-garden/value-insight")
async def creator_garden_value_insight(body: CreatorGardenValueInsightRequest) -> dict:
    """Free trend + value research for pre-publish — personalized price rationale ($0, no auth)."""
    locale = "th" if body.locale.lower().startswith("th") else "en"
    tier_id = re.sub(r"[^a-z0-9_-]", "", body.model_tier_id.lower()) or "standard"
    return await generate_publish_insight(
        raw_story=body.raw_story,
        locale=locale,
        workflow_name=body.workflow_name.strip(),
        description=body.description.strip(),
        category=body.category.strip().lower() or "quality",
        identity=body.identity.strip(),
        audience=body.audience.strip(),
        problem=body.problem.strip(),
        model_tier_id=tier_id,
    )


@router.post("/creator-garden/import-pdf")
async def creator_garden_import_pdf(
    file: UploadFile = File(...),
    locale: str = Form(default="th"),
    model_tier_id: str = Form(default="standard"),
) -> dict:
    """Free PDF → agent-flow draft ($0, no auth). PDF is processed in memory — not stored."""
    loc = "th" if locale.lower().startswith("th") else "en"
    tier_id = re.sub(r"[^a-z0-9_-]", "", model_tier_id.lower()) or "standard"
    return await import_skill_from_pdf(upload=file, locale=loc, model_tier_id=tier_id)