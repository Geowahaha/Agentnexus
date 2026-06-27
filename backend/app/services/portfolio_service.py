from app.auth.models import User
from app.models.portfolio import AgentProfile, PortfolioItem, PortfolioItemCreate, PortfolioItemUpdate
from app.repositories.portfolio_repository import PortfolioRepository
from app.services.agent_registry import AgentNotFoundError, AgentRegistry
from app.services.workflow_service import WorkflowNotFoundError, WorkflowPermissionError, WorkflowService

TASK_PREVIEW_MAX = 500
OUTPUT_PREVIEW_MAX = 3000


def _truncate(text: str, max_len: int) -> str:
    cleaned = text.strip()
    if len(cleaned) <= max_len:
        return cleaned
    return cleaned[: max_len - 3] + "..."


class PortfolioService:
    def __init__(
        self,
        repository: PortfolioRepository,
        registry: AgentRegistry,
        workflow_service: WorkflowService,
    ) -> None:
        self._repository = repository
        self._registry = registry
        self._workflow_service = workflow_service

    async def get_profile(
        self,
        agent_id: str,
        *,
        include_private: bool = False,
    ) -> AgentProfile:
        await self._registry.get_agent(agent_id)
        portfolio = await self._repository.list_for_agent(agent_id, public_only=not include_private)
        stats = await self._repository.get_stats(agent_id)
        return AgentProfile(agent_id=agent_id, stats=stats, portfolio=portfolio)

    async def create_from_workflow(
        self,
        agent_id: str,
        data: PortfolioItemCreate,
        *,
        current_user: User,
    ) -> PortfolioItem:
        agent = await self._registry.get_agent(agent_id)
        if agent.owner_id != current_user.id:
            raise PermissionError("Only the agent owner can add portfolio items.")

        existing = await self._repository.get_by_agent_and_workflow(agent_id, data.workflow_id)
        if existing:
            raise ValueError("This workflow is already in the agent portfolio.")

        try:
            workflow_state, _ = await self._workflow_service.get_status(
                data.workflow_id,
                user_id=current_user.id,
            )
        except WorkflowNotFoundError as exc:
            raise ValueError(f"Workflow '{data.workflow_id}' not found.") from exc
        except WorkflowPermissionError as exc:
            raise PermissionError("You can only pin workflows you ran.") from exc

        if workflow_state.get("status") != "completed":
            raise ValueError("Only completed workflows can be added to a portfolio.")

        workflow_type = workflow_state.get("workflow_type", "single_agent")
        self._ensure_agent_in_workflow(agent_id, workflow_state)

        task_preview = _truncate(workflow_state.get("task_description") or "", TASK_PREVIEW_MAX)
        output_preview = self._resolve_output_preview(agent_id, workflow_state)

        if not output_preview:
            raise ValueError("Workflow has no output to showcase.")

        title = data.title
        if not title:
            task = workflow_state.get("task_description") or ""
            title = _truncate(task, 120) if task else "Work sample"

        return await self._repository.create(
            agent_id,
            PortfolioItemCreate(
                workflow_id=data.workflow_id,
                title=title,
                summary=data.summary,
                is_public=data.is_public,
            ),
            task_preview=task_preview,
            output_preview=output_preview,
            workflow_type=workflow_type,
        )

    async def update_item(
        self,
        agent_id: str,
        item_id: str,
        data: PortfolioItemUpdate,
        *,
        current_user: User,
    ) -> PortfolioItem:
        await self._ensure_owner(agent_id, current_user)
        item = await self._repository.get_by_id(item_id)
        if item is None or item.agent_id != agent_id:
            raise ValueError("Portfolio item not found.")
        updated = await self._repository.update(item_id, data)
        if updated is None:
            raise ValueError("Portfolio item not found.")
        return updated

    async def delete_item(self, agent_id: str, item_id: str, *, current_user: User) -> None:
        await self._ensure_owner(agent_id, current_user)
        item = await self._repository.get_by_id(item_id)
        if item is None or item.agent_id != agent_id:
            raise ValueError("Portfolio item not found.")
        deleted = await self._repository.delete(item_id)
        if not deleted:
            raise ValueError("Portfolio item not found.")

    async def _ensure_owner(self, agent_id: str, current_user: User) -> None:
        try:
            agent = await self._registry.get_agent(agent_id)
        except AgentNotFoundError as exc:
            raise ValueError(f"Agent '{agent_id}' not found.") from exc
        if agent.owner_id != current_user.id:
            raise PermissionError("Only the agent owner can manage portfolio items.")

    @staticmethod
    def _ensure_agent_in_workflow(agent_id: str, workflow_state: dict) -> None:
        workflow_type = workflow_state.get("workflow_type", "single_agent")
        if workflow_type == "single_agent":
            if workflow_state.get("agent_id") != agent_id:
                raise ValueError("This workflow did not use the selected agent.")
            return

        intermediate = workflow_state.get("intermediate_results") or {}
        crew = intermediate.get("crew") or []
        if agent_id not in crew:
            raise ValueError("This workflow did not include the selected agent in its crew.")

    @staticmethod
    def _resolve_output_preview(agent_id: str, workflow_state: dict) -> str:
        intermediate = workflow_state.get("intermediate_results") or {}
        agent_outputs = intermediate.get("agent_outputs") or {}
        if agent_id in agent_outputs and agent_outputs[agent_id]:
            return _truncate(str(agent_outputs[agent_id]), OUTPUT_PREVIEW_MAX)

        final_output = workflow_state.get("final_output")
        if final_output:
            return _truncate(str(final_output), OUTPUT_PREVIEW_MAX)
        return ""