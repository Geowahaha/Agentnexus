"""Build verified case studies (showcases) from completed expert-skill workflows."""

from __future__ import annotations

import re

from app.models.expert_skill import ExpertSkill
from app.models.showcase import SkillShowcase
from app.repositories.showcase_repository import ShowcaseRepository


def _extract_qa_verdict(final_output: str) -> str | None:
    for pattern in (
        r"Verdict:\s*\*?\*?(READY|NEEDS_CORRECTION)\*?\*?",
        r"\*\*Verdict\*\*\s*[|:]\s*\*?\*?(READY|NEEDS_CORRECTION)",
    ):
        match = re.search(pattern, final_output, re.IGNORECASE)
        if match:
            return match.group(1).upper()
    return None


def _truncate_sample(final_output: str, *, max_chars: int = 12000) -> str:
    text = final_output.strip()
    if len(text) <= max_chars:
        return text
    return text[: max_chars - 3] + "..."


class ShowcaseService:
    def __init__(self, repository: ShowcaseRepository) -> None:
        self._repository = repository

    async def create_from_workflow(
        self,
        *,
        skill: ExpertSkill,
        workflow_id: str,
        workflow_state: dict,
        title: str | None = None,
        site_name: str | None = None,
        site_url: str | None = None,
    ) -> SkillShowcase:
        if workflow_state.get("status") != "completed":
            raise ValueError("Only completed workflows can become case studies.")

        final_output = str(workflow_state.get("final_output") or "").strip()
        if len(final_output) < 200:
            raise ValueError("Workflow output is too short for a case study.")

        task = str(workflow_state.get("task_description") or "").strip()
        intermediate = workflow_state.get("intermediate_results") or {}
        delivery_quality = intermediate.get("delivery_quality") or "full"
        verdict = _extract_qa_verdict(final_output)

        exec_seconds = workflow_state.get("execution_time_seconds")
        stats = {
            "workflow_id": workflow_id,
            "delivery_quality": str(delivery_quality),
            "runtime": f"{exec_seconds:.0f}s" if exec_seconds else "—",
        }
        if verdict:
            stats["qa_verdict"] = verdict

        highlights = []
        if verdict:
            highlights.append(f"QA: {verdict}")
        if exec_seconds:
            highlights.append(f"Runtime: {exec_seconds:.0f}s")
        highlights.append("Verified OBOLLA workflow run")

        deliverables = []
        steps = intermediate.get("expert_skill_steps") or {}
        if isinstance(steps, dict):
            deliverables = [f"{key.replace('_', ' ').title()} step" for key in steps.keys()][:6]

        return await self._repository.create(
            expert_skill_id=skill.id,
            title=title or f"{skill.name} — verified run",
            site_name=site_name or "Customer task",
            site_url=site_url or "",
            summary=(
                f"Real completed run of {skill.name}. "
                f"Task: {task[:240]}{'…' if len(task) > 240 else ''}"
            ),
            workflow_id=workflow_id,
            sample_output=_truncate_sample(final_output),
            metric_label="QA verdict" if verdict else "Delivery",
            metric_value=verdict or str(delivery_quality).upper(),
            highlights=highlights,
            deliverables=deliverables or ["Pipeline output", "QA-reviewed deliverables"],
            stats=stats,
            is_featured=False,
        )