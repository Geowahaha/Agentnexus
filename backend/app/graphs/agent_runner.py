from typing import TypeVar

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AIMessage, BaseMessage, ToolMessage
from pydantic import BaseModel

from app.core.llm import LLMFactory
from app.graphs.utils import (
    accumulate_usage,
    extract_content,
    fallback_models_for,
    format_llm_error,
    is_recoverable_llm_error,
    provider_configured,
)
from app.models.state import AgentNexusState
from app.services.bridge_context import get_bridge_tool_context
from app.services.tool_resolver import ToolResolver
from app.tools.bridge_catalog import BRIDGE_TOOL_NAMES

MAX_TOOL_ROUNDS = 5


async def invoke_agent_with_tools(
    llm: BaseChatModel,
    messages: list[BaseMessage],
    tool_names: list[str],
    *,
    model: str,
    state: AgentNexusState,
    tool_resolver: ToolResolver,
) -> tuple[AIMessage, list[BaseMessage], dict]:
    effective_tool_names = list(tool_names)
    if get_bridge_tool_context() is not None:
        for bridge_name in BRIDGE_TOOL_NAMES:
            if bridge_name not in effective_tool_names:
                effective_tool_names.append(bridge_name)

    tools = await tool_resolver.resolve_tools(effective_tool_names)
    if not tools:
        response = await llm.ainvoke(messages)
        if not isinstance(response, AIMessage):
            response = AIMessage(content=str(response))
        return response, [response], {"tool_calls": []}

    bound_llm = llm.bind_tools(tools)
    tool_map = {tool.name: tool for tool in tools}
    conversation = list(messages)
    emitted_messages: list[BaseMessage] = []
    tool_log: list[dict] = []

    response: AIMessage = AIMessage(content="")
    for _ in range(MAX_TOOL_ROUNDS):
        response = await bound_llm.ainvoke(conversation)
        if not isinstance(response, AIMessage):
            response = AIMessage(content=str(response))

        emitted_messages.append(response)
        conversation.append(response)

        if not response.tool_calls:
            break

        for call in response.tool_calls:
            tool = tool_map.get(call["name"])
            if tool is None:
                output = f"Unknown tool: {call['name']}"
            else:
                output = await tool.ainvoke(call["args"])

            tool_log.append(
                {
                    "tool": call["name"],
                    "input": call["args"],
                    "output": str(output),
                }
            )
            tool_message = ToolMessage(content=str(output), tool_call_id=call["id"])
            emitted_messages.append(tool_message)
            conversation.append(tool_message)

    usage = accumulate_usage(state, [msg for msg in emitted_messages if isinstance(msg, AIMessage)], model)
    return response, emitted_messages, {"tool_calls": tool_log, **usage}


async def invoke_agent_with_tools_resilient(
    factory: LLMFactory,
    primary_model: str,
    messages: list[BaseMessage],
    tool_names: list[str],
    *,
    state: AgentNexusState,
    tool_resolver: ToolResolver,
) -> tuple[AIMessage, list[BaseMessage], dict, str]:
    warnings: list[str] = []
    last_error: Exception | None = None

    for model in fallback_models_for(primary_model):
        if not provider_configured(factory, model):
            warnings.append(f"Skipped fallback model '{model}' — provider API key not configured.")
            continue
        llm = factory.get(model)
        try:
            response, emitted_messages, tool_metadata = await invoke_agent_with_tools(
                llm,
                messages,
                tool_names,
                model=model,
                state=state,
                tool_resolver=tool_resolver,
            )
            if model != primary_model:
                warnings.append(
                    f"Primary model '{primary_model}' unavailable; used fallback '{model}'."
                )
            if warnings:
                tool_metadata["llm_fallback_warnings"] = warnings
            return response, emitted_messages, tool_metadata, model
        except Exception as exc:
            last_error = exc
            if not is_recoverable_llm_error(exc):
                raise
            warnings.append(f"Model '{model}' failed: {format_llm_error(exc)}")

    if last_error is not None:
        raise last_error
    raise RuntimeError(f"No configured LLM provider available for '{primary_model}'.")


TSchema = TypeVar("TSchema", bound=BaseModel)


async def invoke_structured_with_fallback(
    factory: LLMFactory,
    *,
    primary_model: str,
    messages: list[BaseMessage | str],
    schema: type[TSchema],
) -> tuple[TSchema, str, list[str]]:
    warnings: list[str] = []
    last_error: Exception | None = None

    for model in fallback_models_for(primary_model):
        if not provider_configured(factory, model):
            warnings.append(f"Skipped fallback model '{model}' — provider API key not configured.")
            continue
        llm = factory.get(model)
        structured = llm.with_structured_output(schema)
        try:
            result = await structured.ainvoke(messages)
            if not isinstance(result, schema):
                result = schema.model_validate(result)
            if model != primary_model:
                warnings.append(
                    f"Primary model '{primary_model}' unavailable; supervisor used fallback '{model}'."
                )
            return result, model, warnings
        except Exception as exc:
            last_error = exc
            if not is_recoverable_llm_error(exc):
                raise
            warnings.append(f"Model '{model}' failed: {format_llm_error(exc)}")

    if last_error is not None:
        raise last_error
    raise RuntimeError(f"No configured LLM provider available for '{primary_model}'.")


def build_tool_aware_updates(
    *,
    response: AIMessage,
    emitted_messages: list[BaseMessage],
    tool_metadata: dict,
    state: AgentNexusState,
    model: str,
    status: str,
    now,
    extra_intermediate: dict | None = None,
) -> dict:
    intermediate = dict(state.get("intermediate_results") or {})
    if tool_metadata.get("tool_calls"):
        intermediate["tool_calls"] = tool_metadata["tool_calls"]
    if tool_metadata.get("llm_fallback_warnings"):
        intermediate["llm_fallback_warnings"] = tool_metadata["llm_fallback_warnings"]
    if extra_intermediate:
        intermediate.update(extra_intermediate)

    updates: dict = {
        "messages": emitted_messages,
        "final_output": extract_content(response),
        "status": status,
        "error_message": None,
        "updated_at": now,
        "intermediate_results": intermediate,
    }

    if "total_tokens" in tool_metadata:
        updates["total_tokens"] = tool_metadata["total_tokens"]
        updates["total_cost_usd"] = tool_metadata["total_cost_usd"]
    else:
        from app.graphs.utils import usage_updates

        updates.update(usage_updates(state, response, model))

    return updates