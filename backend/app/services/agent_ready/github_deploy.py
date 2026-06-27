from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import Any

import httpx

GITHUB_API = "https://api.github.com"


class GitHubDeployAdapter:
    """Create a branch + PR with agent-ready fix pack files."""

    def __init__(self, token: str | None = None) -> None:
        self.token = (
            token or os.environ.get("GITHUB_TOKEN") or os.environ.get("GIT_TOKEN") or ""
        ).strip()
        if not self.token:
            raise RuntimeError("GITHUB_TOKEN not configured")

    @property
    def configured(self) -> bool:
        return bool(self.token)

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }

    async def _request(
        self,
        method: str,
        path: str,
        *,
        json: dict | None = None,
    ) -> Any:
        async with httpx.AsyncClient(timeout=90.0) as client:
            res = await client.request(method, f"{GITHUB_API}{path}", headers=self._headers(), json=json)
            if res.status_code >= 400:
                raise RuntimeError(f"GitHub API {method} {path}: {res.status_code} {res.text[:500]}")
            if not res.content:
                return {}
            return res.json()

    @staticmethod
    def parse_repo(repo: str) -> tuple[str, str]:
        cleaned = repo.strip().removeprefix("https://github.com/").strip("/")
        if "/" not in cleaned:
            raise ValueError("repo must be owner/name")
        owner, name = cleaned.split("/", 1)
        return owner, name

    async def create_pull_request_with_files(
        self,
        *,
        repo: str,
        files: dict[str, str],
        base_branch: str = "main",
        site_url: str,
        title: str | None = None,
    ) -> dict[str, Any]:
        owner, name = self.parse_repo(repo)
        base_ref = await self._request("GET", f"/repos/{owner}/{name}/git/ref/heads/{base_branch}")
        base_sha = base_ref["object"]["sha"]
        base_commit = await self._request("GET", f"/repos/{owner}/{name}/git/commits/{base_sha}")
        base_tree_sha = base_commit["tree"]["sha"]

        tree_entries = []
        for path, content in sorted(files.items()):
            blob = await self._request(
                "POST",
                f"/repos/{owner}/{name}/git/blobs",
                json={"content": content, "encoding": "utf-8"},
            )
            tree_entries.append(
                {
                    "path": path,
                    "mode": "100644",
                    "type": "blob",
                    "sha": blob["sha"],
                }
            )

        new_tree = await self._request(
            "POST",
            f"/repos/{owner}/{name}/git/trees",
            json={"base_tree": base_tree_sha, "tree": tree_entries},
        )
        branch_slug = datetime.now(timezone.utc).strftime("agent-ready/%Y%m%d-%H%M%S")
        commit_msg = f"feat(agent-ready): isitagentready fix pack for {site_url}"
        commit = await self._request(
            "POST",
            f"/repos/{owner}/{name}/git/commits",
            json={
                "message": commit_msg,
                "tree": new_tree["sha"],
                "parents": [base_sha],
            },
        )

        await self._request(
            "POST",
            f"/repos/{owner}/{name}/git/refs",
            json={"ref": f"refs/heads/{branch_slug}", "sha": commit["sha"]},
        )

        pr_title = title or f"Agent-Ready: isitagentready fix pack ({site_url})"
        pr_body = (
            f"Automated agent-ready fix pack from [OBOLLA](https://obolla.com).\n\n"
            f"- Target site: {site_url}\n"
            f"- Files: {len(files)}\n"
            f"- Reference: [successcasting.com 100% Level 5](https://www.successcasting.com)\n\n"
            "After merge, purge CDN cache and run verify:\n"
            f"`POST https://obolla.com/api/v1/agent-ready/verify` with `{{\"url\":\"{site_url}\"}}`"
        )
        pr = await self._request(
            "POST",
            f"/repos/{owner}/{name}/pulls",
            json={
                "title": pr_title,
                "head": branch_slug,
                "base": base_branch,
                "body": pr_body,
            },
        )
        return {
            "repo": f"{owner}/{name}",
            "branch": branch_slug,
            "commit_sha": commit["sha"],
            "pull_request_number": pr["number"],
            "pull_request_url": pr["html_url"],
            "files_changed": len(files),
        }