from datetime import datetime, timezone

from langgraph.graph import END, START, StateGraph

from app.models.state import AgentNexusState


def _start_node(state: AgentNexusState) -> dict:
    return {
        "status": "running",
        "updated_at": datetime.now(timezone.utc),
    }


def _finalize_node(state: AgentNexusState) -> dict:
    return {
        "status": "completed",
        "updated_at": datetime.now(timezone.utc),
    }


def build_base_graph() -> StateGraph:
    """Minimal LangGraph scaffold — extend with agent nodes and routing."""
    graph = StateGraph(AgentNexusState)
    graph.add_node("start", _start_node)
    graph.add_node("finalize", _finalize_node)
    graph.add_edge(START, "start")
    graph.add_edge("start", "finalize")
    graph.add_edge("finalize", END)
    return graph