"""
Agent Behavior Trace — Core proprietary data asset for the long-term Data Moat.

This model captures high-fidelity, structured, causally-linked agent behavior
correlated with verifiable site states (from signed AIBotAuth scans).

Design principles (PM long-term requirements):
- Structured over generic blobs: typed events with schema_version for evolution.
- Cryptographic provenance: links to signed scan artifacts where available.
- Causal: explicit pre/post + lift for defensibility.
- Compounding: designed for aggregation into SkillEfficacy, DomainBenchmarks, etc.
- Expensive to replicate: requires operating trusted signed crawler + high-volume curated skills + execution on measured URLs.

This is not "analytics". This is the ground truth dataset that powers unique intelligence no competitor can easily duplicate.
"""
import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Numeric, String, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class AgentBehaviorTraceORM(Base):
    __tablename__ = "agent_behavior_traces"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Linkage
    workflow_id: Mapped[str] = mapped_column(String(36), nullable=False, unique=True, index=True)
    expert_skill_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("expert_skills.id", ondelete="SET NULL"), nullable=True
    )
    skill_slug: Mapped[str | None] = mapped_column(String(120), nullable=True, index=True)
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    # Target
    target_url: Mapped[str] = mapped_column(String(500), nullable=False, index=True)
    url_fingerprint: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)  # e.g. hash of canonical + key signals

    # Structured high-fidelity trace (versioned proprietary schema)
    fingerprint_version: Mapped[str] = mapped_column(String(16), nullable=False, default="1.0")
    pre_visibility: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)      # structured pre-state from AIBotAuth/IsIt
    behavior_sequence: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)   # typed events: mcp_call, llm_step, etc.
    post_visibility: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    causal_lift: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)         # deltas + attribution

    # Provenance & ownership (cryptographic defensibility)
    provenance: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)          # aibotauth signatures, our hashes, verification status

    # Costs & metadata for compounding analysis
    marketplace_cost_usd: Mapped[Decimal] = mapped_column(Numeric(12, 4), nullable=False, default=Decimal("0"))
    llm_cost_usd: Mapped[Decimal] = mapped_column(Numeric(12, 4), nullable=False, default=Decimal("0"))
    total_cost_usd: Mapped[Decimal] = mapped_column(Numeric(12, 4), nullable=False, default=Decimal("0"))
    step_count: Mapped[int] = mapped_column(default=0)
    success: Mapped[bool] = mapped_column(default=True)

    # Revenue Attribution Data (key moat pillar) - linked from billing/earnings via workflow_id
    revenue_attribution: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)  # e.g. {"gross_usd": x, "platform_fee": y, "earnings": [...], "attributed_revenue": true}

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    # Schema evolution plan (long-term): 
    # v1.0: basic + revenue_att
    # v1.1: add revenue_causal_fidelity, signed_revenue_obj
    # v2.0: separate revenue_attributions table for normalization + MCP support
    # Always version in fingerprint_version and revenue_att["_signature"]["version"]
