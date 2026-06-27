from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from fastapi.responses import FileResponse

from app.auth.dependencies import get_current_user
from app.auth.models import User
from app.core.config import settings
from app.core.deps import (
    get_notification_repository,
    get_review_attachment_service,
    get_review_inbox_repository,
)
from app.repositories.notification_repository import NotificationRepository
from app.models.review_inbox import (
    QuickReply,
    QuickReplyCreate,
    QuickReplyUpdate,
    ReviewInboxResponse,
    ReviewNotificationBadge,
    ReviewNotificationSettings,
    ReviewThread,
    ThreadMessage,
)
from app.repositories.review_inbox_repository import ReviewInboxRepository
from app.services.review_attachment_service import ReviewAttachmentService

router = APIRouter()


@router.get("/inbox", response_model=ReviewInboxResponse)
async def get_review_inbox(
    status: str | None = Query(default=None, alias="status"),
    rating: int | None = Query(default=None, ge=1, le=5),
    search: str | None = Query(default=None),
    sort: str = Query(default="newest", pattern="^(newest|unanswered|response_time)$"),
    current_user: User = Depends(get_current_user),
    repository: ReviewInboxRepository = Depends(get_review_inbox_repository),
) -> ReviewInboxResponse:
    return await repository.get_inbox(
        current_user.id,
        status_filter=status,
        rating_filter=rating,
        search=search,
        sort=sort,
        api_prefix=settings.api_prefix,
    )


@router.get("/inbox/badge", response_model=ReviewNotificationBadge)
async def get_review_inbox_badge(
    current_user: User = Depends(get_current_user),
    repository: ReviewInboxRepository = Depends(get_review_inbox_repository),
) -> ReviewNotificationBadge:
    return await repository.get_notification_badge(current_user.id)


@router.get("/quick-replies", response_model=list[QuickReply])
async def list_quick_replies(
    current_user: User = Depends(get_current_user),
    repository: ReviewInboxRepository = Depends(get_review_inbox_repository),
) -> list[QuickReply]:
    return await repository.list_quick_replies(current_user.id)


@router.post("/quick-replies", response_model=QuickReply, status_code=status.HTTP_201_CREATED)
async def create_quick_reply(
    payload: QuickReplyCreate,
    current_user: User = Depends(get_current_user),
    repository: ReviewInboxRepository = Depends(get_review_inbox_repository),
) -> QuickReply:
    return await repository.create_quick_reply(current_user.id, payload)


@router.patch("/quick-replies/{reply_id}", response_model=QuickReply)
async def update_quick_reply(
    reply_id: str,
    payload: QuickReplyUpdate,
    current_user: User = Depends(get_current_user),
    repository: ReviewInboxRepository = Depends(get_review_inbox_repository),
) -> QuickReply:
    try:
        return await repository.update_quick_reply(current_user.id, reply_id, payload)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.delete("/quick-replies/{reply_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_quick_reply(
    reply_id: str,
    current_user: User = Depends(get_current_user),
    repository: ReviewInboxRepository = Depends(get_review_inbox_repository),
) -> None:
    try:
        await repository.delete_quick_reply(current_user.id, reply_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/notification-settings", response_model=ReviewNotificationSettings)
async def get_notification_settings(
    current_user: User = Depends(get_current_user),
    repository: ReviewInboxRepository = Depends(get_review_inbox_repository),
) -> ReviewNotificationSettings:
    return await repository.get_notification_settings(current_user.id)


@router.put("/notification-settings", response_model=ReviewNotificationSettings)
async def update_notification_settings(
    payload: ReviewNotificationSettings,
    current_user: User = Depends(get_current_user),
    repository: ReviewInboxRepository = Depends(get_review_inbox_repository),
) -> ReviewNotificationSettings:
    try:
        return await repository.update_notification_settings(current_user.id, payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/attachments/{attachment_id}/download")
async def download_review_attachment(
    attachment_id: str,
    current_user: User = Depends(get_current_user),
    repository: ReviewInboxRepository = Depends(get_review_inbox_repository),
    attachment_service: ReviewAttachmentService = Depends(get_review_attachment_service),
):
    try:
        attachment = await repository.get_attachment_for_creator(current_user.id, attachment_id)
        path = attachment_service.resolve_path(attachment.storage_path)
        return FileResponse(path, filename=attachment.file_name, media_type=attachment.content_type)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail="File not found") from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/{review_id}/thread", response_model=ReviewThread)
async def get_review_thread(
    review_id: str,
    current_user: User = Depends(get_current_user),
    repository: ReviewInboxRepository = Depends(get_review_inbox_repository),
) -> ReviewThread:
    try:
        return await repository.get_thread(current_user.id, review_id, api_prefix=settings.api_prefix)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/{review_id}/reply", response_model=ThreadMessage)
async def reply_to_review(
    review_id: str,
    body: str = Form(..., min_length=1),
    files: list[UploadFile] = File(default=[]),
    current_user: User = Depends(get_current_user),
    repository: ReviewInboxRepository = Depends(get_review_inbox_repository),
    attachment_service: ReviewAttachmentService = Depends(get_review_attachment_service),
    notifications: NotificationRepository = Depends(get_notification_repository),
):
    from uuid import uuid4

    message_id = str(uuid4())
    attachment_meta: list[tuple[str, str, int, str]] = []
    try:
        for upload in files:
            if not upload.filename:
                continue
            meta = await attachment_service.save_upload(message_id, upload)
            attachment_meta.append(meta)
        return await repository.add_creator_reply(
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


@router.post("/{review_id}/resolve")
async def resolve_review(
    review_id: str,
    current_user: User = Depends(get_current_user),
    repository: ReviewInboxRepository = Depends(get_review_inbox_repository),
    notifications: NotificationRepository = Depends(get_notification_repository),
):
    try:
        item = await repository.resolve_review(
            current_user.id,
            review_id,
            notifications=notifications,
        )
        return {"ok": True, "item": item}
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc