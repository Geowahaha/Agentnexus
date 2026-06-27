from datetime import datetime, timezone
from uuid import UUID, uuid4

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models.expert_skill import ExpertSkillORM
from app.db.models.review_inbox import (
    CreatorQuickReplyORM,
    CreatorReviewNotificationSettingsORM,
    ReviewMessageAttachmentORM,
    ReviewThreadMessageORM,
)
from app.db.models.skill_review import SkillReviewORM
from app.db.models.user import UserORM
from app.models.review_inbox import (
    QuickReply,
    QuickReplyCreate,
    QuickReplyUpdate,
    ReviewAttachment,
    ReviewInboxItem,
    ReviewInboxResponse,
    ReviewInboxStats,
    ReviewNotificationBadge,
    ReviewNotificationSettings,
    ReviewThread,
    ThreadMessage,
)

DEFAULT_QUICK_REPLIES = [
    ("Thank you!", "ขอบคุณสำหรับรีวิวครับ! ยินดีที่ skill นี้ช่วยคุณได้"),
    ("Feedback noted", "ขอบคุณสำหรับข้อเสนอแนะครับ เราจะนำไปปรับปรุงในเวอร์ชันถัดไป"),
    ("Happy to help", "ยินดีช่วยเหลือครับ หากมีคำถามเพิ่มเติม สามารถสอบถามได้เลย"),
]


def _avatar_url(name: str) -> str:
    encoded = name.strip().replace(" ", "+") or "User"
    return f"https://ui-avatars.com/api/?name={encoded}&background=1a222d&color=22d3ee&size=64"


def _format_response_time(hours: float | None) -> str | None:
    if hours is None:
        return None
    if hours < 1:
        return f"ตอบกลับเฉลี่ยภายใน {int(hours * 60)} นาที"
    if hours < 24:
        return f"ตอบกลับเฉลี่ยภายใน {hours:.1f} ชั่วโมง"
    return f"ตอบกลับเฉลี่ยภายใน {hours / 24:.1f} วัน"


def _hours_between(start: datetime, end: datetime) -> float:
    delta = end - start
    return round(delta.total_seconds() / 3600, 2)


class ReviewInboxRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def _skill_ids_for_creator(self, creator_id: str) -> list[UUID]:
        result = await self._session.execute(
            select(ExpertSkillORM.id).where(ExpertSkillORM.owner_id == UUID(creator_id))
        )
        return list(result.scalars().all())

    async def _verify_review_access(self, creator_id: str, review_id: str) -> SkillReviewORM:
        skill_ids = await self._skill_ids_for_creator(creator_id)
        if not skill_ids:
            raise KeyError("Review not found")
        result = await self._session.execute(
            select(SkillReviewORM).where(
                SkillReviewORM.id == UUID(review_id),
                SkillReviewORM.expert_skill_id.in_(skill_ids),
            )
        )
        review = result.scalar_one_or_none()
        if review is None:
            raise KeyError("Review not found")
        return review

    async def get_inbox(
        self,
        creator_id: str,
        *,
        status_filter: str | None = None,
        rating_filter: int | None = None,
        search: str | None = None,
        sort: str = "newest",
        api_prefix: str = "/api/v1",
    ) -> ReviewInboxResponse:
        skill_ids = await self._skill_ids_for_creator(creator_id)
        stats = await self._compute_stats(creator_id, skill_ids)

        if not skill_ids:
            return ReviewInboxResponse(stats=stats, items=[])

        msg_count_subq = (
            select(
                ReviewThreadMessageORM.review_id,
                func.count().label("msg_count"),
            )
            .group_by(ReviewThreadMessageORM.review_id)
            .subquery()
        )

        query = (
            select(
                SkillReviewORM,
                ExpertSkillORM.name,
                UserORM.full_name,
                func.coalesce(msg_count_subq.c.msg_count, 0).label("thread_msgs"),
            )
            .join(ExpertSkillORM, ExpertSkillORM.id == SkillReviewORM.expert_skill_id)
            .join(UserORM, UserORM.id == SkillReviewORM.buyer_id)
            .outerjoin(msg_count_subq, msg_count_subq.c.review_id == SkillReviewORM.id)
            .where(SkillReviewORM.expert_skill_id.in_(skill_ids))
        )

        if status_filter and status_filter != "all":
            query = query.where(SkillReviewORM.status == status_filter)
        if rating_filter is not None:
            query = query.where(SkillReviewORM.rating == rating_filter)
        if search:
            term = f"%{search.lower()}%"
            query = query.where(
                or_(
                    func.lower(UserORM.full_name).like(term),
                    func.lower(ExpertSkillORM.name).like(term),
                    func.lower(SkillReviewORM.comment).like(term),
                )
            )

        if sort == "unanswered":
            query = query.order_by(
                SkillReviewORM.status == "unread",
                SkillReviewORM.first_response_at.is_(None),
                SkillReviewORM.created_at.desc(),
            )
        elif sort == "response_time":
            query = query.order_by(
                SkillReviewORM.first_response_at.is_(None),
                SkillReviewORM.first_response_at.asc(),
                SkillReviewORM.created_at.desc(),
            )
        else:
            query = query.order_by(SkillReviewORM.created_at.desc())

        result = await self._session.execute(query)
        items: list[ReviewInboxItem] = []
        for review, skill_name, buyer_name, thread_msgs in result.all():
            preview = review.comment[:140] + ("…" if len(review.comment) > 140 else "")
            response_hours = None
            if review.first_response_at is not None:
                response_hours = _hours_between(review.created_at, review.first_response_at)
            items.append(
                ReviewInboxItem(
                    id=str(review.id),
                    expert_skill_id=str(review.expert_skill_id),
                    skill_name=skill_name,
                    buyer_id=str(review.buyer_id),
                    buyer_name=buyer_name,
                    buyer_avatar_url=_avatar_url(buyer_name),
                    rating=review.rating,
                    comment_preview=preview,
                    status=review.status,
                    is_read=review.is_read,
                    workflow_id=review.workflow_id,
                    created_at=review.created_at,
                    updated_at=review.updated_at,
                    first_response_at=review.first_response_at,
                    response_time_hours=response_hours,
                    message_count=1 + int(thread_msgs),
                )
            )

        return ReviewInboxResponse(stats=stats, items=items)

    async def _compute_stats(self, creator_id: str, skill_ids: list[UUID]) -> ReviewInboxStats:
        if not skill_ids:
            return ReviewInboxStats(
                average_rating=None,
                total_reviews=0,
                unread_count=0,
                response_rate_percent=0.0,
                average_response_time_hours=None,
                average_response_time_label=None,
            )

        base = select(SkillReviewORM).where(SkillReviewORM.expert_skill_id.in_(skill_ids))

        total_result = await self._session.execute(select(func.count()).select_from(base.subquery()))
        total = int(total_result.scalar_one())

        avg_result = await self._session.execute(select(func.avg(SkillReviewORM.rating)).where(
            SkillReviewORM.expert_skill_id.in_(skill_ids)
        ))
        avg_rating = avg_result.scalar_one()
        average_rating = round(float(avg_rating), 2) if avg_rating is not None else None

        unread_result = await self._session.execute(
            select(func.count()).where(
                SkillReviewORM.expert_skill_id.in_(skill_ids),
                SkillReviewORM.status == "unread",
            )
        )
        unread_count = int(unread_result.scalar_one())

        replied_result = await self._session.execute(
            select(func.count()).where(
                SkillReviewORM.expert_skill_id.in_(skill_ids),
                SkillReviewORM.first_response_at.is_not(None),
            )
        )
        replied_count = int(replied_result.scalar_one())
        response_rate = round((replied_count / total) * 100, 1) if total else 0.0

        avg_hours = None
        if replied_count:
            rows = await self._session.execute(
                select(SkillReviewORM.created_at, SkillReviewORM.first_response_at).where(
                    SkillReviewORM.expert_skill_id.in_(skill_ids),
                    SkillReviewORM.first_response_at.is_not(None),
                )
            )
            hours = [
                _hours_between(created, responded)
                for created, responded in rows.all()
                if responded is not None
            ]
            if hours:
                avg_hours = round(sum(hours) / len(hours), 2)

        return ReviewInboxStats(
            average_rating=average_rating,
            total_reviews=total,
            unread_count=unread_count,
            response_rate_percent=response_rate,
            average_response_time_hours=avg_hours,
            average_response_time_label=_format_response_time(avg_hours),
        )

    async def get_notification_badge(self, creator_id: str) -> ReviewNotificationBadge:
        skill_ids = await self._skill_ids_for_creator(creator_id)
        settings = await self.get_notification_settings(creator_id)
        if not skill_ids:
            return ReviewNotificationBadge(unread_count=0, notify_mode=settings.notify_mode)

        unread_result = await self._session.execute(
            select(func.count()).where(
                SkillReviewORM.expert_skill_id.in_(skill_ids),
                SkillReviewORM.status == "unread",
            )
        )
        return ReviewNotificationBadge(
            unread_count=int(unread_result.scalar_one()),
            notify_mode=settings.notify_mode,
        )

    async def get_thread(self, creator_id: str, review_id: str, *, api_prefix: str) -> ReviewThread:
        review = await self._verify_review_access(creator_id, review_id)

        skill_result = await self._session.execute(
            select(ExpertSkillORM.name).where(ExpertSkillORM.id == review.expert_skill_id)
        )
        skill_name = skill_result.scalar_one()

        buyer_result = await self._session.execute(
            select(UserORM.full_name).where(UserORM.id == review.buyer_id)
        )
        buyer_name = buyer_result.scalar_one()

        messages_result = await self._session.execute(
            select(ReviewThreadMessageORM)
            .where(ReviewThreadMessageORM.review_id == review.id)
            .order_by(ReviewThreadMessageORM.created_at.asc())
        )
        thread_rows = list(messages_result.scalars().all())

        sender_ids = {row.sender_id for row in thread_rows}
        sender_ids.add(review.buyer_id)
        names_result = await self._session.execute(
            select(UserORM.id, UserORM.full_name).where(UserORM.id.in_(sender_ids))
        )
        name_map = {row.id: row.full_name for row in names_result.all()}

        message_ids = [row.id for row in thread_rows]
        attachments_by_message: dict[UUID, list[ReviewMessageAttachmentORM]] = {}
        if message_ids:
            att_result = await self._session.execute(
                select(ReviewMessageAttachmentORM).where(
                    ReviewMessageAttachmentORM.message_id.in_(message_ids)
                )
            )
            for att in att_result.scalars().all():
                attachments_by_message.setdefault(att.message_id, []).append(att)

        messages: list[ThreadMessage] = [
            ThreadMessage(
                id=str(review.id),
                sender_id=str(review.buyer_id),
                sender_name=buyer_name,
                sender_role="buyer",
                body=review.comment,
                attachments=[],
                created_at=review.created_at,
                is_initial_review=True,
            )
        ]

        for row in thread_rows:
            attachments = [
                ReviewAttachment(
                    id=str(att.id),
                    file_name=att.file_name,
                    content_type=att.content_type,
                    file_size=att.file_size,
                    download_url=f"{api_prefix}/creators/me/reviews/attachments/{att.id}/download",
                    created_at=att.created_at,
                )
                for att in attachments_by_message.get(row.id, [])
            ]
            messages.append(
                ThreadMessage(
                    id=str(row.id),
                    sender_id=str(row.sender_id),
                    sender_name=name_map.get(row.sender_id, "User"),
                    sender_role=row.sender_role,
                    body=row.body,
                    attachments=attachments,
                    created_at=row.created_at,
                )
            )

        now = datetime.now(timezone.utc)
        review.is_read = True
        review.creator_last_read_at = now
        review.updated_at = now
        await self._session.commit()

        return ReviewThread(
            review_id=str(review.id),
            expert_skill_id=str(review.expert_skill_id),
            skill_name=skill_name,
            buyer_id=str(review.buyer_id),
            buyer_name=buyer_name,
            rating=review.rating,
            status=review.status,
            messages=messages,
            first_response_at=review.first_response_at,
            resolved_at=review.resolved_at,
        )

    async def add_creator_reply(
        self,
        creator_id: str,
        review_id: str,
        *,
        body: str,
        message_id: str,
        attachment_meta: list[tuple[str, str, int, str]],
        api_prefix: str,
        notifications=None,
    ) -> ThreadMessage:
        review = await self._verify_review_access(creator_id, review_id)
        skill_result = await self._session.execute(
            select(ExpertSkillORM.name).where(ExpertSkillORM.id == review.expert_skill_id)
        )
        skill_name = skill_result.scalar_one()
        now = datetime.now(timezone.utc)
        message = ReviewThreadMessageORM(
            id=UUID(message_id),
            review_id=review.id,
            sender_id=UUID(creator_id),
            sender_role="creator",
            body=body.strip(),
            created_at=now,
        )
        self._session.add(message)

        attachments: list[ReviewAttachment] = []
        for file_name, content_type, file_size, storage_path in attachment_meta:
            att = ReviewMessageAttachmentORM(
                id=uuid4(),
                message_id=message.id,
                file_name=file_name,
                content_type=content_type,
                file_size=file_size,
                storage_path=storage_path,
                created_at=now,
            )
            self._session.add(att)
            attachments.append(
                ReviewAttachment(
                    id=str(att.id),
                    file_name=att.file_name,
                    content_type=att.content_type,
                    file_size=att.file_size,
                    download_url=f"{api_prefix}/creators/me/reviews/attachments/{att.id}/download",
                    created_at=att.created_at,
                )
            )

        if review.first_response_at is None:
            review.first_response_at = now
        if review.status == "unread":
            review.status = "replied"
        review.is_read = True
        review.creator_last_read_at = now
        review.updated_at = now

        creator_result = await self._session.execute(
            select(UserORM.full_name).where(UserORM.id == UUID(creator_id))
        )
        creator_name = creator_result.scalar_one()

        if notifications is not None:
            await notifications.create_event(
                str(review.buyer_id),
                event_type="thread_reply",
                title="Creator replied to your review",
                body=f"{creator_name} responded on {skill_name}",
                payload={
                    "review_id": review_id,
                    "expert_skill_id": str(review.expert_skill_id),
                    "skill_name": skill_name,
                    "creator_name": creator_name,
                    "workflow_id": review.workflow_id,
                },
            )

        await self._session.commit()

        return ThreadMessage(
            id=str(message.id),
            sender_id=creator_id,
            sender_name=creator_name,
            sender_role="creator",
            body=message.body,
            attachments=attachments,
            created_at=message.created_at,
        )

    async def resolve_review(
        self,
        creator_id: str,
        review_id: str,
        *,
        notifications=None,
    ) -> ReviewInboxItem:
        review = await self._verify_review_access(creator_id, review_id)
        skill_result = await self._session.execute(
            select(ExpertSkillORM.name).where(ExpertSkillORM.id == review.expert_skill_id)
        )
        skill_name = skill_result.scalar_one()
        creator_result = await self._session.execute(
            select(UserORM.full_name).where(UserORM.id == UUID(creator_id))
        )
        creator_name = creator_result.scalar_one()

        now = datetime.now(timezone.utc)
        review.status = "resolved"
        review.resolved_at = now
        review.updated_at = now

        if notifications is not None:
            await notifications.create_event(
                str(review.buyer_id),
                event_type="thread_resolved",
                title="Review thread resolved",
                body=f"{creator_name} marked your review on {skill_name} as resolved",
                payload={
                    "review_id": review_id,
                    "expert_skill_id": str(review.expert_skill_id),
                    "skill_name": skill_name,
                    "creator_name": creator_name,
                    "workflow_id": review.workflow_id,
                },
            )

        await self._session.commit()
        inbox = await self.get_inbox(creator_id)
        for item in inbox.items:
            if item.id == review_id:
                return item
        raise KeyError("Review not found after resolve")

    async def get_attachment_for_creator(self, creator_id: str, attachment_id: str) -> ReviewMessageAttachmentORM:
        skill_ids = await self._skill_ids_for_creator(creator_id)
        result = await self._session.execute(
            select(ReviewMessageAttachmentORM, SkillReviewORM)
            .join(ReviewThreadMessageORM, ReviewThreadMessageORM.id == ReviewMessageAttachmentORM.message_id)
            .join(SkillReviewORM, SkillReviewORM.id == ReviewThreadMessageORM.review_id)
            .where(
                ReviewMessageAttachmentORM.id == UUID(attachment_id),
                SkillReviewORM.expert_skill_id.in_(skill_ids),
            )
        )
        row = result.first()
        if row is None:
            raise KeyError("Attachment not found")
        return row[0]

    async def ensure_default_quick_replies(self, creator_id: str) -> list[QuickReply]:
        result = await self._session.execute(
            select(CreatorQuickReplyORM)
            .where(CreatorQuickReplyORM.creator_id == UUID(creator_id))
            .order_by(CreatorQuickReplyORM.sort_order.asc(), CreatorQuickReplyORM.created_at.asc())
        )
        rows = list(result.scalars().all())
        if not rows:
            now = datetime.now(timezone.utc)
            for index, (title, body) in enumerate(DEFAULT_QUICK_REPLIES):
                row = CreatorQuickReplyORM(
                    id=uuid4(),
                    creator_id=UUID(creator_id),
                    title=title,
                    body=body,
                    sort_order=index,
                    created_at=now,
                    updated_at=now,
                )
                self._session.add(row)
                rows.append(row)
            await self._session.commit()
            for row in rows:
                await self._session.refresh(row)

        return [
            QuickReply(
                id=str(row.id),
                title=row.title,
                body=row.body,
                sort_order=row.sort_order,
                created_at=row.created_at,
                updated_at=row.updated_at,
            )
            for row in rows
        ]

    async def list_quick_replies(self, creator_id: str) -> list[QuickReply]:
        return await self.ensure_default_quick_replies(creator_id)

    async def create_quick_reply(self, creator_id: str, payload: QuickReplyCreate) -> QuickReply:
        await self.ensure_default_quick_replies(creator_id)
        now = datetime.now(timezone.utc)
        count_result = await self._session.execute(
            select(func.count()).where(CreatorQuickReplyORM.creator_id == UUID(creator_id))
        )
        sort_order = int(count_result.scalar_one())
        row = CreatorQuickReplyORM(
            id=uuid4(),
            creator_id=UUID(creator_id),
            title=payload.title,
            body=payload.body,
            sort_order=sort_order,
            created_at=now,
            updated_at=now,
        )
        self._session.add(row)
        await self._session.commit()
        await self._session.refresh(row)
        return QuickReply(
            id=str(row.id),
            title=row.title,
            body=row.body,
            sort_order=row.sort_order,
            created_at=row.created_at,
            updated_at=row.updated_at,
        )

    async def update_quick_reply(
        self,
        creator_id: str,
        reply_id: str,
        payload: QuickReplyUpdate,
    ) -> QuickReply:
        result = await self._session.execute(
            select(CreatorQuickReplyORM).where(
                CreatorQuickReplyORM.id == UUID(reply_id),
                CreatorQuickReplyORM.creator_id == UUID(creator_id),
            )
        )
        row = result.scalar_one_or_none()
        if row is None:
            raise KeyError("Quick reply not found")
        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(row, field, value)
        row.updated_at = datetime.now(timezone.utc)
        await self._session.commit()
        await self._session.refresh(row)
        return QuickReply(
            id=str(row.id),
            title=row.title,
            body=row.body,
            sort_order=row.sort_order,
            created_at=row.created_at,
            updated_at=row.updated_at,
        )

    async def delete_quick_reply(self, creator_id: str, reply_id: str) -> None:
        result = await self._session.execute(
            select(CreatorQuickReplyORM).where(
                CreatorQuickReplyORM.id == UUID(reply_id),
                CreatorQuickReplyORM.creator_id == UUID(creator_id),
            )
        )
        row = result.scalar_one_or_none()
        if row is None:
            raise KeyError("Quick reply not found")
        await self._session.delete(row)
        await self._session.commit()

    async def get_notification_settings(self, creator_id: str) -> ReviewNotificationSettings:
        result = await self._session.execute(
            select(CreatorReviewNotificationSettingsORM).where(
                CreatorReviewNotificationSettingsORM.creator_id == UUID(creator_id)
            )
        )
        row = result.scalar_one_or_none()
        if row is None:
            return ReviewNotificationSettings(notify_mode="all")
        return ReviewNotificationSettings(notify_mode=row.notify_mode)

    async def update_notification_settings(
        self,
        creator_id: str,
        settings: ReviewNotificationSettings,
    ) -> ReviewNotificationSettings:
        if settings.notify_mode not in {"all", "unread_only"}:
            raise ValueError("notify_mode must be 'all' or 'unread_only'")
        result = await self._session.execute(
            select(CreatorReviewNotificationSettingsORM).where(
                CreatorReviewNotificationSettingsORM.creator_id == UUID(creator_id)
            )
        )
        row = result.scalar_one_or_none()
        now = datetime.now(timezone.utc)
        if row is None:
            row = CreatorReviewNotificationSettingsORM(
                creator_id=UUID(creator_id),
                notify_mode=settings.notify_mode,
                updated_at=now,
            )
            self._session.add(row)
        else:
            row.notify_mode = settings.notify_mode
            row.updated_at = now
        await self._session.commit()
        return settings