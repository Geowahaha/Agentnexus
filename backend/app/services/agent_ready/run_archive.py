from __future__ import annotations

import json
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from app.services.agent_ready.fix_pack import generate_diff_for_file
from app.services.agent_ready.live_snapshot import fetch_live_discovery_files, host_slug


def resolve_archive_root() -> Path:
    explicit = (os.environ.get("AGENT_READY_ARCHIVE_ROOT") or "").strip()
    if not explicit:
        try:
            from app.core.config import settings

            explicit = (settings.agent_ready_archive_root or "").strip()
        except Exception:  # noqa: BLE001
            explicit = ""
    if explicit:
        return Path(explicit)
    for candidate in (
        Path(__file__).resolve().parents[4] / "agent-ready-sites",
        Path("/app/agent-ready-sites"),
        Path.cwd() / "agent-ready-sites",
    ):
        if candidate.parent.exists():
            return candidate
    return Path("agent-ready-sites")


def _safe_write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _find_git_root(start: Path) -> Path | None:
    p = start.resolve()
    for _ in range(8):
        if (p / ".git").is_dir():
            return p
        if p.parent == p:
            break
        p = p.parent
    return None


def _classify_change(before: str | None, after: str) -> str:
    if not before:
        return "added"
    if before.strip() == after.strip():
        return "unchanged"
    return "modified"


def _build_changelog(changes: list[dict[str, Any]], site_url: str, action: str) -> str:
    lines = [
        f"# Agent-Ready change log — {site_url}",
        "",
        f"- **Action:** {action}",
        f"- **Recorded:** {datetime.now(timezone.utc).isoformat()}",
        "",
        "## Files",
        "",
    ]
    for c in changes:
        icon = {"added": "+", "modified": "~", "unchanged": "="}.get(c["change"], "?")
        lines.append(f"- [{icon}] `{c['path']}` — {c['change']}: {c.get('summary', '')}")
    lines.extend(["", "## Deploy / proof", "", "_See RUN.json for deploy and revenue metadata._", ""])
    return "\n".join(lines)


class AgentReadyRunArchive:
    """Per-site before[]/after[] boxes + optional git commit."""

    def __init__(self, root: Path | None = None) -> None:
        self.root = root or resolve_archive_root()

    def site_dir(self, url: str) -> Path:
        return self.root / host_slug(url)

    async def save_run(
        self,
        *,
        url: str,
        action: str,
        source: str,
        after_files: dict[str, str],
        before_files: dict[str, str] | None = None,
        diffs: dict[str, str] | None = None,
        extra: dict[str, Any] | None = None,
        fetch_before_if_missing: bool = True,
    ) -> dict[str, Any]:
        site_url = url if url.startswith("http") else f"https://{url.lstrip('/')}"
        host = host_slug(site_url)
        now = datetime.now(timezone.utc)
        run_suffix = (extra or {}).get("billing_id") or (extra or {}).get("run_id") or now.strftime("%H%M%S")
        run_id = f"{now.strftime('%Y%m%dT%H%M%SZ')}_{str(run_suffix)[:8]}"
        run_dir = self.site_dir(site_url) / "runs" / run_id
        before_dir = run_dir / "before"
        after_dir = run_dir / "after"
        diffs_dir = run_dir / "diffs"

        before = dict(before_files or {})
        before_meta: dict[str, Any] = {"source": "provided"}
        if fetch_before_if_missing and not before:
            snap = await fetch_live_discovery_files(site_url)
            before = snap.get("files") or {}
            before_meta = snap.get("meta") or {}

        all_paths = sorted(set(before.keys()) | set(after_files.keys()))
        changes: list[dict[str, Any]] = []
        for rel_path in all_paths:
            b = before.get(rel_path)
            a = after_files.get(rel_path)
            if a is None:
                continue
            change = _classify_change(b, a)
            if b is not None:
                _safe_write(before_dir / rel_path, b)
            _safe_write(after_dir / rel_path, a)
            diff_text = (diffs or {}).get(rel_path)
            if not diff_text:
                diff_text = generate_diff_for_file(rel_path, a, b or "")
            _safe_write(diffs_dir / f"{rel_path}.diff", diff_text)
            summary = ""
            if change == "added":
                summary = "new agent-ready file proposed"
            elif change == "modified":
                summary = f"~{abs(len(a) - len(b or ''))} chars vs live"
            else:
                summary = "no content change vs live"
            changes.append({"path": rel_path, "change": change, "summary": summary})

        run_record: dict[str, Any] = {
            "run_id": run_id,
            "site_url": site_url,
            "host": host,
            "action": action,
            "source": source,
            "recorded_at": now.isoformat(),
            "before": {
                "file_count": len(before),
                "meta": before_meta,
            },
            "after": {"file_count": len(after_files)},
            "changes": changes,
            "changed_count": sum(1 for c in changes if c["change"] != "unchanged"),
            "added_count": sum(1 for c in changes if c["change"] == "added"),
            "modified_count": sum(1 for c in changes if c["change"] == "modified"),
            "archive_path": str(run_dir.relative_to(self.root)).replace("\\", "/") if run_dir.is_relative_to(self.root) else str(run_dir),
        }
        if extra:
            run_record["result"] = extra

        _safe_write(run_dir / "RUN.json", json.dumps(run_record, indent=2, ensure_ascii=False))
        _safe_write(run_dir / "CHANGELOG.md", _build_changelog(changes, site_url, action))

        site_index = {
            "host": host,
            "site_url": site_url,
            "last_run_id": run_id,
            "last_recorded_at": now.isoformat(),
            "total_runs": len(list((self.site_dir(site_url) / "runs").glob("*/RUN.json"))) if (self.site_dir(site_url) / "runs").exists() else 1,
            "last_changed_files": run_record["changed_count"],
        }
        _safe_write(self.site_dir(site_url) / "SITE.json", json.dumps(site_index, indent=2))

        git_result = self.try_git_commit(run_dir, host, run_id, run_record["changed_count"])
        run_record["git"] = git_result
        _safe_write(run_dir / "RUN.json", json.dumps(run_record, indent=2, ensure_ascii=False))

        return run_record

    def try_git_commit(self, run_dir: Path, host: str, run_id: str, changed: int) -> dict[str, Any]:
        if os.environ.get("AGENT_READY_ARCHIVE_GIT", "1").strip().lower() in ("0", "false", "no"):
            return {"committed": False, "reason": "AGENT_READY_ARCHIVE_GIT disabled"}
        git_root = _find_git_root(self.root)
        if not git_root:
            return {"committed": False, "reason": "no git repo near archive root"}
        try:
            rel_run = run_dir.relative_to(git_root).as_posix()
            rel_site = (self.root / host / "SITE.json").relative_to(git_root).as_posix()
        except ValueError:
            return {"committed": False, "reason": "archive outside git repo"}
        msg = f"agent-ready: {host} run {run_id} ({changed} files changed)"
        try:
            subprocess.run(
                ["git", "add", rel_run, rel_site],
                cwd=git_root,
                check=True,
                capture_output=True,
                text=True,
                timeout=30,
            )
            commit = subprocess.run(
                ["git", "commit", "-m", msg],
                cwd=git_root,
                capture_output=True,
                text=True,
                timeout=30,
            )
            if commit.returncode == 0:
                sha = subprocess.check_output(
                    ["git", "rev-parse", "HEAD"], cwd=git_root, text=True
                ).strip()
                result: dict[str, Any] = {"committed": True, "commit": sha[:12], "message": msg}
                if os.environ.get("AGENT_READY_ARCHIVE_GIT_PUSH", "").strip().lower() in ("1", "true", "yes"):
                    push = subprocess.run(
                        ["git", "push"],
                        cwd=git_root,
                        capture_output=True,
                        text=True,
                        timeout=60,
                    )
                    result["pushed"] = push.returncode == 0
                    if push.returncode != 0:
                        result["push_error"] = (push.stderr or push.stdout or "")[:300]
                return result
            if "nothing to commit" in (commit.stdout or "") + (commit.stderr or ""):
                return {"committed": False, "reason": "nothing to commit"}
            return {"committed": False, "reason": (commit.stderr or commit.stdout or "")[:300]}
        except Exception as exc:  # noqa: BLE001
            return {"committed": False, "reason": str(exc)[:300]}

    def list_sites(self) -> list[dict[str, Any]]:
        if not self.root.is_dir():
            return []
        out: list[dict[str, Any]] = []
        for site_json in self.root.glob("*/SITE.json"):
            try:
                out.append(json.loads(site_json.read_text(encoding="utf-8")))
            except Exception:  # noqa: BLE001
                continue
        return sorted(out, key=lambda s: s.get("last_recorded_at") or "", reverse=True)

    def list_runs(self, url: str, *, limit: int = 20) -> list[dict[str, Any]]:
        runs_dir = self.site_dir(url) / "runs"
        if not runs_dir.is_dir():
            return []
        out: list[dict[str, Any]] = []
        for run_json in sorted(runs_dir.glob("*/RUN.json"), reverse=True)[:limit]:
            try:
                out.append(json.loads(run_json.read_text(encoding="utf-8")))
            except Exception:  # noqa: BLE001
                continue
        return out

    def get_run(self, url: str, run_id: str) -> dict[str, Any] | None:
        run_json = self.site_dir(url) / "runs" / run_id / "RUN.json"
        if not run_json.is_file():
            return None
        try:
            return json.loads(run_json.read_text(encoding="utf-8"))
        except Exception:  # noqa: BLE001
            return None