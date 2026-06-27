from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.billing_transaction import BillingTransactionORM
from app.db.models.creator_earning import CreatorEarningORM
from app.db.models.expert_skill import ExpertSkillORM
from app.db.models.skill_review import SkillReviewORM
from app.db.models.user import UserORM
from app.models.creator import (
    AnalyticsDataPoint,
    CreatorActivityItem,
    CreatorAnalytics,
    CreatorPayoutHistoryItem,
    CreatorPayouts,
    CreatorReviewsSummary,
    CreatorSkillItem,
    CreatorSkillStats,
    CreatorSummary,
    CreatorTopSkill,
    SkillReview,
)


MINIMUM_PAYOUT_USD = Decimal("10")


class CreatorRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def _skill_ids_for_creator(self, creator_id: str) -> list[UUID]:
        result = await self._session.execute(
            select(ExpertSkillORM.id).where(ExpertSkillORM.owner_id == UUID(creator_id))
        )
        return list(result.scalars().all())

    async def _runs_for_skill(self, creator_id: str, skill_id: str) -> int:
        result = await self._session.execute(
            select(func.count())
            .select_from(CreatorEarningORM)
            .where(
                CreatorEarningORM.creator_id == UUID(creator_id),
                CreatorEarningORM.agent_id == UUID(skill_id),
                CreatorEarningORM.product_type == "expert_skill",
            )
        )
        return int(result.scalar_one())

    async def _earnings_for_skill(self, creator_id: str, skill_id: str) -> Decimal:
        result = await self._session.execute(
            select(func.coalesce(func.sum(CreatorEarningORM.net_amount_usd), 0))
            .where(
                CreatorEarningORM.creator_id == UUID(creator_id),
                CreatorEarningORM.agent_id == UUID(skill_id),
                CreatorEarningORM.product_type == "expert_skill",
            )
        )
        return Decimal(str(result.scalar_one()))

    async def _rating_for_skill(self, skill_id: str) -> tuple[float | None, int]:
        result = await self._session.execute(
            select(
                func.avg(SkillReviewORM.rating),
                func.count(),
            ).where(SkillReviewORM.expert_skill_id == UUID(skill_id))
        )
        avg_rating, count = result.one()
        if not count:
            return None, 0
        return round(float(avg_rating), 2), int(count)

    async def list_skills(self, creator_id: str) -> list[CreatorSkillItem]:
        result = await self._session.execute(
            select(ExpertSkillORM)
            .where(ExpertSkillORM.owner_id == UUID(creator_id))
            .order_by(ExpertSkillORM.created_at.desc())
        )
        items: list[CreatorSkillItem] = []
        for row in result.scalars().all():
            skill_id = str(row.id)
            runs = await self._runs_for_skill(creator_id, skill_id)
            earnings = await self._earnings_for_skill(creator_id, skill_id)
            avg_rating, review_count = await self._rating_for_skill(skill_id)
            items.append(
                CreatorSkillItem(
                    id=skill_id,
                    slug=row.slug,
                    name=row.name,
                    description=row.description,
                    category=row.category,
                    pack_slug=row.pack_slug,
                    crew_config=dict(row.crew_config or {}),
                    capabilities=list(row.capabilities or []),
                    price_usd_per_run=row.price_usd_per_run,
                    owner_id=str(row.owner_id),
                    is_active=row.is_active,
                    created_at=row.created_at,
                    updated_at=row.updated_at,
                    stats=CreatorSkillStats(
                        total_runs=runs,
                        total_earnings_usd=earnings,
                        average_rating=avg_rating,
                        review_count=review_count,
                    ),
                )
            )
        return items

    async def total_runs(self, creator_id: str) -> int:
        skill_ids = await self._skill_ids_for_creator(creator_id)
        if not skill_ids:
            return 0
        result = await self._session.execute(
            select(func.count())
            .select_from(CreatorEarningORM)
            .where(
                CreatorEarningORM.creator_id == UUID(creator_id),
                CreatorEarningORM.product_type == "expert_skill",
                CreatorEarningORM.agent_id.in_(skill_ids),
            )
        )
        return int(result.scalar_one())

    async def total_earnings(self, creator_id: str) -> Decimal:
        result = await self._session.execute(
            select(func.coalesce(func.sum(CreatorEarningORM.net_amount_usd), 0)).where(
                CreatorEarningORM.creator_id == UUID(creator_id)
            )
        )
        return Decimal(str(result.scalar_one()))

    async def average_rating(self, creator_id: str) -> tuple[float | None, int]:
        skill_ids = await self._skill_ids_for_creator(creator_id)
        if not skill_ids:
            return None, 0
        result = await self._session.execute(
            select(func.avg(SkillReviewORM.rating), func.count())
            .where(SkillReviewORM.expert_skill_id.in_(skill_ids))
        )
        avg_rating, count = result.one()
        if not count:
            return None, 0
        return round(float(avg_rating), 2), int(count)

    async def top_skill_this_month(self, creator_id: str) -> CreatorTopSkill | None:
        now = datetime.now(timezone.utc)
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        skill_ids = await self._skill_ids_for_creator(creator_id)
        if not skill_ids:
            return None

        result = await self._session.execute(
            select(
                CreatorEarningORM.agent_id,
                func.count().label("runs"),
                func.coalesce(func.sum(CreatorEarningORM.net_amount_usd), 0).label("earnings"),
            )
            .where(
                CreatorEarningORM.creator_id == UUID(creator_id),
                CreatorEarningORM.product_type == "expert_skill",
                CreatorEarningORM.agent_id.in_(skill_ids),
                CreatorEarningORM.created_at >= month_start,
            )
            .group_by(CreatorEarningORM.agent_id)
            .order_by(func.sum(CreatorEarningORM.net_amount_usd).desc())
            .limit(1)
        )
        row = result.first()
        if row is None:
            return None

        skill_result = await self._session.execute(
            select(ExpertSkillORM.name).where(ExpertSkillORM.id == row.agent_id)
        )
        skill_name = skill_result.scalar_one_or_none() or "Unknown skill"
        return CreatorTopSkill(
            skill_id=str(row.agent_id),
            skill_name=skill_name,
            runs=int(row.runs),
            earnings_usd=Decimal(str(row.earnings)),
        )

    async def recent_activity(self, creator_id: str, *, limit: int = 10) -> list[CreatorActivityItem]:
        activities: list[CreatorActivityItem] = []

        earnings_result = await self._session.execute(
            select(CreatorEarningORM, ExpertSkillORM.name)
            .join(ExpertSkillORM, ExpertSkillORM.id == CreatorEarningORM.agent_id, isouter=True)
            .where(
                CreatorEarningORM.creator_id == UUID(creator_id),
                CreatorEarningORM.product_type == "expert_skill",
            )
            .order_by(CreatorEarningORM.created_at.desc())
            .limit(limit)
        )
        for earning, skill_name in earnings_result.all():
            activities.append(
                CreatorActivityItem(
                    id=str(earning.id),
                    activity_type="run",
                    title=f"New run — {skill_name or 'Expert Skill'}",
                    detail=f"Workflow {earning.workflow_id}",
                    amount_usd=Decimal(str(earning.net_amount_usd)),
                    created_at=earning.created_at,
                )
            )

        skill_ids = await self._skill_ids_for_creator(creator_id)
        if skill_ids:
            reviews_result = await self._session.execute(
                select(SkillReviewORM, ExpertSkillORM.name)
                .join(ExpertSkillORM, ExpertSkillORM.id == SkillReviewORM.expert_skill_id)
                .where(SkillReviewORM.expert_skill_id.in_(skill_ids))
                .order_by(SkillReviewORM.created_at.desc())
                .limit(limit)
            )
            for review, skill_name in reviews_result.all():
                activities.append(
                    CreatorActivityItem(
                        id=str(review.id),
                        activity_type="review",
                        title=f"New review — {skill_name}",
                        detail=review.comment[:120],
                        amount_usd=None,
                        created_at=review.created_at,
                    )
                )

        activities.sort(key=lambda item: item.created_at, reverse=True)
        return activities[:limit]

    async def get_summary(
        self,
        creator_id: str,
        *,
        earnings_balance_usd: Decimal,
        platform_fee_percent: float,
    ) -> CreatorSummary:
        skills = await self.list_skills(creator_id)
        avg_rating, review_count = await self.average_rating(creator_id)
        return CreatorSummary(
            total_earnings_usd=await self.total_earnings(creator_id),
            earnings_balance_usd=earnings_balance_usd,
            total_runs=await self.total_runs(creator_id),
            active_skills=sum(1 for skill in skills if skill.is_active),
            total_skills=len(skills),
            average_rating=avg_rating,
            review_count=review_count,
            top_skill_this_month=await self.top_skill_this_month(creator_id),
            recent_activity=await self.recent_activity(creator_id),
            minimum_payout_usd=MINIMUM_PAYOUT_USD,
            platform_fee_percent=platform_fee_percent,
        )

    async def get_analytics(self, creator_id: str, period: str = "week") -> CreatorAnalytics:
        now = datetime.now(timezone.utc).date()
        if period == "day":
            start = now - timedelta(days=6)
            bucket_days = 1
        elif period == "month":
            start = now - timedelta(days=29)
            bucket_days = 1
        else:
            period = "week"
            start = now - timedelta(days=27)
            bucket_days = 7

        skill_ids = await self._skill_ids_for_creator(creator_id)
        data_points: list[AnalyticsDataPoint] = []
        if skill_ids:
            result = await self._session.execute(
                select(
                    func.date(CreatorEarningORM.created_at).label("day"),
                    func.coalesce(func.sum(CreatorEarningORM.net_amount_usd), 0).label("earnings"),
                    func.count().label("runs"),
                )
                .where(
                    CreatorEarningORM.creator_id == UUID(creator_id),
                    CreatorEarningORM.product_type == "expert_skill",
                    CreatorEarningORM.agent_id.in_(skill_ids),
                    func.date(CreatorEarningORM.created_at) >= start,
                )
                .group_by(func.date(CreatorEarningORM.created_at))
                .order_by(func.date(CreatorEarningORM.created_at))
            )
            daily = {
                row.day: (Decimal(str(row.earnings)), int(row.runs))
                for row in result.all()
            }
        else:
            daily = {}

        if period == "week":
            cursor = start
            while cursor <= now:
                week_end = min(cursor + timedelta(days=bucket_days - 1), now)
                earnings = Decimal("0")
                runs = 0
                day = cursor
                while day <= week_end:
                    day_stats = daily.get(day)
                    if day_stats:
                        earnings += day_stats[0]
                        runs += day_stats[1]
                    day += timedelta(days=1)
                data_points.append(
                    AnalyticsDataPoint(period_start=cursor, earnings_usd=earnings, runs=runs)
                )
                cursor += timedelta(days=bucket_days)
        else:
            cursor = start
            while cursor <= now:
                day_stats = daily.get(cursor, (Decimal("0"), 0))
                data_points.append(
                    AnalyticsDataPoint(
                        period_start=cursor,
                        earnings_usd=day_stats[0],
                        runs=day_stats[1],
                    )
                )
                cursor += timedelta(days=1)

        top_skills: list[CreatorTopSkill] = []
        if skill_ids:
            top_result = await self._session.execute(
                select(
                    CreatorEarningORM.agent_id,
                    func.count().label("runs"),
                    func.coalesce(func.sum(CreatorEarningORM.net_amount_usd), 0).label("earnings"),
                )
                .where(
                    CreatorEarningORM.creator_id == UUID(creator_id),
                    CreatorEarningORM.product_type == "expert_skill",
                    CreatorEarningORM.agent_id.in_(skill_ids),
                    func.date(CreatorEarningORM.created_at) >= start,
                )
                .group_by(CreatorEarningORM.agent_id)
                .order_by(func.sum(CreatorEarningORM.net_amount_usd).desc())
                .limit(5)
            )
            for row in top_result.all():
                skill_result = await self._session.execute(
                    select(ExpertSkillORM.name).where(ExpertSkillORM.id == row.agent_id)
                )
                skill_name = skill_result.scalar_one_or_none() or "Unknown skill"
                top_skills.append(
                    CreatorTopSkill(
                        skill_id=str(row.agent_id),
                        skill_name=skill_name,
                        runs=int(row.runs),
                        earnings_usd=Decimal(str(row.earnings)),
                    )
                )

        total_runs = sum(point.runs for point in data_points)
        day_count = max((now - start).days + 1, 1)
        avg_runs_per_day = round(total_runs / day_count, 2)

        return CreatorAnalytics(
            period=period,
            data_points=data_points,
            top_skills=top_skills,
            average_runs_per_day=avg_runs_per_day,
            conversion_rate=None,
            conversion_tracked=False,
        )

    async def get_reviews(self, creator_id: str) -> CreatorReviewsSummary:
        skill_ids = await self._skill_ids_for_creator(creator_id)
        if not skill_ids:
            return CreatorReviewsSummary(average_rating=None, review_count=0, reviews=[])

        avg_rating, review_count = await self.average_rating(creator_id)
        result = await self._session.execute(
            select(SkillReviewORM, ExpertSkillORM.name, UserORM.full_name)
            .join(ExpertSkillORM, ExpertSkillORM.id == SkillReviewORM.expert_skill_id)
            .join(UserORM, UserORM.id == SkillReviewORM.buyer_id)
            .where(SkillReviewORM.expert_skill_id.in_(skill_ids))
            .order_by(SkillReviewORM.created_at.desc())
        )
        reviews = [
            SkillReview(
                id=str(review.id),
                expert_skill_id=str(review.expert_skill_id),
                skill_name=skill_name,
                buyer_id=str(review.buyer_id),
                buyer_name=buyer_name,
                rating=review.rating,
                comment=review.comment,
                workflow_id=review.workflow_id,
                created_at=review.created_at,
            )
            for review, skill_name, buyer_name in result.all()
        ]
        return CreatorReviewsSummary(
            average_rating=avg_rating,
            review_count=review_count,
            reviews=reviews,
        )

    async def get_payouts(
        self,
        creator_id: str,
        *,
        earnings_balance_usd: Decimal,
        total_earned_usd: Decimal,
    ) -> CreatorPayouts:
        result = await self._session.execute(
            select(BillingTransactionORM)
            .where(
                BillingTransactionORM.user_id == UUID(creator_id),
                BillingTransactionORM.transaction_type == "earnings_transfer",
            )
            .order_by(BillingTransactionORM.created_at.desc())
            .limit(50)
        )
        history = [
            CreatorPayoutHistoryItem(
                id=str(row.id),
                amount_usd=Decimal(str(row.amount_usd)),
                transaction_type=row.transaction_type,
                description=row.description,
                created_at=row.created_at,
            )
            for row in result.scalars().all()
        ]
        return CreatorPayouts(
            earnings_balance_usd=earnings_balance_usd,
            total_earned_usd=total_earned_usd,
            minimum_payout_usd=MINIMUM_PAYOUT_USD,
            can_request_payout=earnings_balance_usd >= MINIMUM_PAYOUT_USD,
            payout_history=history,
        )