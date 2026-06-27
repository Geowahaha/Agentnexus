import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Numeric, String, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class VisibilityEventORM(Base):
    __tablename__ = "visibility_events"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    url: Mapped[str] = mapped_column(String(500), nullable=False, index=True)
    scanned_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    source: Mapped[str] = mapped_column(String(60), nullable=False, default="aibotauth_mcp")
    overall: Mapped[int | None] = mapped_column(Numeric(5, 1), nullable=True)  # allow float-ish scores via numeric
    grade: Mapped[str | None] = mapped_column(String(10), nullable=True)
    level: Mapped[str | None] = mapped_column(String(20), nullable=True)
    percent: Mapped[int | None] = mapped_column(Numeric(5, 1), nullable=True)  # e.g. isitagentready %
    details: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    proof_share_id: Mapped[str | None] = mapped_column(String(120), nullable=True)
    proof_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    workflow_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    linked_skill_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("expert_skills.id", ondelete="SET NULL"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
