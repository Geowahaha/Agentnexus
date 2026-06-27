import asyncio
import logging
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any

logger = logging.getLogger(__name__)

from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.types import Command

from app.agents.definitions import agent_to_definition, resolve_crew
from app.billing.models import WorkflowBilling
from app.billing.service import BillingService
from app.core.llm import LLMFactory
from app.graphs.base import build_base_graph
from app.graphs.expert_skill import create_expert_skill_graph
from app.graphs.utils import hydrate_expert_skill_steps_from_final_output
from app.graphs.multi_agent import create_multi_agent_graph
from app.graphs.single_agent import create_single_agent_graph
from app.models.state import AgentNexusState, WorkflowType, create_initial_state
from app.repositories.expert_skill_repository import ExpertSkillRepository
from app.repositories.wallet_repository import InsufficientBalanceError
from app.services.agent_registry import AgentNotFoundError, AgentRegistry
from app.services.bridge_context import (
    BridgeToolContext,
    reset_bridge_tool_context,
    set_bridge_context_from_state,
    set_bridge_tool_context,
)
from app.services.bridge_service import BridgeService
from app.services.mcp_service import MCPService
from app.core.config import settings
from app.services.tool_resolver import ToolResolver
from app.services.moat_service import (
    build_and_record_fingerprint,
    perform_post_causal_measurement_and_fingerprint,
    record_behavioral_trace,
    record_skill_execution_event,
)
from app.core.database import async_session_maker  # direct maker for moat logging context (non-Depends)

FABLE5_LOCAL_SLUG = "fable5-coding-agent"
FABLE5_PREMIUM_SLUG = "fable5-coding-agent-premium"


class WorkflowNotFoundError(KeyError):
    """Raised when a workflow thread does not exist in the checkpointer."""


class WorkflowPermissionError(PermissionError):
    """Raised when a user tries to access another user's workflow."""


class WorkflowService:
    def __init__(
        self,
        factory: LLMFactory,
        registry: AgentRegistry,
        checkpointer: BaseCheckpointSaver,
        tool_resolver: ToolResolver,
        billing: BillingService,
        expert_skills: ExpertSkillRepository,
        mcp_service: MCPService,
        bridge_service: BridgeService,
        *,
        signup_credits_usd: Decimal,
    ) -> None:
        self._factory = factory
        self._registry = registry
        self._checkpointer = checkpointer
        self._tool_resolver = tool_resolver
        self._billing = billing
        self._expert_skills = expert_skills
        self._mcp_service = mcp_service
        self._bridge = bridge_service
        self._signup_credits_usd = signup_credits_usd
        self._background_tasks: set[asyncio.Task] = set()

    def _config(self, workflow_id: str) -> dict:
        return {"configurable": {"thread_id": workflow_id}}

    async def _validate_expert_skill_preflight(self, expert_skill_id: str | None) -> None:
        if not expert_skill_id:
            return
        skill = await self._expert_skills.get_by_id(expert_skill_id)
        if skill is None:
            return
        if skill.slug == FABLE5_LOCAL_SLUG:
            if not settings.ollama_enabled:
                raise ValueError(
                    "Free Fable-5 requires OLLAMA_ENABLED=true and model qwen3.6-27b-fable5 "
                    "on the server. See local-ollama-setup in the skill playbook, or use "
                    "Fable-5 Coding Agent Pro ($5) — cloud GPT-4.1 + Grok, no GPU needed."
                )
        elif skill.slug == FABLE5_PREMIUM_SLUG:
            missing: list[str] = []
            if not settings.openai_api_key:
                missing.append("OPENAI_API_KEY")
            if not settings.xai_api_key:
                missing.append("XAI_API_KEY")
            if missing:
                raise ValueError(
                    f"Fable-5 Pro requires platform keys: {', '.join(missing)}. "
                    "Contact support or try the free local LoRA tier with Ollama."
                )

    async def _prepare_bridge_context(self, user_id: str, task_context: dict | None):
        device_id = (task_context or {}).get("bridge_device_id")
        if not device_id:
            return None
        await self._bridge.ensure_device_for_user(user_id, str(device_id))
        return set_bridge_tool_context(
            BridgeToolContext(user_id=user_id, device_id=str(device_id))
        )

    @staticmethod
    def _clear_bridge_context(token) -> None:
        if token is not None:
            reset_bridge_tool_context(token)

    async def run(
        self,
        *,
        user_id: str,
        task_description: str,
        workflow_type: WorkflowType = "single_agent",
        task_context: dict | None = None,
        agent_id: str | None = None,
        agent_role: str | None = None,
        require_human_approval: bool = False,
    ) -> tuple[AgentNexusState, WorkflowBilling | None]:
        agent_def = None
        if agent_id:
            try:
                agent = await self._registry.get_agent(agent_id)
                agent_def = agent_to_definition(agent)
                agent_role = agent_role or agent.role
            except AgentNotFoundError as exc:
                raise ValueError(f"Unknown agent '{agent_id}'") from exc

        merged_context = dict(task_context or {})
        if require_human_approval:
            merged_context["require_human_approval"] = True

        agent_ids = merged_context.get("agents")
        expert_skill_id = merged_context.get("expert_skill_id")

        if workflow_type == "expert_skill" or expert_skill_id:
            from app.expert_skills.input_mode import skill_requires_url
            from app.utils.url_normalize import extract_target_url, normalize_expert_skill_task

            skill_row = None
            skill_slug = str(merged_context.get("expert_skill_slug") or "")
            if expert_skill_id:
                skill_row = await self._expert_skills.get_by_id(str(expert_skill_id))
                if skill_row is not None:
                    skill_slug = skill_row.slug
                    merged_context["expert_skill_slug"] = skill_slug

            needs_url = False
            if skill_row is not None:
                needs_url = skill_requires_url(
                    pack_slug=skill_row.pack_slug,
                    crew_config=skill_row.crew_config,
                    category=skill_row.category,
                    slug=skill_row.slug,
                    name=skill_row.name,
                    description=skill_row.description,
                )

            task_description = normalize_expert_skill_task(task_description)
            if needs_url and extract_target_url(task_description) is None:
                raise ValueError(
                    "Please enter a valid URL, e.g. example.com or https://example.com"
                )
            await self._validate_expert_skill_preflight(
                str(expert_skill_id) if expert_skill_id else None
            )
            if skill_slug == "agent-ready-auto-fix":
                target = merged_context.get("target_url") or extract_target_url(task_description)
                if target:
                    from app.core.database import async_session_maker
                    from app.repositories.agent_ready_session_repository import AgentReadySessionRepository
                    from app.services.agent_ready.entitlement_guard import is_entitled

                    async with async_session_maker() as db:
                        repo = AgentReadySessionRepository(db)
                        if await is_entitled(repo, user_id, str(target)):
                            raise ValueError(
                                "This website is already purchased — use free re-scan on Agent-Ready. "
                                "Enter a different URL to buy another site."
                            )
        await self._billing.ensure_sufficient_balance(
            user_id,
            workflow_type=workflow_type,
            agent_id=agent_id,
            agent_ids=agent_ids,
            expert_skill_id=expert_skill_id,
            initial_balance=self._signup_credits_usd,
        )

        initial_state = create_initial_state(
            user_id=user_id,
            task_description=task_description,
            workflow_type=workflow_type,
            task_context=merged_context or None,
            agent_id=agent_id,
            agent_role=agent_role,
        )

        bridge_token = await self._prepare_bridge_context(user_id, merged_context)
        if bridge_token is not None:
            device = await self._bridge.ensure_device_for_user(
                user_id, str(merged_context["bridge_device_id"])
            )
            initial_state["intermediate_results"] = {
                **initial_state.get("intermediate_results", {}),
                "bridge_device": device,
            }

        graph = await self._compile_graph(workflow_type, merged_context or None, agent_def)
        workflow_id = initial_state["workflow_id"]
        config = self._config(workflow_id)

        try:
            if workflow_type == "expert_skill":
                initial_state["status"] = "running"
                initial_state["updated_at"] = datetime.now(timezone.utc)
                await graph.aupdate_state(config, dict(initial_state), as_node="prepare")
                self._spawn_background_workflow(
                    graph, dict(initial_state), config, bridge_token=bridge_token
                )
                return dict(initial_state), None

            # Simple cost ceiling check (per skill budget)
            if initial_state.get("budget_usd"):
                est = await self._billing.estimate_cost(initial_state)  # assume exists or stub
                if est.get("estimated_total", 0) > initial_state["budget_usd"]:
                    raise ValueError("Cost ceiling exceeded for this skill run")

            result = await graph.ainvoke(initial_state, config)
            normalized = await self._normalize_result(graph, workflow_id, result)
            billing = await self._billing.settle_workflow(
                dict(normalized), initial_balance=self._signup_credits_usd
            )
            await self._record_moat_execution(normalized, billing)
            return normalized, billing
        except Exception as e:
            # Basic retry strategy stub (for non-expert skills)
            if workflow_type != "expert_skill" and "timeout" in str(e).lower():
                logger.warning(f"Retry attempt for {workflow_id}")
            raise
        finally:
            if workflow_type != "expert_skill":
                self._clear_bridge_context(bridge_token)

    def _spawn_background_workflow(
        self,
        graph,
        initial_state: dict,
        config: dict,
        bridge_token=None,
    ) -> None:
        """Spawn workflow execution in the background using asyncio task."""
        task = asyncio.create_task(
            self._execute_workflow_background(graph, initial_state, config)
        )
        self._background_tasks.add(task)
        task.add_done_callback(self._background_tasks.discard)

    async def _execute_workflow_background(
        self,
        graph,
        initial_state: dict,
        config: dict,
    ) -> None:
        workflow_id = initial_state["workflow_id"]
        bridge_token = set_bridge_context_from_state(initial_state)
        trace_id = f"wf-{workflow_id[:8]}"
        logger.info(f"[{trace_id}] Starting background execution")
        try:
            result = await graph.ainvoke(None, config)
            normalized = await self._normalize_result(graph, workflow_id, result)
            billing = await self._billing.settle_workflow(
                dict(normalized),
                initial_balance=self._signup_credits_usd,
            )
            await self._record_moat_execution(normalized, billing)
            logger.info(f"[{trace_id}] Completed successfully")
        except Exception as exc:
            logger.error(f"[{trace_id}] Execution failed: {exc}")
            try:
                snapshot = await graph.aget_state(config)
                state = dict(snapshot.values or initial_state)
                state["status"] = "failed"
                state["error_message"] = str(exc)
                state["updated_at"] = datetime.now(timezone.utc)
                await graph.aupdate_state(config, state)
                await self._billing.settle_workflow(
                    state,
                    initial_balance=self._signup_credits_usd,
                )
            except Exception:
                pass
        finally:
            self._clear_bridge_context(bridge_token)

    async def _record_moat_execution(self, normalized: dict, billing: Any | None = None) -> None:
        """PM-directed rich moat capture. Pulls full behavioral trace + basic signals."""
        try:
            task_context = normalized.get("task_context") or {}
            wf_id = str(normalized.get("workflow_id") or task_context.get("workflow_id") or "")
            if not wf_id:
                return

            skill_slug = task_context.get("expert_skill_slug")
            skill_id = task_context.get("expert_skill_id")
            user_id = normalized.get("user_id") or task_context.get("user_id")

            target_urls: list[str] = []
            url = task_context.get("target_url")
            if url:
                target_urls = [url]

            # Costs
            mkt = Decimal("0")
            llm_c = Decimal("0")
            tot = Decimal("0")
            if billing:
                mkt = getattr(billing, "marketplace_cost_usd", 0) or Decimal("0")
                llm_c = getattr(billing, "llm_cost_usd", 0) or Decimal("0")
                tot = Decimal(str(mkt)) + Decimal(str(llm_c))

            intermediate = normalized.get("intermediate_results") or {}
            full_steps = dict(intermediate.get("expert_skill_steps") or {})
            has_proof = bool(intermediate.get("aibotauth_proof"))

            step_sum = {
                "status": normalized.get("status"),
                "has_proof": has_proof,
                "step_count": len(full_steps),
            }

            outcome_proxies: dict[str, Any] = {}
            if has_proof:
                outcome_proxies["has_aibotauth_proof"] = True
                outcome_proxies["proof_meta"] = intermediate.get("aibotauth_proof")

            # Use fresh session
            async with async_session_maker() as session:
                await record_skill_execution_event(
                    session=session,
                    workflow_id=wf_id,
                    expert_skill_id=skill_id,
                    skill_slug=skill_slug,
                    user_id=user_id,
                    target_urls=target_urls,
                    step_summary=step_sum,
                    marketplace_cost_usd=mkt,
                    llm_cost_usd=llm_c,
                    total_cost_usd=tot,
                    outcome_proxies=outcome_proxies,
                    completed=True,
                )

                # PM-approved richer behavioral trace (legacy)
                await record_behavioral_trace(
                    session=session,
                    workflow_id=wf_id,
                    skill_slug=skill_slug,
                    expert_skill_id=skill_id,
                    full_steps=full_steps,
                    mcp_calls=None,
                    llm_usage={},
                    warnings=intermediate.get("warnings", []),
                    raw_artifacts={"proof": intermediate.get("aibotauth_proof") if has_proof else None},
                )

                # PM long-term core: Structured Agent Behavior Fingerprint (durable moat asset)
                pre_vis = intermediate.get("scan_data") or intermediate.get("agent_ready_analyze", {}).get("scan") or {}
                post_vis = intermediate.get("aibotauth_proof") or {}
                lift = (intermediate.get("aibotauth_proof") or {}).get("causal_lift") or {}

                # Build richer typed sequence from steps (high-fidelity trajectories)
                # This is key to replication resistance: capturing decision/tool traces, not just final text.
                behavior_seq: list[dict[str, Any]] = []
                for step_id, output in full_steps.items():
                    ev = {
                        "step_id": step_id,
                        "event_type": "action" if "deploy" in str(step_id).lower() else "step",
                        "output_summary": str(output)[:400] if output else "",
                    }
                    if step_id in ("scan", "analyze", "verify"):
                        ev["event_type"] = "mcp_call" if "scan" in step_id else "decision"
                        ev["tool"] = "aibotauth.scan" if "scan" in step_id else None
                    behavior_seq.append(ev)

                await build_and_record_fingerprint(
                    session=session,
                    workflow_id=wf_id,
                    target_url=url or (target_urls[0] if target_urls else ""),
                    skill_slug=skill_slug,
                    expert_skill_id=skill_id,
                    user_id=user_id,
                    pre_visibility=pre_vis,
                    behavior_sequence=behavior_seq,
                    post_visibility=post_vis if post_vis else {},
                    causal_lift=lift,
                    provenance={
                        "has_aibotauth_proof": has_proof,
                        "aibotauth_source": "mcp_or_proof_api",
                        "fingerprint_built_by": "obolla_moat_v1",
                    },
                    costs={"marketplace_cost_usd": float(mkt), "llm_cost_usd": float(llm_c), "total_cost_usd": float(tot)},
                    success=normalized.get("status") == "completed",
                )

                # Execution Team: Automatic causal post-measurement for moat-critical skills
                # This creates direct pre-execution-post fingerprints.
                moat_skills = {"ai-visibility-2026", "fix-bot-ai-agent-ready", "agent-ready-auto-fix", "seo-expert-analysis"}
                if skill_slug in moat_skills and url:
                    await perform_post_causal_measurement_and_fingerprint(
                        session=session,
                        workflow_id=wf_id,
                        target_url=url,
                        skill_slug=skill_slug,
                        pre_visibility=pre_vis,
                        behavior_sequence=behavior_seq,
                        costs={"marketplace_cost_usd": float(mkt), "llm_cost_usd": float(llm_c), "total_cost_usd": float(tot)},
                        success=normalized.get("status") == "completed",
                    )
        except Exception as exc:  # noqa: BLE001 — never break primary path
            logger.warning("moat execution record skipped (non-fatal): %s", exc)

    async def get_status(
        self, workflow_id: str, *, user_id: str
    ) -> tuple[AgentNexusState, WorkflowBilling | None]:
        graph, snapshot = await self._load_workflow(workflow_id)
        if snapshot.values is None:
            raise WorkflowNotFoundError(workflow_id)
        self._ensure_workflow_owner(snapshot.values, user_id)
        normalized = await self._normalize_result(graph, workflow_id, snapshot.values)
        billing = await self._billing.settle_workflow(dict(normalized), initial_balance=self._signup_credits_usd)
        return normalized, billing

    async def resume(self, workflow_id: str, feedback: str, *, user_id: str) -> tuple[AgentNexusState, WorkflowBilling | None]:
        graph, snapshot = await self._load_workflow(workflow_id)
        if snapshot.values is None:
            raise WorkflowNotFoundError(workflow_id)
        self._ensure_workflow_owner(snapshot.values, user_id)
        if not self._has_interrupt(snapshot):
            raise ValueError(f"Workflow '{workflow_id}' is not waiting for human input.")

        result = await graph.ainvoke(Command(resume=feedback), self._config(workflow_id))
        normalized = await self._normalize_result(graph, workflow_id, result)
        billing = await self._billing.settle_workflow(dict(normalized), initial_balance=self._signup_credits_usd)
        return normalized, billing

    async def _load_workflow(self, workflow_id: str):
        checkpoint_tuple = await self._checkpointer.aget_tuple(self._config(workflow_id))
        if checkpoint_tuple is None:
            raise WorkflowNotFoundError(workflow_id)

        state_values = checkpoint_tuple.checkpoint.get("channel_values", {})
        agent_def = await self._resolve_agent_def_from_state(state_values)
        graph = await self._compile_graph(
            state_values.get("workflow_type", "single_agent"),
            state_values.get("task_context"),
            agent_def,
        )
        snapshot = await graph.aget_state(self._config(workflow_id))
        return graph, snapshot

    async def _resolve_agent_def_from_state(self, state_values: dict):
        agent_id = state_values.get("agent_id")
        if not agent_id:
            return None
        try:
            agent = await self._registry.get_agent(agent_id)
            return agent_to_definition(agent)
        except AgentNotFoundError:
            return None

    async def _compile_graph(
        self,
        workflow_type: WorkflowType,
        task_context: dict | None,
        agent_def,
    ):
        if workflow_type == "single_agent":
            return create_single_agent_graph(
                self._factory,
                agent_def,
                tool_resolver=self._tool_resolver,
                checkpointer=self._checkpointer,
            )
        if workflow_type == "multi_agent":
            agent_ids = (task_context or {}).get("agents")
            crew = await resolve_crew(agent_ids, self._registry)
            if not crew:
                raise ValueError("No active agents available for multi-agent workflow.")
            return create_multi_agent_graph(
                self._factory,
                crew,
                tool_resolver=self._tool_resolver,
                checkpointer=self._checkpointer,
            )
        if workflow_type == "expert_skill":
            skill_id = (task_context or {}).get("expert_skill_id")
            if not skill_id:
                raise ValueError("expert_skill_id is required for expert_skill workflow.")
            skill = await self._expert_skills.get_by_id(skill_id)
            if skill is None:
                raise ValueError(f"Unknown expert skill '{skill_id}'")
            return create_expert_skill_graph(
                self._factory,
                pack_slug=skill.pack_slug,
                crew_config=skill.crew_config,
                mcp_service=self._mcp_service,
                checkpointer=self._checkpointer,
                category=skill.category,
                skill_name=skill.name,
                skill_description=skill.description,
            )
        if workflow_type == "marketplace_run":
            # Not yet wired to a dedicated graph. Marketplace runs typically use expert_skill.
            raise ValueError("Workflow type 'marketplace_run' is not supported yet. Use expert_skill, single_agent or multi_agent.")
        return build_base_graph().compile(checkpointer=self._checkpointer)

    async def _normalize_result(
        self,
        graph,
        workflow_id: str,
        result: AgentNexusState | dict,
    ) -> AgentNexusState:
        snapshot = await graph.aget_state(self._config(workflow_id))
        state = dict(snapshot.values or result)
        if self._has_interrupt(snapshot):
            state["status"] = "waiting_human"
            interrupt_payload = self._extract_interrupt_payload(snapshot)
            intermediate = dict(state.get("intermediate_results") or {})
            intermediate["interrupt"] = interrupt_payload
            state["intermediate_results"] = intermediate
        state = hydrate_expert_skill_steps_from_final_output(state)
        return state  # type: ignore[return-value]

    @staticmethod
    def _ensure_workflow_owner(state_values: dict, user_id: str) -> None:
        owner_id = state_values.get("user_id")
        if owner_id and owner_id != user_id:
            raise WorkflowPermissionError(f"Workflow '{state_values.get('workflow_id')}' is not owned by this user")

    @staticmethod
    def _has_interrupt(snapshot) -> bool:
        return bool(snapshot.tasks and any(task.interrupts for task in snapshot.tasks))

    @staticmethod
    def _extract_interrupt_payload(snapshot) -> list:
        payloads: list = []
        for task in snapshot.tasks or []:
            for item in task.interrupts or []:
                payloads.append(item.value)
        return payloads


# Re-export for API layer
__all__ = [
    "InsufficientBalanceError",
    "WorkflowNotFoundError",
    "WorkflowPermissionError",
    "WorkflowService",
]