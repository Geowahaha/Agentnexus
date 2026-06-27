from datetime import datetime, timezone
from typing import Literal

from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph

from app.agents.definitions import AgentDefinition
from app.core.config import settings
from app.core.llm import LLMFactory
from app.graphs.agent_runner import build_tool_aware_updates, invoke_agent_with_tools_resilient
from app.services.tool_resolver import ToolResolver
from app.graphs.human_review import (
    human_review_node,
    is_human_loop_enabled,
    route_after_human_review,
)
from app.graphs.utils import execution_time_seconds, failed_updates, running_updates
from app.models.state import AgentNexusState


def create_single_agent_graph(
    factory: LLMFactory,
    agent_def: AgentDefinition | None = None,
    *,
    tool_resolver: ToolResolver,
    checkpointer: BaseCheckpointSaver | None = None,
) -> CompiledStateGraph:
    model = agent_def.llm_model if agent_def else None
    tool_names = list(agent_def.tools) if agent_def else []
    workflow = StateGraph(AgentNexusState)

    def prepare_node(state: AgentNexusState) -> dict:
        current_agent = (
            agent_def.agent_id
            if agent_def
            else state.get("agent_id") or "default_agent"
        )
        updates = running_updates(state, current_agent=current_agent)
        if not state["messages"]:
            updates["messages"] = [HumanMessage(content=state["task_description"])]
        return updates

    async def agent_node(state: AgentNexusState) -> dict:
        now = datetime.now(timezone.utc)
        messages = list(state["messages"])
        role = state.get("agent_role") or (agent_def.role if agent_def else None)
        if role:
            messages = [SystemMessage(content=role), *messages]

        active_model = agent_def.llm_model if agent_def else (model or settings.default_model)
        status: Literal["running", "completed"] = (
            "running" if is_human_loop_enabled(state) else "completed"
        )

        try:
            response, emitted_messages, tool_metadata, model_used = (
                await invoke_agent_with_tools_resilient(
                    factory,
                    active_model,
                    messages,
                    tool_names,
                    state=state,
                    tool_resolver=tool_resolver,
                )
            )
            return {
                **build_tool_aware_updates(
                    response=response,
                    emitted_messages=emitted_messages,
                    tool_metadata=tool_metadata,
                    state=state,
                    model=model_used,
                    status=status,
                    now=now,
                ),
                "execution_time_seconds": execution_time_seconds(state),
            }
        except Exception as exc:
            return failed_updates(state, exc)

    def route_after_human(state: AgentNexusState) -> Literal["__end__", "agent"]:
        target = route_after_human_review(state, revise_target="agent")
        if target == "__end__":
            return END
        return "agent"

    workflow.add_node("prepare", prepare_node)
    workflow.add_node("agent", agent_node)
    workflow.add_node("human_review", human_review_node)
    workflow.add_edge(START, "prepare")
    workflow.add_edge("prepare", "agent")
    workflow.add_edge("agent", "human_review")
    workflow.add_conditional_edges("human_review", route_after_human, ["agent", END])
    return workflow.compile(checkpointer=checkpointer)