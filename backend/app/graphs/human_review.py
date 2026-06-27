from datetime import datetime, timezone
from typing import Literal

from langchain_core.messages import HumanMessage
from langgraph.types import interrupt

from app.models.state import AgentNexusState

APPROVE_KEYWORDS = {"approve", "approved", "ok", "yes", "lgtm", "accept", "accepted"}


def is_human_loop_enabled(state: AgentNexusState) -> bool:
    task_context = state.get("task_context") or {}
    return bool(task_context.get("require_human_approval", False))


def _is_approved(feedback: str) -> bool:
    return feedback.strip().lower() in APPROVE_KEYWORDS


def build_interrupt_payload(state: AgentNexusState) -> dict:
    return {
        "workflow_id": state["workflow_id"],
        "prompt": (
            "Review the draft output. Reply with 'approve' to accept "
            "or provide revision feedback."
        ),
        "draft_output": state.get("final_output"),
        "agent_outputs": (state.get("intermediate_results") or {}).get("agent_outputs"),
        "current_agent": state.get("current_agent"),
    }


def human_review_node(state: AgentNexusState) -> dict:
    if not is_human_loop_enabled(state):
        return {}

    feedback = interrupt(build_interrupt_payload(state))
    feedback_text = str(feedback)
    approved = _is_approved(feedback_text)
    now = datetime.now(timezone.utc)
    intermediate = dict(state.get("intermediate_results") or {})
    intermediate["human_feedback"] = feedback_text
    intermediate["human_approved"] = approved

    if approved:
        return {
            "status": "completed",
            "updated_at": now,
            "intermediate_results": intermediate,
        }

    return {
        "status": "running",
        "final_output": None,
        "messages": [HumanMessage(content=f"Human revision requested: {feedback_text}")],
        "updated_at": now,
        "intermediate_results": {
            **intermediate,
            "human_revision_requested": True,
        },
    }


def route_after_human_review(
    state: AgentNexusState,
    *,
    revise_target: str,
) -> Literal["__end__"] | str:
    if not is_human_loop_enabled(state):
        return "__end__"
    if (state.get("intermediate_results") or {}).get("human_approved"):
        return "__end__"
    return revise_target