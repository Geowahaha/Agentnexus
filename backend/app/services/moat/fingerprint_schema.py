"""
Proprietary Fingerprint Schema for Agent Behavior Traces.

This defines the canonical, versioned structure for our Data Moat assets.

PM Long-term Requirements:
- Typed events for high-fidelity decision processes, tool interactions, causal chains.
- Explicit provenance (cryptographic).
- Versioning for evolution without breaking compounding value.
- This schema + the data collected through our closed AIBotAuth+OBOLLA loop is expensive to replicate at quality and scale.
  Competitors would need equivalent signed real-web visibility + high-signal skill executions + causal measurement.

Do not treat as generic JSON. This is our IP structure.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


class BaseTraceEvent(BaseModel):
    """Base for all typed trace events."""
    event_type: str
    timestamp: datetime | None = None
    duration_ms: float | None = None
    success: bool = True
    metadata: dict[str, Any] = Field(default_factory=dict)


class MCPCallEvent(BaseTraceEvent):
    """MCP tool call (e.g., AIBotAuth scan, other skills)."""
    event_type: Literal["mcp_call"] = "mcp_call"
    tool: str
    input_summary: dict[str, Any] | str  # Avoid storing full sensitive inputs; hash or summary
    output_summary: dict[str, Any] | str
    mcp_server: str | None = None


class LLMReasoningEvent(BaseTraceEvent):
    """LLM step in agent reasoning."""
    event_type: Literal["llm_reasoning"] = "llm_reasoning"
    model: str
    prompt_hash: str | None = None  # SHA of prompt for provenance without full leak
    output_summary: str
    tokens: dict[str, int] | None = None


class DecisionEvent(BaseTraceEvent):
    """Explicit decision or branching point."""
    event_type: Literal["decision"] = "decision"
    decision: str
    rationale_summary: str
    alternatives_considered: list[str] = Field(default_factory=list)


class AgentActionEvent(BaseTraceEvent):
    """General action (deploy, content gen, etc.)."""
    event_type: Literal["action"] = "action"
    action_type: str
    target: str | None = None
    result_summary: str


class ErrorRecoveryEvent(BaseTraceEvent):
    """Error and recovery attempt (critical for fidelity)."""
    event_type: Literal["error_recovery"] = "error_recovery"
    error_type: str
    recovery_action: str
    outcome: str


TraceEvent = MCPCallEvent | LLMReasoningEvent | DecisionEvent | AgentActionEvent | ErrorRecoveryEvent


class PreVisibilityState(BaseModel):
    """Structured pre-execution site state from signed scanner."""
    overall: float | None = None
    grade: str | None = None
    percent: float | None = None
    level: str | None = None
    key_signals: dict[str, Any] = Field(default_factory=dict)  # e.g. llms.txt present, schema, etc.
    scan_signature: str | None = None  # Link to AIBotAuth signature if available


class PostVisibilityState(PreVisibilityState):
    """Post-execution state (often from follow-up scan)."""
    pass


class CausalLift(BaseModel):
    """Explicit causal outcome."""
    delta_overall: float | None = None
    delta_percent: float | None = None
    attribution: dict[str, Any] = Field(default_factory=dict)  # which steps contributed
    confidence: str | None = None


class Provenance(BaseModel):
    """Cryptographic and ownership provenance."""
    aibotauth_signatures: list[str] = Field(default_factory=list)
    our_signature: str | None = None  # JWT or Ed25519 signature of the fingerprint
    fingerprint_hash: str | None = None
    source: str = "aibotauth_obolla_closed_loop"
    verified: bool = False


class AgentBehaviorFingerprint(BaseModel):
    """
    Canonical high-fidelity fingerprint.

    This is the structured, signed representation that makes our moat durable.
    Versioned so we can evolve the schema while preserving historical value for compounding.
    """
    fingerprint_version: str = "1.1"  # Bumped for typed events + signing
    workflow_id: str
    target_url: str
    url_fingerprint: str | None = None
    skill_slug: str | None = None
    pre_visibility: PreVisibilityState
    behavior_sequence: list[TraceEvent]  # Typed, not raw dicts
    post_visibility: PostVisibilityState | None = None
    causal_lift: CausalLift | None = None
    provenance: Provenance
    costs: dict[str, float] = Field(default_factory=dict)
    step_count: int = 0
    success: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_schema_extra = {
            "description": "Proprietary Agent Behavior Fingerprint. Expensive to replicate due to required signed real-web visibility + executed skills + causal linkage."
        }


def compute_fingerprint_hash(fp: AgentBehaviorFingerprint) -> str:
    """Simple hash for provenance (extend with full signing)."""
    import hashlib
    import json
    data = fp.model_dump_json(exclude={"provenance": {"our_signature"}})
    return hashlib.sha256(data.encode()).hexdigest()
