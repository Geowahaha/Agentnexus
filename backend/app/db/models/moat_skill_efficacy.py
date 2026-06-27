import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Numeric, String, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class MoatSkillEfficacyORM(Base):
    """Persisted derived profile for the Data Moat.

    This stores the proprietary SkillEfficacyProfile with revenue attribution.
    Allows compounding without recompute and enables revenue intelligence products.
    """
    __tablename__ = "moat_skill_efficacy"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    skill_slug: Mapped[str] = mapped_column(String(120), nullable=False, unique=True, index=True)
    total_runs: Mapped[int] = mapped_column(default=0)
    successful_lifts: Mapped[int] = mapped_column(default=0)
    avg_delta_percent: Mapped[Decimal] = mapped_column(Numeric(8, 2), default=Decimal("0"))
    confidence_score: Mapped[Decimal] = mapped_column(Numeric(5, 3), default=Decimal("0"))
    url_categories: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    total_attributed_revenue_usd: Mapped[Decimal] = mapped_column(Numeric(12, 4), default=Decimal("0"))
    avg_revenue_per_lift: Mapped[Decimal] = mapped_column(Numeric(12, 4), default=Decimal("0"))
    profile_data: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)  # full profile snapshot
    last_updated: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
