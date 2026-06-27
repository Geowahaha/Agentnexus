from __future__ import annotations

import asyncio
import base64
import json
import mimetypes
import os
from typing import Any

import httpx

try:
    import blake3 as _blake3
except ImportError:  # pragma: no cover
    _blake3 = None

CF_API = "https://api.cloudflare.com/client/v4"
PAGES_ASSETS = f"{CF_API}/pages/assets"


def _asset_hash(content: bytes, path: str) -> str:
    """Cloudflare Pages hash: blake3(base64(content) + ext) truncated to 32 hex chars."""
    if _blake3 is None:
        raise RuntimeError("blake3 package required for Cloudflare Pages direct upload")
    ext = ""
    if "." in path.rsplit("/", 1)[-1]:
        ext = path.rsplit(".", 1)[-1]
    payload = base64.b64encode(content).decode("ascii") + ext
    return _blake3.blake3(payload.encode("ascii")).hexdigest()[:32]


def _mime(path: str) -> str:
    guessed, _ = mimetypes.guess_type(path)
    return guessed or "application/octet-stream"


class CloudflarePagesDeployAdapter:
    """Direct Upload API for Cloudflare Pages (no Wrangler required on server)."""

    def __init__(
        self,
        *,
        api_token: str | None = None,
        account_id: str | None = None,
    ) -> None:
        self.api_token = (api_token or os.environ.get("CLOUDFLARE_API_TOKEN") or "").strip()
        self.account_id = (account_id or os.environ.get("CLOUDFLARE_ACCOUNT_ID") or "").strip()

    @property
    def configured(self) -> bool:
        return bool(self.api_token and self.account_id)

    def _api_headers(self) -> dict[str, str]:
        if not self.api_token:
            raise RuntimeError("CLOUDFLARE_API_TOKEN not configured")
        return {
            "Authorization": f"Bearer {self.api_token}",
            "Content-Type": "application/json",
        }

    async def _upload_token(self, project_name: str) -> str:
        async with httpx.AsyncClient(timeout=60.0) as client:
            res = await client.post(
                f"{CF_API}/accounts/{self.account_id}/pages/projects/{project_name}/upload-token",
                headers=self._api_headers(),
            )
            res.raise_for_status()
            payload = res.json()
            if not payload.get("success"):
                raise RuntimeError(f"upload-token failed: {payload.get('errors')}")
            return payload["result"]["jwt"]

    async def _check_missing(self, jwt: str, hashes: list[str]) -> list[str]:
        async with httpx.AsyncClient(timeout=60.0) as client:
            res = await client.post(
                f"{PAGES_ASSETS}/check-missing",
                headers={"Authorization": f"Bearer {jwt}", "Content-Type": "application/json"},
                json={"hashes": hashes},
            )
            res.raise_for_status()
            payload = res.json()
            return payload.get("result") or []

    async def _upload_batch(self, jwt: str, batch: list[dict[str, Any]]) -> None:
        async with httpx.AsyncClient(timeout=120.0) as client:
            res = await client.post(
                f"{PAGES_ASSETS}/upload",
                headers={"Authorization": f"Bearer {jwt}", "Content-Type": "application/json"},
                json=batch,
            )
            res.raise_for_status()
            payload = res.json()
            if not payload.get("success"):
                raise RuntimeError(f"assets/upload failed: {payload.get('errors')}")

    async def _upsert_hashes(self, jwt: str, hashes: list[str]) -> None:
        async with httpx.AsyncClient(timeout=60.0) as client:
            res = await client.post(
                f"{PAGES_ASSETS}/upsert-hashes",
                headers={"Authorization": f"Bearer {jwt}", "Content-Type": "application/json"},
                json={"hashes": hashes},
            )
            res.raise_for_status()

    async def _create_deployment(
        self,
        project_name: str,
        manifest: dict[str, str],
        *,
        branch: str = "main",
    ) -> dict[str, Any]:
        form = {
            "branch": branch,
            "manifest": json.dumps(manifest),
        }
        headers = {"Authorization": f"Bearer {self.api_token}"}
        async with httpx.AsyncClient(timeout=120.0) as client:
            res = await client.post(
                f"{CF_API}/accounts/{self.account_id}/pages/projects/{project_name}/deployments",
                headers=headers,
                data=form,
            )
            res.raise_for_status()
            payload = res.json()
            if not payload.get("success"):
                raise RuntimeError(f"deployment create failed: {payload.get('errors')}")
            return payload["result"]

    async def deploy_files(
        self,
        *,
        project_name: str,
        files: dict[str, str],
        branch: str = "main",
    ) -> dict[str, Any]:
        if not self.configured:
            raise RuntimeError("CLOUDFLARE_API_TOKEN and CLOUDFLARE_ACCOUNT_ID required")

        normalized: dict[str, bytes] = {}
        for path, text in files.items():
            key = path.lstrip("/")
            normalized[key] = text.encode("utf-8")

        hash_by_path: dict[str, str] = {
            path: _asset_hash(data, path) for path, data in normalized.items()
        }
        manifest = {f"/{path}": hash_by_path[path] for path in hash_by_path}

        jwt = await self._upload_token(project_name)
        all_hashes = list(hash_by_path.values())
        missing = await self._check_missing(jwt, all_hashes)

        if missing:
            upload_items = []
            hash_to_path = {v: k for k, v in hash_by_path.items()}
            for h in missing:
                path = hash_to_path.get(h)
                if not path:
                    continue
                content = normalized[path]
                upload_items.append(
                    {
                        "key": h,
                        "value": base64.b64encode(content).decode("ascii"),
                        "metadata": {"contentType": _mime(path)},
                        "base64": True,
                    }
                )
            chunk_size = 100
            for i in range(0, len(upload_items), chunk_size):
                await self._upload_batch(jwt, upload_items[i : i + chunk_size])
            await self._upsert_hashes(jwt, missing)

        deployment = await self._create_deployment(project_name, manifest, branch=branch)
        return {
            "project_name": project_name,
            "branch": branch,
            "files": len(files),
            "uploaded_hashes": len(missing),
            "deployment_id": deployment.get("id"),
            "url": deployment.get("url"),
            "environment": deployment.get("environment"),
        }

    async def wait_for_success(
        self,
        project_name: str,
        deployment_id: str,
        *,
        timeout_s: float = 180.0,
        poll_s: float = 4.0,
    ) -> dict[str, Any]:
        deadline = asyncio.get_event_loop().time() + timeout_s
        while asyncio.get_event_loop().time() < deadline:
            async with httpx.AsyncClient(timeout=30.0) as client:
                res = await client.get(
                    f"{CF_API}/accounts/{self.account_id}/pages/projects/{project_name}/deployments/{deployment_id}",
                    headers=self._api_headers(),
                )
                res.raise_for_status()
                dep = res.json()["result"]
            stage = dep.get("latest_stage") or {}
            status = stage.get("status")
            if status == "success":
                return dep
            if status in ("failure", "canceled"):
                raise RuntimeError(f"Pages deployment {status}: {deployment_id}")
            await asyncio.sleep(poll_s)
        raise TimeoutError(f"Pages deployment {deployment_id} timed out")