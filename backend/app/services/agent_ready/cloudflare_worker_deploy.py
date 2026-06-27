from __future__ import annotations

import os
from typing import Any

import httpx

CF_API = "https://api.cloudflare.com/client/v4"


class CloudflareWorkerDeployAdapter:
    """Workers Scripts API + GitHub Actions dispatch for OBOLLA edge deploy."""

    def __init__(self, *, api_token: str | None = None, account_id: str | None = None) -> None:
        self.api_token = (api_token or os.environ.get("CLOUDFLARE_API_TOKEN") or "").strip()
        self.account_id = (account_id or os.environ.get("CLOUDFLARE_ACCOUNT_ID") or "").strip()

    def _headers(self) -> dict[str, str]:
        if not self.api_token:
            raise RuntimeError("CLOUDFLARE_API_TOKEN not configured")
        return {"Authorization": f"Bearer {self.api_token}", "Content-Type": "application/json"}

    async def verify_workers_deploy_token(self) -> dict[str, Any]:
        if not self.account_id:
            return {"ok": False, "error": "cf_account_id required"}
        async with httpx.AsyncClient(timeout=30.0) as client:
            res = await client.get(
                f"{CF_API}/accounts/{self.account_id}/workers/scripts",
                headers=self._headers(),
            )
            if res.status_code == 403:
                return {
                    "ok": False,
                    "error": "Token lacks Workers Scripts permission (need Workers Scripts Edit)",
                }
            if res.status_code >= 400:
                return {"ok": False, "error": f"HTTP {res.status_code}: {res.text[:300]}"}
            data = res.json()
            scripts = data.get("result") or []
            return {"ok": bool(data.get("success")), "scripts_count": len(scripts)}

    async def trigger_github_worker_deploy(
        self,
        *,
        repo: str,
        github_token: str,
        workflow_file: str = "deploy-obolla.yml",
        ref: str = "main",
        inputs: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        from app.services.agent_ready.github_deploy import GitHubDeployAdapter

        owner, name = GitHubDeployAdapter.parse_repo(repo)
        async with httpx.AsyncClient(timeout=60.0) as client:
            res = await client.post(
                f"https://api.github.com/repos/{owner}/{name}/actions/workflows/{workflow_file}/dispatches",
                headers={
                    "Authorization": f"Bearer {github_token}",
                    "Accept": "application/vnd.github+json",
                    "X-GitHub-Api-Version": "2022-11-28",
                },
                json={"ref": ref, "inputs": inputs or {}},
            )
            if res.status_code == 204:
                return {
                    "repo": f"{owner}/{name}",
                    "workflow": workflow_file,
                    "ref": ref,
                    "status": "dispatched",
                }
            raise RuntimeError(f"GitHub workflow dispatch failed: {res.status_code} {res.text[:500]}")