from fastapi import APIRouter, Depends, HTTPException, Query

from app.core.deps import get_showcase_repository
from app.models.showcase import SkillShowcase
from app.repositories.showcase_repository import ShowcaseRepository

router = APIRouter()


@router.get("", response_model=list[SkillShowcase])
async def list_showcases(
    category: str | None = Query(default=None),
    featured_only: bool = Query(default=False),
    expert_skill_id: str | None = Query(default=None),
    repository: ShowcaseRepository = Depends(get_showcase_repository),
) -> list[SkillShowcase]:
    try:
        return await repository.list_all(
            active_only=True,
            category=category,
            featured_only=featured_only,
            expert_skill_id=expert_skill_id,
        )
    except Exception:
        # Avoid 500 on UI loads if data or join issue
        return []


@router.get("/{showcase_id}", response_model=SkillShowcase)
async def get_showcase(
    showcase_id: str,
    repository: ShowcaseRepository = Depends(get_showcase_repository),
) -> SkillShowcase:
    showcase = await repository.get_by_id(showcase_id)
    if showcase is None or not showcase.is_active:
        raise HTTPException(status_code=404, detail=f"Showcase '{showcase_id}' not found")
    return showcase