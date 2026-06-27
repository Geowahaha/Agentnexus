from fastapi import APIRouter, Depends, HTTPException, status

from pydantic import BaseModel, Field

from app.auth.dependencies import get_current_user
from app.auth.models import User
from app.billing.models import WorkflowBilling
from app.core.deps import get_workflow_service
from app.models.state import WorkflowType
from app.repositories.wallet_repository import InsufficientBalanceError
from app.services.workflow_service import WorkflowNotFoundError, WorkflowService, WorkflowPermissionError

router = APIRouter()


class WorkflowRunRequest(BaseModel):
    task_description: str = Field(..., min_length=1)
    workflow_type: WorkflowType = "single_agent"
    task_context: dict | None = None
    agent_id: str | None = None
    agent_role: str | None = None
    agents: list[str] | None = Field(
        default=None,
        description="Agent UUIDs for multi_agent workflow",
    )
    expert_skill_id: str | None = Field(
        default=None,
        description="Expert skill UUID for expert_skill workflow",
    )
    require_human_approval: bool = Field(
        default=False,
        description="Pause workflow for human review before completion",
    )
    bridge_device_id: str | None = Field(
        default=None,
        description="Paired local machine UUID — enables bridge.* tools for this run",
    )


class WorkflowResumeRequest(BaseModel):
    feedback: str = Field(
        ...,
        min_length=1,
        description="Use 'approve' to accept the draft or provide revision feedback",
    )


class WorkflowRunResponse(BaseModel):
    workflow_id: str
    status: str
    final_output: str | None = None
    total_tokens: int = 0
    total_cost_usd: float = 0.0
    execution_time_seconds: float | None = None
    error_message: str | None = None
    agent_id: str | None = None
    agents_used: list[str] | None = None
    intermediate_results: dict | None = None
    human_prompt: str | None = None
    workflow_type: str | None = None
    expert_skill_id: str | None = None
    billing: WorkflowBilling | None = None


def _to_response(result: dict, billing: WorkflowBilling | None = None) -> WorkflowRunResponse:
    intermediate = result.get("intermediate_results") or {}
    interrupt_payload = intermediate.get("interrupt") or []
    human_prompt = None
    if interrupt_payload:
        first = interrupt_payload[0]
        human_prompt = first.get("prompt") if isinstance(first, dict) else str(first)

    task_context = result.get("task_context") or {}
    return WorkflowRunResponse(
        workflow_id=result["workflow_id"],
        status=result["status"],
        final_output=result.get("final_output"),
        total_tokens=result.get("total_tokens", 0),
        total_cost_usd=result.get("total_cost_usd", 0.0),
        execution_time_seconds=result.get("execution_time_seconds"),
        error_message=result.get("error_message"),
        agent_id=result.get("agent_id"),
        agents_used=intermediate.get("crew"),
        intermediate_results=intermediate,
        human_prompt=human_prompt,
        workflow_type=result.get("workflow_type"),
        expert_skill_id=task_context.get("expert_skill_id"),
        billing=billing,
    )


@router.post("/run", response_model=WorkflowRunResponse)
async def run_workflow(
    request: WorkflowRunRequest,
    current_user: User = Depends(get_current_user),
    service: WorkflowService = Depends(get_workflow_service),
) -> WorkflowRunResponse:
    task_context = dict(request.task_context or {})
    if request.agents:
        task_context["agents"] = request.agents
    if request.expert_skill_id:
        task_context["expert_skill_id"] = request.expert_skill_id
    if request.bridge_device_id:
        task_context["bridge_device_id"] = request.bridge_device_id

    try:
        result, billing = await service.run(
            user_id=current_user.id,
            task_description=request.task_description,
            workflow_type=request.workflow_type,
            task_context=task_context or None,
            agent_id=request.agent_id,
            agent_role=request.agent_role,
            require_human_approval=request.require_human_approval,
        )
    except InsufficientBalanceError as exc:
        raise HTTPException(status_code=status.HTTP_402_PAYMENT_REQUIRED, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Workflow failed: {exc}",
        ) from exc

    return _to_response(result, billing)


@router.get("/{workflow_id}", response_model=WorkflowRunResponse)
async def get_workflow_status(
    workflow_id: str,
    current_user: User = Depends(get_current_user),
    service: WorkflowService = Depends(get_workflow_service),
) -> WorkflowRunResponse:
    try:
        result, billing = await service.get_status(workflow_id, user_id=current_user.id)
    except WorkflowNotFoundError as exc:
        raise HTTPException(status_code=404, detail=f"Workflow '{workflow_id}' not found") from exc
    except WorkflowPermissionError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except InsufficientBalanceError as exc:
        raise HTTPException(status_code=status.HTTP_402_PAYMENT_REQUIRED, detail=str(exc)) from exc
    return _to_response(result, billing)


@router.post("/{workflow_id}/resume", response_model=WorkflowRunResponse)
async def resume_workflow(
    workflow_id: str,
    request: WorkflowResumeRequest,
    current_user: User = Depends(get_current_user),
    service: WorkflowService = Depends(get_workflow_service),
) -> WorkflowRunResponse:
    try:
        result, billing = await service.resume(workflow_id, request.feedback, user_id=current_user.id)
    except WorkflowNotFoundError as exc:
        raise HTTPException(status_code=404, detail=f"Workflow '{workflow_id}' not found") from exc
    except WorkflowPermissionError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except InsufficientBalanceError as exc:
        raise HTTPException(status_code=status.HTTP_402_PAYMENT_REQUIRED, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return _to_response(result, billing)