#!/usr/bin/env python3
"""Inspect workflow charge + checkpoint status (dev ops)."""

import asyncio
import json
import sys

import re

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

STEP_FAILED = "**Step failed**"


def _hydrate_steps(final_output: str | None) -> list[str]:
    if not final_output:
        return []
    steps: dict[str, str] = {}
    for part in re.split(r"(?m)^## ", final_output.strip()):
        part = part.strip()
        if not part or part.startswith("Warnings"):
            continue
        title, _, _body = part.partition("\n")
        slug = re.sub(r"[^a-z0-9]+", "_", title.lower()).strip("_") or "section"
        steps[slug] = _
    return list(steps.keys())


def _delivery_quality(final_output: str | None, err: str | None) -> str:
    lowered = (err or "").lower()
    if "credits exhausted" in lowered or "resource_exhausted" in lowered:
        if "fallback" not in lowered:
            return "failed"
        return "degraded"
    if final_output and len(final_output) > 500:
        return "degraded" if "step failed" in lowered else "full"
    return "failed"


IDS = sys.argv[1:] or [
    "1b4bcec0-1e52-4432-8bbd-4dfb9e312ca5",
    "f2af58dc-3705-4c05-bb01-11984e2889d8",
    "525e4326-0653-44cc-b041-2c0263b17353",
    "00663ea4-2949-4e59-b62e-b47d3c9fd747",
]


async def main() -> None:
    engine = create_async_engine(
        "postgresql+asyncpg://agentnexus:agentnexus@127.0.0.1:5432/agentnexus"
    )
    async with engine.connect() as conn:
        for wid in IDS:
            r = await conn.execute(
                text(
                    "SELECT workflow_id, marketplace_cost_usd, llm_cost_usd, total_cost_usd "
                    "FROM workflow_charges WHERE workflow_id = :w"
                ),
                {"w": wid},
            )
            charge = r.mappings().first()
            cp = await conn.execute(
                text(
                    "SELECT checkpoint FROM checkpoints "
                    "WHERE thread_id = :w ORDER BY checkpoint_id DESC LIMIT 1"
                ),
                {"w": wid},
            )
            row = cp.mappings().first()
            status = err = task = None
            steps: list[str] = []
            failed_steps: list[str] = []
            hydrated_steps: list[str] = []
            delivery_quality = None
            if row:
                ch = row["checkpoint"]
                if isinstance(ch, (bytes, str)):
                    try:
                        ch = json.loads(ch if isinstance(ch, str) else ch.decode())
                    except Exception:
                        ch = {}
                vals = ch.get("channel_values") or {} if isinstance(ch, dict) else {}
                status = vals.get("status")
                err = vals.get("error_message")
                task = (vals.get("task_description") or "")[:100]
                ir = vals.get("intermediate_results") or {}
                step_map = ir.get("expert_skill_steps") or {}
                steps = list(step_map.keys())
                failed_steps = [
                    k for k, v in step_map.items() if "**Step failed**" in str(v)
                ]
                hydrated_steps = _hydrate_steps(vals.get("final_output"))
                delivery_quality = _delivery_quality(vals.get("final_output"), err)
            print("---", wid)
            print("charge:", dict(charge) if charge else None)
            print("status:", status, "| task:", task)
            print("steps:", steps)
            print("hydrated_steps:", hydrated_steps)
            print("failed_steps:", failed_steps)
            print("delivery_quality:", delivery_quality)
            print("err:", (err or "")[:300])
            if row and isinstance(ch, dict):
                fo = vals.get("final_output")
                print("final_output_len:", len(fo or "") if fo else 0)
                print("intermediate_keys:", list((vals.get("intermediate_results") or {}).keys()))


if __name__ == "__main__":
    asyncio.run(main())