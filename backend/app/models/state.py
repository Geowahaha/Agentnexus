from datetime import datetime, timezone
from typing import Annotated, Literal, TypedDict
from uuid import uuid4

from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages


WorkflowType = Literal["single_agent", "multi_agent", "marketplace_run", "expert_skill"]
WorkflowStatus = Literal["pending", "running", "waiting_human", "completed", "failed"]


class AgentNexusState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]
    workflow_id: str
    workflow_type: WorkflowType
    current_agent: str | None
    next_agent: str | None
    user_id: str
    agent_id: str | None
    agent_role: str | None
    task_description: str
    task_context: dict | None
    final_output: str | None
    intermediate_results: dict
    total_cost_usd: float
    total_tokens: int
    execution_time_seconds: float | None
    status: WorkflowStatus
    error_message: str | None
    created_at: datetime
    updated_at: datetime


def create_initial_state(
    *,
    user_id: str,
    task_description: str,
    workflow_type: WorkflowType = "single_agent",
    task_context: dict | None = None,
    agent_id: str | None = None,
    agent_role: str | None = None,
) -> AgentNexusState:
    now = datetime.now(timezone.utc)
    return AgentNexusState(
        messages=[],
        workflow_id=str(uuid4()),
        workflow_type=workflow_type,
        current_agent=None,
        next_agent=None,
        user_id=user_id,
        agent_id=agent_id,
        agent_role=agent_role,
        task_description=task_description,
        task_context=task_context,
        final_output=None,
        intermediate_results={},
        total_cost_usd=0.0,
        total_tokens=0,
        execution_time_seconds=None,
        status="pending",
        error_message=None,
        created_at=now,
        updated_at=now,
    )