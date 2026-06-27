from datetime import datetime, timezone
from typing import Literal

from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph
from pydantic import BaseModel, Field

from app.agents.definitions import (
    FINISH_AGENT,
    MAX_SUPERVISOR_STEPS,
    AgentDefinition,
    crew_agent_ids,
)
from app.core.config import settings
from app.core.llm import LLMFactory
from app.graphs.agent_runner import (
    build_tool_aware_updates,
    invoke_agent_with_tools_resilient,
    invoke_structured_with_fallback,
)
from app.services.tool_resolver import ToolResolver
from app.graphs.human_review import (
    human_review_node,
    is_human_loop_enabled,
    route_after_human_review,
)
from app.graphs.utils import (
    execution_time_seconds,
    extract_content,
    failed_updates,
    running_updates,
)
from app.models.state import AgentNexusState


class SupervisorDecision(BaseModel):
    next_agent: str = Field(
        description="The next agent to run, or FINISH when the task is complete."
    )
    reasoning: str = Field(description="Short explanation for the routing decision.")


def _crew_from_state(
    state: AgentNexusState,
    crew_by_id: dict[str, AgentDefinition],
) -> list[AgentDefinition]:
    crew_ids = state.get("intermediate_results", {}).get("crew", [])
    return [crew_by_id[agent_id] for agent_id in crew_ids if agent_id in crew_by_id]


def _supervisor_prompt(state: AgentNexusState, crew: list[AgentDefinition]) -> str:
    agent_lines = "\n".join(
        f"- {agent.agent_id} ({agent.llm_model}, tools={list(agent.tools)}): {agent.description}"
        for agent in crew
    )
    completed = state.get("intermediate_results", {}).get("agent_outputs", {})
    completed_lines = (
        "\n".join(f"- {agent_id}: done" for agent_id in completed)
        if completed
        else "- none yet"
    )
    options = ", ".join([agent.agent_id for agent in crew] + [FINISH_AGENT])
    return (
        "You are the workflow supervisor for a multi-agent team.\n"
        f"Task: {state['task_description']}\n\n"
        f"Available agents:\n{agent_lines}\n\n"
        f"Completed agents:\n{completed_lines}\n\n"
        f"Choose the next agent from: {options}\n"
        "Return FINISH when the task is sufficiently complete."
    )


def _worker_prompt(state: AgentNexusState, agent: AgentDefinition) -> list:
    outputs = state.get("intermediate_results", {}).get("agent_outputs", {})
    context_lines = "\n\n".join(
        f"[{agent_id}]\n{content}" for agent_id, content in outputs.items()
    )
    context_block = context_lines or "No prior agent output yet."
    return [
        SystemMessage(content=agent.role),
        HumanMessage(
            content=(
                f"Task: {state['task_description']}\n\n"
                f"Work completed so far:\n{context_block}\n\n"
                f"As the {agent.name}, provide your contribution."
            )
        ),
    ]


def create_multi_agent_graph(
    factory: LLMFactory,
    crew: list[AgentDefinition],
    *,
    tool_resolver: ToolResolver,
    checkpointer: BaseCheckpointSaver | None = None,
) -> CompiledStateGraph:
    if not crew:
        raise ValueError("Multi-agent graph requires at least one agent in the crew.")

    crew_by_id = {agent.agent_id: agent for agent in crew}
    workflow = StateGraph(AgentNexusState)
    supervisor_model = settings.supervisor_model or settings.default_model

    def prepare_node(state: AgentNexusState) -> dict:
        active_crew = _crew_from_state(state, crew_by_id) or crew
        return {
            **running_updates(state, current_agent="supervisor"),
            "next_agent": active_crew[0].agent_id,
            "intermediate_results": {
                **state.get("intermediate_results", {}),
                "crew": crew_agent_ids(active_crew),
                "agent_outputs": {},
                "supervisor_steps": 0,
                "routing_history": [],
            },
        }

    async def supervisor_node(state: AgentNexusState) -> dict:
        if state.get("status") == "failed":
            return {"next_agent": FINISH_AGENT}

        now = datetime.now(timezone.utc)
        active_crew = _crew_from_state(state, crew_by_id) or crew
        allowed = {agent.agent_id for agent in active_crew} | {FINISH_AGENT}
        intermediate = dict(state.get("intermediate_results", {}))
        steps = int(intermediate.get("supervisor_steps", 0))

        if steps >= MAX_SUPERVISOR_STEPS:
            return {"next_agent": FINISH_AGENT, "current_agent": "supervisor", "updated_at": now}

        try:
            decision, _, supervisor_warnings = await invoke_structured_with_fallback(
                factory,
                primary_model=supervisor_model,
                messages=[_supervisor_prompt(state, active_crew)],
                schema=SupervisorDecision,
            )
            next_agent = decision.next_agent
            reasoning = decision.reasoning

            if next_agent not in allowed:
                pending = [
                    agent.agent_id
                    for agent in active_crew
                    if agent.agent_id not in intermediate.get("agent_outputs", {})
                ]
                next_agent = pending[0] if pending else FINISH_AGENT

            routing_history = list(intermediate.get("routing_history", []))
            routing_history.append({"next_agent": next_agent, "reasoning": reasoning})

            supervisor_intermediate = {
                **intermediate,
                "supervisor_steps": steps + 1,
                "routing_history": routing_history,
            }
            if supervisor_warnings:
                supervisor_intermediate["llm_fallback_warnings"] = [
                    *intermediate.get("llm_fallback_warnings", []),
                    *supervisor_warnings,
                ]

            return {
                "next_agent": next_agent,
                "current_agent": "supervisor",
                "intermediate_results": supervisor_intermediate,
                "updated_at": now,
            }
        except Exception as exc:
            return failed_updates(state, exc)

    def route_from_supervisor(state: AgentNexusState) -> Literal["finalize"] | str:
        if state.get("status") == "failed":
            return "finalize"
        next_agent = state.get("next_agent")
        if next_agent == FINISH_AGENT or not next_agent:
            return "finalize"
        return next_agent

    def make_worker_node(agent: AgentDefinition):
        async def worker_node(state: AgentNexusState) -> dict:
            now = datetime.now(timezone.utc)
            try:
                response, emitted_messages, tool_metadata, model_used = (
                    await invoke_agent_with_tools_resilient(
                        factory,
                        agent.llm_model,
                        _worker_prompt(state, agent),
                        list(agent.tools),
                        state=state,
                        tool_resolver=tool_resolver,
                    )
                )

                intermediate = dict(state.get("intermediate_results", {}))
                agent_outputs = dict(intermediate.get("agent_outputs", {}))
                agent_outputs[agent.agent_id] = extract_content(response)

                return {
                    **build_tool_aware_updates(
                        response=response,
                        emitted_messages=emitted_messages,
                        tool_metadata=tool_metadata,
                        state=state,
                        model=model_used,
                        status="running",
                        now=now,
                        extra_intermediate={"agent_outputs": agent_outputs},
                    ),
                    "current_agent": agent.agent_id,
                    "next_agent": None,
                }
            except Exception as exc:
                return failed_updates(state, exc)

        return worker_node

    async def finalize_node(state: AgentNexusState) -> dict:
        now = datetime.now(timezone.utc)
        if state.get("status") == "failed":
            return {
                "execution_time_seconds": execution_time_seconds(state),
                "updated_at": now,
            }

        outputs = state.get("intermediate_results", {}).get("agent_outputs", {})
        crew_ids = state.get("intermediate_results", {}).get("crew", crew_agent_ids(crew))
        final_output = next(
            (outputs[agent_id] for agent_id in reversed(crew_ids) if agent_id in outputs),
            None,
        )
        status = "running" if is_human_loop_enabled(state) else "completed"
        return {
            "final_output": final_output,
            "status": status,
            "current_agent": None,
            "next_agent": FINISH_AGENT,
            "execution_time_seconds": execution_time_seconds(state),
            "error_message": None,
            "updated_at": now,
        }

    def route_after_human(state: AgentNexusState) -> Literal["supervisor"] | str:
        target = route_after_human_review(state, revise_target="supervisor")
        if target == "__end__":
            return END
        return "supervisor"

    workflow.add_node("prepare", prepare_node)
    workflow.add_node("supervisor", supervisor_node)
    workflow.add_node("finalize", finalize_node)
    workflow.add_node("human_review", human_review_node)

    for agent in crew:
        workflow.add_node(agent.agent_id, make_worker_node(agent))

    workflow.add_edge(START, "prepare")
    workflow.add_edge("prepare", "supervisor")

    route_map: dict[str, str] = {agent_id: agent_id for agent_id in crew_agent_ids(crew)}
    route_map["finalize"] = "finalize"
    workflow.add_conditional_edges("supervisor", route_from_supervisor, route_map)

    for agent_id in crew_agent_ids(crew):
        workflow.add_edge(agent_id, "supervisor")

    workflow.add_edge("finalize", "human_review")
    workflow.add_conditional_edges("human_review", route_after_human, ["supervisor", END])
    return workflow.compile(checkpointer=checkpointer)