from datetime import datetime, timezone
from uuid import UUID, uuid4

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.expert_skill import ExpertSkillORM
from app.db.models.review_inbox import ReviewThreadMessageORM
from app.db.models.skill_review import SkillReviewORM
from app.db.models.user import UserORM
from app.models.buyer_review import BuyerReviewItem, BuyerReviewSubmitted
from app.models.review_inbox import ReviewAttachment, ReviewThread, ThreadMessage
from app.repositories.notification_repository import NotificationRepository


class BuyerReviewRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_review_for_buyer(self, buyer_id: str, expert_skill_id: str) -> SkillReviewORM | None:
        result = await self._session.execute(
            select(SkillReviewORM).where(
                SkillReviewORM.buyer_id == UUID(buyer_id),
                SkillReviewORM.expert_skill_id == UUID(expert_skill_id),
            )
        )
        return result.scalar_one_or_none()

    async def get_review_by_id(self, buyer_id: str, review_id: str) -> SkillReviewORM:
        result = await self._session.execute(
            select(SkillReviewORM).where(
                SkillReviewORM.id == UUID(review_id),
                SkillReviewORM.buyer_id == UUID(buyer_id),
            )
        )
        review = result.scalar_one_or_none()
        if review is None:
            raise KeyError("Review not found")
        return review

    async def _to_buyer_item(self, review: SkillReviewORM) -> BuyerReviewItem:
        skill_result = await self._session.execute(
            select(ExpertSkillORM.name, ExpertSkillORM.slug).where(
                ExpertSkillORM.id == review.expert_skill_id
            )
        )
        skill_row = skill_result.one()

        creator_msgs = await self._session.execute(
            select(func.count()).where(
                ReviewThreadMessageORM.review_id == review.id,
                ReviewThreadMessageORM.sender_role == "creator",
            )
        )
        creator_reply_count = int(creator_msgs.scalar_one())

        unread = 0
        if review.buyer_last_read_at:
            unread_result = await self._session.execute(
                select(func.count()).where(
                    ReviewThreadMessageORM.review_id == review.id,
                    ReviewThreadMessageORM.sender_role == "creator",
                    ReviewThreadMessageORM.created_at > review.buyer_last_read_at,
                )
            )
            unread = int(unread_result.scalar_one())
        elif creator_reply_count > 0:
            unread = creator_reply_count

        return BuyerReviewItem(
            id=str(review.id),
            expert_skill_id=str(review.expert_skill_id),
            skill_name=skill_row.name,
            skill_slug=skill_row.slug,
            rating=review.rating,
            comment=review.comment,
            status=review.status,
            workflow_id=review.workflow_id,
            created_at=review.created_at,
            updated_at=review.updated_at,
            has_creator_reply=creator_reply_count > 0,
            unread_replies=unread,
        )

    async def list_reviews(self, buyer_id: str) -> list[BuyerReviewItem]:
        result = await self._session.execute(
            select(SkillReviewORM)
            .where(SkillReviewORM.buyer_id == UUID(buyer_id))
            .order_by(SkillReviewORM.created_at.desc())
        )
        reviews = list(result.scalars().all())
        return [await self._to_buyer_item(review) for review in reviews]

    async def submit_review(
        self,
        buyer_id: str,
        *,
        expert_skill_id: str,
        workflow_id: str,
        rating: int,
        comment: str,
        notifications: NotificationRepository,
    ) -> BuyerReviewSubmitted:
        existing = await self.get_review_for_buyer(buyer_id, expert_skill_id)
        if existing is not None:
            item = await self._to_buyer_item(existing)
            return BuyerReviewSubmitted(
                review=item,
                message="You already reviewed this skill",
            )

        skill_result = await self._session.execute(
            select(ExpertSkillORM).where(ExpertSkillORM.id == UUID(expert_skill_id))
        )
        skill = skill_result.scalar_one_or_none()
        if skill is None:
            raise KeyError("Expert skill not found")

        buyer_result = await self._session.execute(
            select(UserORM.full_name).where(UserORM.id == UUID(buyer_id))
        )
        buyer_name = buyer_result.scalar_one()

        now = datetime.now(timezone.utc)
        review = SkillReviewORM(
            id=uuid4(),
            expert_skill_id=UUID(expert_skill_id),
            buyer_id=UUID(buyer_id),
            rating=rating,
            comment=comment.strip(),
            workflow_id=workflow_id,
            status="unread",
            is_read=False,
            created_at=now,
            updated_at=now,
        )
        self._session.add(review)

        await notifications.create_event(
            str(skill.owner_id),
            event_type="new_review",
            title="New review received",
            body=f"{buyer_name} left a {rating}★ review on {skill.name}",
            payload={
                "review_id": str(review.id),
                "expert_skill_id": expert_skill_id,
                "skill_name": skill.name,
                "rating": rating,
                "buyer_name": buyer_name,
                "workflow_id": workflow_id,
            },
        )

        await self._session.commit()
        item = await self._to_buyer_item(review)
        return BuyerReviewSubmitted(review=item)

    async def get_thread(self, buyer_id: str, review_id: str, *, api_prefix: str) -> ReviewThread:
        from app.db.models.review_inbox import ReviewMessageAttachmentORM

        review = await self.get_review_by_id(buyer_id, review_id)

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
        attachments_by_message: dict[UUID, list] = {}
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
                    download_url=f"{api_prefix}/reviews/me/attachments/{att.id}/download",
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
        review.buyer_last_read_at = now
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

    async def add_buyer_reply(
        self,
        buyer_id: str,
        review_id: str,
        *,
        body: str,
        message_id: str,
        attachment_meta: list[tuple[str, str, int, str]],
        api_prefix: str,
        notifications: NotificationRepository,
    ) -> ThreadMessage:
        from app.db.models.review_inbox import ReviewMessageAttachmentORM

        review = await self.get_review_by_id(buyer_id, review_id)
        skill_result = await self._session.execute(
            select(ExpertSkillORM).where(ExpertSkillORM.id == review.expert_skill_id)
        )
        skill = skill_result.scalar_one()

        buyer_result = await self._session.execute(
            select(UserORM.full_name).where(UserORM.id == UUID(buyer_id))
        )
        buyer_name = buyer_result.scalar_one()

        now = datetime.now(timezone.utc)
        message = ReviewThreadMessageORM(
            id=UUID(message_id),
            review_id=review.id,
            sender_id=UUID(buyer_id),
            sender_role="buyer",
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
                    download_url=f"{api_prefix}/reviews/me/attachments/{att.id}/download",
                    created_at=att.created_at,
                )
            )

        if review.status == "resolved":
            review.status = "replied"
            review.resolved_at = None
        review.is_read = False
        review.updated_at = now

        await notifications.create_event(
            str(skill.owner_id),
            event_type="thread_reply",
            title="Buyer replied in review thread",
            body=f"{buyer_name} sent a follow-up on {skill.name}",
            payload={
                "review_id": review_id,
                "expert_skill_id": str(skill.id),
                "skill_name": skill.name,
                "buyer_name": buyer_name,
                "workflow_id": review.workflow_id,
            },
        )

        await self._session.commit()

        return ThreadMessage(
            id=str(message.id),
            sender_id=buyer_id,
            sender_name=buyer_name,
            sender_role="buyer",
            body=message.body,
            attachments=attachments,
            created_at=message.created_at,
        )

    async def get_attachment_for_buyer(self, buyer_id: str, attachment_id: str):
        from app.db.models.review_inbox import ReviewMessageAttachmentORM

        result = await self._session.execute(
            select(ReviewMessageAttachmentORM, SkillReviewORM)
            .join(ReviewThreadMessageORM, ReviewThreadMessageORM.id == ReviewMessageAttachmentORM.message_id)
            .join(SkillReviewORM, SkillReviewORM.id == ReviewThreadMessageORM.review_id)
            .where(
                ReviewMessageAttachmentORM.id == UUID(attachment_id),
                SkillReviewORM.buyer_id == UUID(buyer_id),
            )
        )
        row = result.first()
        if row is None:
            raise KeyError("Attachment not found")
        return row[0]