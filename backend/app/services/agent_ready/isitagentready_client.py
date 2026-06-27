from __future__ import annotations

from typing import Any

import httpx

SCAN_URL = "https://isitagentready.com/api/scan"


class IsitagentreadyClient:
    async def scan(self, url: str, *, timeout: float = 90.0) -> dict[str, Any]:
        async with httpx.AsyncClient(timeout=timeout) as client:
            res = await client.post(
                SCAN_URL,
                json={"url": url.rstrip("/")},
                headers={"content-type": "application/json"},
            )
            res.raise_for_status()
            return res.json()

    def flatten_checks(self, scan: dict[str, Any]) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []
        for category, group in (scan.get("checks") or {}).items():
            if not isinstance(group, dict):
                continue
            for check_id, result in group.items():
                if not isinstance(result, dict) or not result.get("status"):
                    continue
                rows.append(
                    {
                        "category": category,
                        "id": check_id,
                        "status": result["status"],
                        "message": result.get("message"),
                    }
                )
        return rows

    def score_summary(self, scan: dict[str, Any]) -> dict[str, Any]:
        rows = self.flatten_checks(scan)
        scored = [r for r in rows if r["status"] in ("pass", "fail")]
        passed = sum(1 for r in scored if r["status"] == "pass")
        failed = sum(1 for r in scored if r["status"] == "fail")
        neutral = sum(1 for r in rows if r["status"] == "neutral")
        total = len(scored)
        percent = round(100 * passed / total) if total else 0
        gaps = [r for r in scored if r["status"] == "fail"]
        return {
            "level": scan.get("level"),
            "level_name": scan.get("levelName"),
            "pass": passed,
            "fail": failed,
            "neutral": neutral,
            "total": total,
            "percent": percent,
            "gaps": gaps,
            "is_commerce": bool(scan.get("isCommerce")),
        }