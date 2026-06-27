from uuid import UUID, uuid4

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.notification_event import NotificationEventORM
from app.models.notification import NotificationBadge, NotificationEvent, NotificationListResponse
from app.services.edge_notify_service import publish_edge_notification


class NotificationRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create_event(
        self,
        user_id: str,
        *,
        event_type: str,
        title: str,
        body: str,
        payload: dict | None = None,
    ) -> NotificationEvent:
        row = NotificationEventORM(
            id=uuid4(),
            user_id=UUID(user_id),
            event_type=event_type,
            title=title,
            body=body,
            payload=payload or {},
            is_read=False,
        )
        self._session.add(row)
        await self._session.flush()
        event = self._to_model(row)
        await publish_edge_notification(
            user_id,
            event_type=event_type,
            title=title,
            body=body,
            payload=payload,
            notification_id=event.id,
        )
        return event

    async def list_events(self, user_id: str, *, limit: int = 30) -> NotificationListResponse:
        result = await self._session.execute(
            select(NotificationEventORM)
            .where(NotificationEventORM.user_id == UUID(user_id))
            .order_by(NotificationEventORM.created_at.desc())
            .limit(limit)
        )
        rows = list(result.scalars().all())
        unread = await self.get_badge(user_id)
        return NotificationListResponse(
            items=[self._to_model(row) for row in rows],
            unread_count=unread.unread_count,
        )

    async def get_badge(self, user_id: str) -> NotificationBadge:
        result = await self._session.execute(
            select(func.count()).where(
                NotificationEventORM.user_id == UUID(user_id),
                NotificationEventORM.is_read.is_(False),
            )
        )
        return NotificationBadge(unread_count=int(result.scalar_one()))

    async def mark_read(self, user_id: str, event_ids: list[str]) -> NotificationBadge:
        if event_ids:
            await self._session.execute(
                update(NotificationEventORM)
                .where(
                    NotificationEventORM.user_id == UUID(user_id),
                    NotificationEventORM.id.in_([UUID(eid) for eid in event_ids]),
                )
                .values(is_read=True)
            )
        else:
            await self._session.execute(
                update(NotificationEventORM)
                .where(
                    NotificationEventORM.user_id == UUID(user_id),
                    NotificationEventORM.is_read.is_(False),
                )
                .values(is_read=True)
            )
        await self._session.commit()
        return await self.get_badge(user_id)

    @staticmethod
    def _to_model(row: NotificationEventORM) -> NotificationEvent:
        return NotificationEvent(
            id=str(row.id),
            event_type=row.event_type,
            title=row.title,
            body=row.body,
            payload=dict(row.payload or {}),
            is_read=row.is_read,
            created_at=row.created_at,
        )