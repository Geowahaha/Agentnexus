from uuid import uuid4

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from fastapi.responses import FileResponse

from app.auth.dependencies import get_current_user
from app.auth.models import User
from app.core.config import settings
from app.core.deps import (
    get_buyer_review_repository,
    get_expert_skill_repository,
    get_notification_repository,
    get_review_attachment_service,
    get_workflow_service,
)
from app.repositories.expert_skill_repository import ExpertSkillRepository
from app.models.buyer_review import (
    BuyerReviewItem,
    BuyerReviewSubmit,
    BuyerReviewSubmitted,
    WorkflowReviewEligibility,
)
from app.models.review_inbox import ReviewThread, ThreadMessage
from app.repositories.buyer_review_repository import BuyerReviewRepository
from app.repositories.notification_repository import NotificationRepository
from app.services.review_attachment_service import ReviewAttachmentService
from app.services.workflow_service import WorkflowNotFoundError, WorkflowPermissionError, WorkflowService

router = APIRouter()


def _completed_status(status: str) -> bool:
    return status == "completed"


@router.get("/me/workflow/{workflow_id}/eligibility", response_model=WorkflowReviewEligibility)
async def get_workflow_review_eligibility(
    workflow_id: str,
    current_user: User = Depends(get_current_user),
    workflow_service: WorkflowService = Depends(get_workflow_service),
    buyer_repo: BuyerReviewRepository = Depends(get_buyer_review_repository),
    skill_repo: ExpertSkillRepository = Depends(get_expert_skill_repository),
) -> WorkflowReviewEligibility:
    try:
        result, _billing = await workflow_service.get_status(workflow_id, user_id=current_user.id)
    except WorkflowNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except WorkflowPermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc

    workflow_type = result.get("workflow_type")
    if workflow_type != "expert_skill":
        return WorkflowReviewEligibility(
            eligible=False,
            reason="Reviews are only available for Expert Skill runs",
            workflow_id=workflow_id,
            workflow_status=result.get("status"),
        )

    if not _completed_status(str(result.get("status"))):
        return WorkflowReviewEligibility(
            eligible=False,
            reason="Workflow must complete before you can leave a review",
            workflow_id=workflow_id,
            workflow_status=result.get("status"),
        )

    task_context = result.get("task_context") or {}
    expert_skill_id = task_context.get("expert_skill_id")
    if not expert_skill_id:
        return WorkflowReviewEligibility(
            eligible=False,
            reason="Expert skill context missing from workflow",
            workflow_id=workflow_id,
            workflow_status=result.get("status"),
        )

    skill = await skill_repo.get_by_id(str(expert_skill_id))
    if skill is None:
        return WorkflowReviewEligibility(
            eligible=False,
            reason="Expert skill not found",
            workflow_id=workflow_id,
        )

    existing = await buyer_repo.get_review_for_buyer(current_user.id, str(expert_skill_id))
    existing_item = await buyer_repo._to_buyer_item(existing) if existing else None

    return WorkflowReviewEligibility(
        eligible=True,
        workflow_id=workflow_id,
        workflow_status=result.get("status"),
        expert_skill_id=str(expert_skill_id),
        skill_name=skill.name,
        skill_slug=skill.slug,
        already_reviewed=existing is not None,
        existing_review=existing_item,
    )


@router.get("/me", response_model=list[BuyerReviewItem])
async def list_my_reviews(
    current_user: User = Depends(get_current_user),
    buyer_repo: BuyerReviewRepository = Depends(get_buyer_review_repository),
) -> list[BuyerReviewItem]:
    return await buyer_repo.list_reviews(current_user.id)


@router.post("/me", response_model=BuyerReviewSubmitted, status_code=status.HTTP_201_CREATED)
async def submit_review(
    payload: BuyerReviewSubmit,
    current_user: User = Depends(get_current_user),
    buyer_repo: BuyerReviewRepository = Depends(get_buyer_review_repository),
    notifications: NotificationRepository = Depends(get_notification_repository),
    workflow_service: WorkflowService = Depends(get_workflow_service),
) -> BuyerReviewSubmitted:
    try:
        result, _billing = await workflow_service.get_status(payload.workflow_id, user_id=current_user.id)
    except WorkflowNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except WorkflowPermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc

    if result.get("workflow_type") != "expert_skill":
        raise HTTPException(status_code=400, detail="Only expert skill workflows can be reviewed")
    if not _completed_status(str(result.get("status"))):
        raise HTTPException(status_code=400, detail="Workflow must be completed before reviewing")

    task_context = result.get("task_context") or {}
    skill_id = str(task_context.get("expert_skill_id") or "")
    if skill_id != payload.expert_skill_id:
        raise HTTPException(status_code=400, detail="expert_skill_id does not match workflow")

    try:
        return await buyer_repo.submit_review(
            current_user.id,
            expert_skill_id=payload.expert_skill_id,
            workflow_id=payload.workflow_id,
            rating=payload.rating,
            comment=payload.comment,
            notifications=notifications,
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/me/{review_id}/thread", response_model=ReviewThread)
async def get_buyer_thread(
    review_id: str,
    current_user: User = Depends(get_current_user),
    buyer_repo: BuyerReviewRepository = Depends(get_buyer_review_repository),
) -> ReviewThread:
    try:
        return await buyer_repo.get_thread(
            current_user.id,
            review_id,
            api_prefix=settings.api_prefix,
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/me/{review_id}/reply", response_model=ThreadMessage)
async def reply_in_thread(
    review_id: str,
    body: str = Form(..., min_length=1),
    files: list[UploadFile] = File(default=[]),
    current_user: User = Depends(get_current_user),
    buyer_repo: BuyerReviewRepository = Depends(get_buyer_review_repository),
    notifications: NotificationRepository = Depends(get_notification_repository),
    attachment_service: ReviewAttachmentService = Depends(get_review_attachment_service),
):
    message_id = str(uuid4())
    attachment_meta: list[tuple[str, str, int, str]] = []
    try:
        for upload in files:
            if not upload.filename:
                continue
            meta = await attachment_service.save_upload(message_id, upload)
            attachment_meta.append(meta)
        return await buyer_repo.add_buyer_reply(
            current_user.id,
            review_id,
            body=body,
            message_id=message_id,
            attachment_meta=attachment_meta,
            api_prefix=settings.api_prefix,
            notifications=notifications,
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/me/attachments/{attachment_id}/download")
async def download_buyer_attachment(
    attachment_id: str,
    current_user: User = Depends(get_current_user),
    buyer_repo: BuyerReviewRepository = Depends(get_buyer_review_repository),
    attachment_service: ReviewAttachmentService = Depends(get_review_attachment_service),
):
    try:
        attachment = await buyer_repo.get_attachment_for_buyer(current_user.id, attachment_id)
        path = attachment_service.resolve_path(attachment.storage_path)
        return FileResponse(path, filename=attachment.file_name, media_type=attachment.content_type)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail="File not found") from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc