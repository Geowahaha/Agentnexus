import json
import re
from datetime import datetime, timezone

# re used by detect_scan_lang via task string checks

from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph

from app.core.llm import LLMFactory
from app.expert_skills.custom_defaults import resolve_crew_config, skill_context_text
from app.expert_skills.model_tiers import runtime_tier_meta
from app.expert_skills.site_intelligence import format_site_intelligence, gather_site_intelligence
from app.graphs.expert_skill_prompts import build_llm_prompt
from app.graphs.utils import (
    STEP_FAILED_MARKER,
    append_expert_skill_warnings,
    assess_expert_skill_delivery,
    execution_time_seconds,
    extract_content,
    failed_updates,
    format_llm_error,
    invoke_llm_with_fallback,
    media_cost_updates,
    running_updates,
    usage_updates,
)
from app.services.xai_imagine_service import (
    XaiImagineError,
    extract_image_prompt_from_step_output,
    generate_image,
)
from app.models.state import AgentNexusState
from app.smart_farm.telemetry_context import (
    build_japanese_melon_deliverable,
    format_dataset_export_markdown,
    is_japanese_melon_dataset_pack,
    is_smart_farm_skill,
    load_telemetry_markdown,
    resolve_authoritative_download_url,
    sanitize_smart_farm_download_urls,
)
from app.services.aibotauth_proof_client import create_proof_from_scan, format_proof_deliverable
from app.services.agent_ready.isitagentready_client import IsitagentreadyClient
from app.services.agent_ready.orchestrator import AgentReadyOrchestrator
from app.services.mcp_service import MCPService
from app.utils.url_normalize import extract_target_url

DEFAULT_STEPS = [
    {"id": "scan", "type": "mcp", "tool": "mcp.aibotauth.scan", "title": "AIBotAuth Scan"},
    {"id": "analyze", "type": "llm", "model": "claude-sonnet-4-5-20250929", "title": "Auditor"},
    {"id": "improve", "type": "llm", "model": "gemini-2.5-flash", "title": "Fix Pack Generator"},
    {"id": "qa", "type": "llm", "model": "grok-3-mini", "title": "QA Challenger"},
]


def detect_scan_lang(task: str, url: str | None) -> str:
    lowered = task.lower()
    if "lang=th" in lowered or "ภาษาไทย" in task or "thai" in lowered:
        return "th"
    if url and (".th/" in url.lower() or url.lower().rstrip("/").endswith(".th")):
        return "th"
    return "en"


def _is_mcp_scan_auth_failure(scan_data: dict) -> bool:
    """AIBotAuth MCP returns only {\"status\":401} when the MCP caller is not authorized."""
    if not isinstance(scan_data, dict):
        return False
    keys = set(scan_data.keys())
    return keys <= {"status"} and scan_data.get("status") in (401, 403)


def _scan_access_warnings(scan_data: dict, url: str, lang: str = "en") -> list[str]:
    warnings: list[str] = []
    status = scan_data.get("status")
    if _is_mcp_scan_auth_failure(scan_data):
        if lang == "th":
            warnings.append(
                "AIBotAuth MCP ตอบ 401 — OBOLLA ยังไม่ได้เชื่อม API key กับ aibotauth.com "
                "(ไม่ใช่เว็บเป้าหมายบล็อกบอท) ใช้ isitagentready fallback หรือตั้งค่า AIBOTAUTH_MCP_API_KEY"
            )
        else:
            warnings.append(
                "AIBotAuth MCP returned 401 — OBOLLA is not authorized to call the scanner API "
                "(this is not the target site blocking bots). Use isitagentready fallback or set "
                "AIBOTAUTH_MCP_API_KEY."
            )
    elif status in (401, 403):
        if lang == "th":
            warnings.append(
                f"เว็บเป้าหมายตอบ HTTP {status} ต่อสแกนเนอร์ — {url} อาจบล็อกบอทหรือต้องล็อกอิน "
                "คะแนนแต่ละชั้นจะจำกัด แก้การเข้าถึงหรือกฎ WAF เพื่อ audit เต็มรูปแบบ"
            )
        else:
            warnings.append(
                f"Target site returned HTTP {status} for the scanner — {url} may block bots or "
                "require authentication. Layer scores will be limited; fix site access or WAF rules "
                "for a full audit."
            )
    error = scan_data.get("error")
    if isinstance(error, str) and error.strip():
        warnings.append(f"Scanner reported: {error.strip()}")
    return warnings


def _format_scan_output(raw: str, scan_data: dict, url: str, lang: str = "en") -> tuple[str, list[str]]:
    warnings = _scan_access_warnings(scan_data, url, lang=lang)
    if not warnings:
        return raw, warnings
    banner_title = "⚠️ สแกนไม่ครบ — เว็บบล็อกบอท" if lang == "th" else "⚠️ Scan access limited"
    banner = banner_title + "\n" + "\n".join(f"- {item}" for item in warnings)
    return f"{banner}\n\n{raw}", warnings


def _make_llm_node(factory: LLMFactory, step: dict, pack_slug: str, skill_context: str):
    model = step.get("model") or "gemini-2.5-flash"
    step_id = step.get("id", "llm")

    async def node(state: AgentNexusState) -> dict:
        now = datetime.now(timezone.utc)
        intermediate = dict(state.get("intermediate_results", {}))
        step_outputs = dict(intermediate.get("expert_skill_steps", {}))
        prior = "\n\n".join(f"### {key}\n{val}" for key, val in step_outputs.items())
        target_url = intermediate.get("target_url")

        smart_farm_meta = dict(intermediate.get("smart_farm_meta") or {})
        task_context = state.get("task_context") or {}
        skill_slug = str(task_context.get("expert_skill_slug") or "")
        if (
            is_japanese_melon_dataset_pack(pack_slug=pack_slug, skill_slug=skill_slug or None)
            and step_id in ("review", "deliver")
        ):
            content = build_japanese_melon_deliverable(
                step_id=step_id,
                smart_farm_meta=smart_farm_meta,
                step_outputs=step_outputs,
            )
            step_outputs[step_id] = content
            updated_intermediate = {
                **intermediate,
                "expert_skill_steps": step_outputs,
            }
            return {
                **running_updates(state, current_agent=step_id),
                "intermediate_results": updated_intermediate,
                "updated_at": now,
            }

        role, task = build_llm_prompt(
            pack_slug=pack_slug,
            step_id=step_id,
            skill_context=skill_context,
            target_url=target_url,
            task_description=state["task_description"],
            step_outputs=step_outputs,
            prior=prior,
        )

        messages = [SystemMessage(content=role), HumanMessage(content=task)]
        step_warnings: list[str] = []
        try:
            response, model_used, step_warnings = await invoke_llm_with_fallback(
                factory,
                primary_model=model,
                messages=messages,
                pack_slug=pack_slug,
            )
            content = extract_content(response)
            if model_used != model:
                content = (
                    f"_Note: ran on fallback model `{model_used}` "
                    f"(configured: `{model}`)._\n\n{content}"
                )
            if is_smart_farm_skill(pack_slug=pack_slug, skill_slug=skill_slug or None) and step_id in (
                "review",
                "deliver",
            ):
                content = sanitize_smart_farm_download_urls(content, step_outputs, smart_farm_meta)
            step_outputs[step_id] = content
            updated_intermediate = append_expert_skill_warnings(
                {**intermediate, "expert_skill_steps": step_outputs},
                step_warnings,
            )
            return {
                **running_updates(state, current_agent=step_id),
                **usage_updates(state, response, model_used),
                "intermediate_results": updated_intermediate,
                "updated_at": now,
            }
        except Exception as exc:
            step_outputs[step_id] = (
                f"**Step failed** ({step.get('title', step_id)})\n\n{format_llm_error(exc)}"
            )
            step_warnings.append(
                f"{step.get('title', step_id)} could not run: {format_llm_error(exc)}"
            )
            updated_intermediate = append_expert_skill_warnings(
                {**intermediate, "expert_skill_steps": step_outputs},
                step_warnings,
            )
            return {
                **running_updates(state, current_agent=step_id),
                "intermediate_results": updated_intermediate,
                "updated_at": now,
            }

    return node


def _make_agent_ready_node(step: dict):
    step_id = step.get("id", "agent_ready")
    action = str(step.get("action") or "analyze")

    async def node(state: AgentNexusState) -> dict:
        now = datetime.now(timezone.utc)
        intermediate = dict(state.get("intermediate_results", {}))
        step_outputs = dict(intermediate.get("expert_skill_steps", {}))
        target_url = intermediate.get("target_url") or extract_target_url(state["task_description"])
        orchestrator = AgentReadyOrchestrator()
        step_warnings: list[str] = []

        if not target_url:
            step_outputs[step_id] = f"**Step failed** ({step.get('title', step_id)})\n\nNo target URL."
            updated_intermediate = {**intermediate, "expert_skill_steps": step_outputs}
            return {
                **running_updates(state, current_agent=step_id),
                "intermediate_results": updated_intermediate,
                "updated_at": now,
            }

        try:
            if action == "verify":
                result = await orchestrator.verify_loop(
                    target_url,
                    target_percent=int(step.get("target_percent") or 95),
                    max_attempts=int(step.get("max_attempts") or 3),
                    purge_between=bool(step.get("purge_between", True)),
                )
                content = orchestrator.format_verify_markdown(result)
                intermediate["agent_ready_verify"] = result
            elif action == "deploy_github":
                repo = step.get("repo") or intermediate.get("github_repo")
                if not repo:
                    raise ValueError("deploy_github requires step.repo or intermediate.github_repo")
                result = await orchestrator.deploy_github_pr(
                    url=target_url,
                    repo=str(repo),
                    base_branch=str(step.get("base_branch") or "main"),
                )
                content = orchestrator.format_deploy_markdown(result, kind="github-pr")
                intermediate["agent_ready_deploy_github"] = result
            elif action == "deploy_cf_pages":
                project_name = step.get("project_name") or intermediate.get("cf_pages_project")
                if not project_name:
                    raise ValueError(
                        "deploy_cf_pages requires step.project_name or intermediate.cf_pages_project"
                    )
                result = await orchestrator.deploy_cloudflare_pages(
                    url=target_url,
                    project_name=str(project_name),
                    branch=str(step.get("branch") or "main"),
                    wait=bool(step.get("wait", True)),
                )
                content = orchestrator.format_deploy_markdown(result, kind="cloudflare-pages")
                intermediate["agent_ready_deploy_cf_pages"] = result
            else:
                result = await orchestrator.analyze(target_url)
                content = orchestrator.format_analyze_markdown(result)
                intermediate["agent_ready_analyze"] = result

            step_outputs[step_id] = content
            updated_intermediate = append_expert_skill_warnings(
                {**intermediate, "expert_skill_steps": step_outputs},
                step_warnings,
            )
            return {
                **running_updates(state, current_agent=step_id),
                "intermediate_results": updated_intermediate,
                "updated_at": now,
            }
        except Exception as exc:
            step_outputs[step_id] = (
                f"**Step failed** ({step.get('title', step_id)})\n\n{format_llm_error(exc)}"
            )
            updated_intermediate = append_expert_skill_warnings(
                {**intermediate, "expert_skill_steps": step_outputs},
                [f"{step.get('title', step_id)}: {format_llm_error(exc)}"],
            )
            return {
                **running_updates(state, current_agent=step_id),
                "intermediate_results": updated_intermediate,
                "updated_at": now,
            }

    return node


def _make_image_gen_node(step: dict, pack_slug: str):
    step_id = step.get("id", "image_generate")
    prompt_step = str(step.get("prompt_step") or "image_prompt")
    model = str(step.get("model") or "grok-imagine-image-quality")
    provider = str(step.get("provider") or "xai")

    async def node(state: AgentNexusState) -> dict:
        now = datetime.now(timezone.utc)
        intermediate = dict(state.get("intermediate_results", {}))
        step_outputs = dict(intermediate.get("expert_skill_steps", {}))
        prior_prompt_text = str(step_outputs.get(prompt_step) or "").strip()
        step_warnings: list[str] = []

        if not prior_prompt_text or STEP_FAILED_MARKER in prior_prompt_text:
            step_outputs[step_id] = (
                f"**Step failed** ({step.get('title', step_id)})\n\n"
                f"Prior step `{prompt_step}` did not produce a usable image prompt."
            )
            updated_intermediate = append_expert_skill_warnings(
                {**intermediate, "expert_skill_steps": step_outputs},
                [f"{step.get('title', step_id)} skipped — image prompt step failed."],
            )
            return {
                **running_updates(state, current_agent=step_id),
                "intermediate_results": updated_intermediate,
                "updated_at": now,
            }

        try:
            prompt, aspect_ratio = extract_image_prompt_from_step_output(prior_prompt_text)
            result = await generate_image(
                prompt=prompt,
                model=model,
                aspect_ratio=aspect_ratio,
            )
            image_url = str(result["url"])
            cost_usd = float(result["cost_usd"])
            aspect_note = f" (aspect: {aspect_ratio})" if aspect_ratio else ""
            content = (
                f"**Generated image** via {provider}/{model}{aspect_note}\n\n"
                f"![Generated social post image]({image_url})\n\n"
                f"**Image URL:** {image_url}\n\n"
                f"**Prompt used:**\n{prompt}\n\n"
                f"_Cost: ${cost_usd:.2f} image generation (billed to wallet)._"
            )
            step_outputs[step_id] = content
            generated_images = list(intermediate.get("generated_images") or [])
            generated_images.append(
                {
                    "step_id": step_id,
                    "url": image_url,
                    "model": model,
                    "prompt": prompt,
                    "aspect_ratio": aspect_ratio,
                    "cost_usd": cost_usd,
                }
            )
            tool_calls = list(intermediate.get("tool_calls") or [])
            tool_calls.append(
                {
                    "tool": f"{provider}.images.generate",
                    "input": {
                        "model": model,
                        "prompt": prompt[:500],
                        "aspect_ratio": aspect_ratio,
                    },
                    "output": image_url,
                }
            )
            updated_intermediate = {
                **intermediate,
                "expert_skill_steps": step_outputs,
                "generated_images": generated_images,
                "tool_calls": tool_calls,
            }
            return {
                **running_updates(state, current_agent=step_id),
                **media_cost_updates(state, cost_usd=cost_usd),
                "intermediate_results": updated_intermediate,
                "updated_at": now,
            }
        except XaiImagineError as exc:
            step_outputs[step_id] = (
                f"**Step failed** ({step.get('title', step_id)})\n\n{exc}"
            )
            step_warnings.append(f"{step.get('title', step_id)}: {exc}")
            updated_intermediate = append_expert_skill_warnings(
                {**intermediate, "expert_skill_steps": step_outputs},
                step_warnings,
            )
            return {
                **running_updates(state, current_agent=step_id),
                "intermediate_results": updated_intermediate,
                "updated_at": now,
            }
        except Exception as exc:
            step_outputs[step_id] = (
                f"**Step failed** ({step.get('title', step_id)})\n\n{format_llm_error(exc)}"
            )
            step_warnings.append(
                f"{step.get('title', step_id)} could not run: {format_llm_error(exc)}"
            )
            updated_intermediate = append_expert_skill_warnings(
                {**intermediate, "expert_skill_steps": step_outputs},
                step_warnings,
            )
            return {
                **running_updates(state, current_agent=step_id),
                "intermediate_results": updated_intermediate,
                "updated_at": now,
            }

    return node


def create_expert_skill_graph(
    factory: LLMFactory,
    *,
    pack_slug: str,
    crew_config: dict,
    mcp_service: MCPService,
    checkpointer: BaseCheckpointSaver | None = None,
    category: str | None = None,
    skill_name: str = "",
    skill_description: str = "",
) -> CompiledStateGraph:
    resolved_config = resolve_crew_config(
        pack_slug,
        crew_config,
        category=category,
        name=skill_name,
        description=skill_description,
    )
    steps = resolved_config.get("steps") or DEFAULT_STEPS
    skill_context = skill_context_text(pack_slug, resolved_config)
    tier_runtime = runtime_tier_meta(resolved_config)
    workflow = StateGraph(AgentNexusState)

    def prepare_node(state: AgentNexusState) -> dict:
        return {
            **running_updates(state, current_agent="prepare"),
            "intermediate_results": {
                **state.get("intermediate_results", {}),
                "expert_skill_steps": {},
                "pack_slug": pack_slug,
                "model_tier_runtime": tier_runtime,
            },
        }

    async def scan_node(state: AgentNexusState) -> dict:
        now = datetime.now(timezone.utc)
        url = extract_target_url(state["task_description"])
        mcp_steps = [s for s in steps if s.get("type") == "mcp"]

        if not mcp_steps:
            task_text = state["task_description"].strip()
            if not task_text:
                return failed_updates(
                    state,
                    ValueError("Please describe your coding task (feature, bug, or refactor)."),
                )
            task_context = state.get("task_context") or {}
            skill_slug = str(task_context.get("expert_skill_slug") or "")
            step_outputs: dict[str, str] = {}
            smart_farm_meta: dict = {}
            if is_smart_farm_skill(pack_slug=pack_slug, skill_slug=skill_slug or None):
                telemetry_md, smart_farm_meta = await load_telemetry_markdown(
                    user_id=state["user_id"],
                    task_description=task_text,
                    task_context=task_context,
                )
                step_outputs["telemetry"] = telemetry_md
                if is_japanese_melon_dataset_pack(
                    pack_slug=pack_slug,
                    skill_slug=skill_slug or None,
                ) and smart_farm_meta.get("farm_id"):
                    from app.core.database import async_session_maker
                    from app.repositories.smart_farm_repository import SmartFarmRepository
                    from app.services.smart_farm_service import SmartFarmService
                    from app.smart_farm.schemas import ExportDatasetRequest

                    try:
                        async with async_session_maker() as session:
                            svc = SmartFarmService(SmartFarmRepository(session))
                            farm_id = str(smart_farm_meta["farm_id"])
                            if smart_farm_meta.get("readings_count", 0) > 0:
                                export_pack = await svc.export_dataset(
                                    state["user_id"],
                                    farm_id,
                                    ExportDatasetRequest(name="marketplace-run", format="json", hours=168),
                                )
                            else:
                                export_pack = await svc.export_schema_template(
                                    state["user_id"],
                                    farm_id,
                                    name="schema-template",
                                )
                        smart_farm_meta["dataset_pack"] = export_pack
                        step_outputs["dataset_export"] = format_dataset_export_markdown(export_pack)
                    except Exception as exc:
                        step_outputs["dataset_export"] = (
                            "## Dataset pack export failed\n"
                            f"Auto-export error: {exc}\n\n"
                            "Open https://obolla.com/smart-farm — ingest telemetry, then export manually."
                        )
            return {
                **running_updates(state, current_agent="intake"),
                "intermediate_results": {
                    **state.get("intermediate_results", {}),
                    "expert_skill_steps": step_outputs,
                    "target_url": url,
                    "task_intake": task_text,
                    "smart_farm_meta": smart_farm_meta,
                },
                "updated_at": now,
            }

        if not url:
            return failed_updates(
                state,
                ValueError(
                    "Please enter a valid URL, e.g. example.com or https://example.com"
                ),
            )

        intermediate = dict(state.get("intermediate_results", {}))
        step_outputs = dict(intermediate.get("expert_skill_steps", {}))
        all_warnings: list[str] = []
        lang = detect_scan_lang(state["task_description"], url)

        proof_meta: dict | None = None
        last_scan_data: dict | None = None

        try:
            for mcp_step in mcp_steps:
                step_id = str(mcp_step.get("id") or "scan")
                tool_name = mcp_step.get("tool", "mcp.aibotauth.scan")
                raw = await mcp_service.invoke_tool(tool_name, {"url": url, "lang": lang})
                try:
                    scan_data = json.loads(raw)
                except json.JSONDecodeError:
                    scan_data = {"raw": raw}

                if _is_mcp_scan_auth_failure(scan_data) and "aibotauth" in tool_name:
                    scanner = IsitagentreadyClient()
                    fallback = await scanner.scan(url)
                    summary = scanner.score_summary(fallback)
                    scan_data = {
                        "source": "isitagentready.com",
                        "level": summary.get("level"),
                        "level_name": summary.get("level_name"),
                        "percent": summary.get("percent"),
                        "pass": summary.get("pass"),
                        "fail": summary.get("fail"),
                        "gaps": summary.get("gaps"),
                        "checks": fallback.get("checks"),
                    }
                    raw = json.dumps(scan_data, indent=2)

                raw_text = raw if isinstance(raw, str) else json.dumps(scan_data, indent=2)
                scan_text, scan_warnings = _format_scan_output(raw_text, scan_data, url, lang=lang)
                step_outputs[step_id] = scan_text
                all_warnings.extend(scan_warnings)

                if (
                    step_id == "scan"
                    and "aibotauth" in tool_name
                    and isinstance(scan_data, dict)
                    and scan_data.get("overall") is not None
                    and not _is_mcp_scan_auth_failure(scan_data)
                ):
                    last_scan_data = scan_data
                    wf_id = str(task_context.get("workflow_id") or state.get("workflow_id") or "")
                    sk_id = task_context.get("expert_skill_id") or None
                    proof_meta = await create_proof_from_scan(
                        url,
                        scan_data,
                        lang=lang,
                        workflow_id=wf_id or None,
                        linked_skill_id=sk_id,
                    )
                    if proof_meta:
                        step_outputs["proof_badge"] = format_proof_deliverable(proof_meta, lang=lang)

            if pack_slug == "seo-expert-analysis":
                intel = await gather_site_intelligence(url, lang=lang)
                step_outputs["site_intel"] = format_site_intelligence(intel)
                if intel.get("fetch_error") or intel.get("warning"):
                    all_warnings.append(
                        f"Site intelligence partial: {intel.get('fetch_error') or intel.get('warning')}"
                    )

            scan_intermediate = {
                **intermediate,
                "expert_skill_steps": step_outputs,
                "target_url": url,
                "scan_result": step_outputs,
                "scan_blocked": bool(all_warnings),
            }
            if proof_meta:
                scan_intermediate["aibotauth_proof"] = proof_meta
            if last_scan_data is not None:
                scan_intermediate["scan_data"] = last_scan_data

            return {
                **running_updates(state, current_agent="scan"),
                "intermediate_results": append_expert_skill_warnings(scan_intermediate, all_warnings),
                "updated_at": now,
            }
        except Exception as exc:
            return failed_updates(state, exc)

    async def finalize_node(state: AgentNexusState) -> dict:
        now = datetime.now(timezone.utc)
        if state.get("status") == "failed":
            return {
                "intermediate_results": dict(state.get("intermediate_results", {})),
                "execution_time_seconds": execution_time_seconds(state),
                "updated_at": now,
            }

        intermediate = dict(state.get("intermediate_results", {}))
        steps_out = dict(intermediate.get("expert_skill_steps", {}))
        smart_farm_meta = dict(intermediate.get("smart_farm_meta") or {})
        pack_slug_final = str(intermediate.get("pack_slug") or "")
        warnings = list(intermediate.get("expert_skill_warnings", []))
        for sid, body in list(steps_out.items()):
            if isinstance(body, str):
                steps_out[sid] = sanitize_smart_farm_download_urls(body, steps_out, smart_farm_meta)
        intermediate["expert_skill_steps"] = steps_out
        tier_runtime = intermediate.get("model_tier_runtime") or {}
        if tier_runtime.get("downgraded"):
            note = tier_runtime.get("note_en") or tier_runtime.get("note_th")
            if note and note not in warnings:
                warnings.insert(0, str(note))
        sections = []
        emitted: set[str] = set()
        for step in steps:
            sid = step.get("id")
            if sid and sid in steps_out:
                sections.append(f"## {step.get('title', sid)}\n{steps_out[sid]}")
                emitted.add(sid)
        if "site_intel" in steps_out and "site_intel" not in emitted:
            sections.insert(
                min(2, len(sections)),
                f"## Site Intelligence (auto-extracted)\n{steps_out['site_intel']}",
            )
        if warnings:
            sections.insert(
                0,
                "## Warnings\n" + "\n".join(f"- {item}" for item in warnings),
            )
        proof_block = steps_out.get("proof_badge")
        if proof_block:
            sections.append(proof_block)
        final_output = "\n\n".join(sections) if sections else None
        if is_japanese_melon_dataset_pack(pack_slug=pack_slug_final):
            final_output = sanitize_smart_farm_download_urls(final_output or "", steps_out, smart_farm_meta)
            official_url = resolve_authoritative_download_url(steps_out, smart_farm_meta)
            if official_url and official_url not in (final_output or ""):
                final_output = (
                    (final_output or "")
                    + "\n\n## Official dataset download\n"
                    + f"[Download dataset pack]({official_url})\n\n"
                    + f"`{official_url}`"
                )
        warning_summary = "; ".join(warnings) if warnings else None

        preview_state = {**state, "final_output": final_output, "intermediate_results": intermediate}
        delivery = assess_expert_skill_delivery(preview_state, crew_steps=steps)
        updated_intermediate = {
            **intermediate,
            "delivery_quality": delivery["delivery_quality"],
            "marketplace_fee_multiplier": delivery["marketplace_fee_multiplier"],
            "failed_llm_steps": delivery["failed_llm_steps"],
            "successful_llm_steps": delivery["successful_llm_steps"],
        }

        status = "completed"
        error_message = warning_summary
        if delivery["delivery_quality"] == "failed":
            status = "failed"
            failed_names = ", ".join(delivery["failed_llm_steps"]) or "all LLM steps"
            billing_note = "Marketplace fee waived — deliverables could not be produced."
            error_message = (
                f"Expert skill run failed: {failed_names}. {billing_note}"
                + (f" Warnings: {warning_summary}" if warning_summary else "")
            )
        elif delivery["delivery_quality"] == "degraded":
            pct = int(delivery["marketplace_fee_multiplier"] * 100)
            degraded_note = f"Partial delivery — marketplace fee reduced to {pct}%."
            error_message = (
                f"{degraded_note} Failed steps: {', '.join(delivery['failed_llm_steps'])}."
                + (f" {warning_summary}" if warning_summary else "")
            )

        return {
            "final_output": final_output,
            "status": status,
            "current_agent": None,
            "intermediate_results": updated_intermediate,
            "execution_time_seconds": execution_time_seconds(state),
            "error_message": error_message,
            "updated_at": now,
        }

    workflow.add_node("prepare", prepare_node)
    workflow.add_node("scan", scan_node)
    workflow.add_node("finalize", finalize_node)

    prev = "prepare"
    workflow.add_edge(START, "prepare")
    workflow.add_edge("prepare", "scan")
    prev = "scan"

    for step in steps:
        step_type = step.get("type")
        if step_type not in ("llm", "image_gen", "agent_ready"):
            continue
        node_name = step["id"]
        if step_type == "image_gen":
            workflow.add_node(node_name, _make_image_gen_node(step, pack_slug))
        elif step_type == "agent_ready":
            workflow.add_node(node_name, _make_agent_ready_node(step))
        else:
            workflow.add_node(
                node_name, _make_llm_node(factory, step, pack_slug, skill_context)
            )
        workflow.add_edge(prev, node_name)
        prev = node_name

    workflow.add_edge(prev, "finalize")
    workflow.add_edge("finalize", END)
    return workflow.compile(checkpointer=checkpointer)