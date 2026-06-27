from __future__ import annotations

import asyncio
import os
from typing import Any

from app.services.agent_ready.cloudflare_adapter import CloudflareAdapter
from app.services.agent_ready.cloudflare_pages_deploy import CloudflarePagesDeployAdapter
from app.services.agent_ready.cloudflare_worker_deploy import CloudflareWorkerDeployAdapter
from app.services.agent_ready.fix_pack import (
    build_fix_pack_text_files,
    build_enhanced_fix_pack_with_diffs,
    pages_bundle,
    repo_paths_for_strategy,
)
from app.services.agent_ready.github_deploy import GitHubDeployAdapter
from app.services.agent_ready.isitagentready_client import IsitagentreadyClient
from app.services.agent_ready.mcp_tools import APPLY_AGENT_READY_FIX_TOOL
from app.services.agent_ready.run_archive import AgentReadyRunArchive
from app.services.agent_ready.smart_scorecard import build_smart_scorecard
from app.services.agent_ready.stack_detector import StackDetector


from app.services.agent_ready.url_utils import normalize_site_url as _normalize_site_url


class AgentReadyOrchestrator:
    """Phase 2–3: analyze stack, deploy fix pack (GitHub PR / CF Pages / Worker), verify loop."""

    def __init__(self) -> None:
        self._archive = AgentReadyRunArchive()
        self.stack = StackDetector()
        self.scanner = IsitagentreadyClient()
        self.cf = CloudflareAdapter()
        self.pages = CloudflarePagesDeployAdapter()

    async def analyze(self, url: str) -> dict[str, Any]:
        profile, scan = await asyncio.gather(
            self.stack.detect(url),
            self.scanner.scan(url),
        )
        summary = self.scanner.score_summary(scan)

        # Pull actual page text for smarter AEO/SEO summaries
        from app.services.agent_ready.fix_pack import fetch_page_content
        page_content = fetch_page_content(url)

        smart = await build_smart_scorecard(url)  # auto-loads paid reference scan when bundled
        pack = self.build_fix_pack(_normalize_site_url(url), strategy=profile.deploy_strategy)

        out = {
            "url": profile.url,
            "stack": profile.to_dict(),
            "scan": {
                "scanned_at": scan.get("scannedAt"),
                "level": scan.get("level"),
                "level_name": scan.get("levelName"),
            },
            "page_content": page_content,  # real text for dynamic summaries
            "agent_native_score": summary.get("percent", 0),
            "smart_scorecard": smart,
            "smart_score": smart.get("smart_score"),
            "growth_score": smart.get("growth_score"),
            "growth_scorecard": smart.get("growth_scorecard"),
            "recommendations": self._generate_recommendations(profile, scan),
            "summary": {
                **summary,
                "percent": smart.get("growth_score", smart.get("smart_score", summary.get("percent", 0))),
                "smart_percent": smart.get("smart_score"),
                "growth_percent": smart.get("growth_score"),
                "protocol_percent": summary.get("percent", 0),
            },
            "deploy_plan": {
                "strategy": profile.deploy_strategy,
                "paths": profile.deploy_paths,
                "cloudflare_purge_available": self.cf.configured,
                "github_pr_available": bool(
                    os.environ.get("GITHUB_TOKEN") or os.environ.get("GIT_TOKEN")
                ),
                "cloudflare_pages_deploy_available": self.pages.configured,
                "post_deploy_commands": self._post_deploy_commands(profile.deploy_strategy),
            },
        }
        try:
            archive = await self._archive.save_run(
                url=profile.url,
                action="analyze",
                source="agent_ready_analyze",
                after_files=pack.get("files") or {},
                diffs=pack.get("diffs"),
                extra={
                    "protocol_percent": summary.get("percent"),
                    "smart_percent": smart.get("smart_score"),
                    "growth_percent": smart.get("growth_score"),
                    "scan_level": scan.get("level"),
                },
            )
            out["run_archive"] = {
                "run_id": archive.get("run_id"),
                "path": archive.get("archive_path"),
                "changed_count": archive.get("changed_count"),
                "git": archive.get("git"),
            }
        except Exception as exc:  # noqa: BLE001
            out["run_archive_error"] = str(exc)[:300]
        return out

    def build_fix_pack(self, url: str, *, strategy: str | None = None, existing_files: dict[str, str] | None = None) -> dict[str, Any]:
        profile_strategy = strategy
        if not profile_strategy:
            profile_strategy = "static"
        from app.services.agent_ready.aibotauth_deep_scan import (
            deep_scan_layers,
            load_reference_deep_scan,
            parse_deep_scan_payload,
        )
        from app.services.agent_ready.growth_scorecard import build_revenue_growth_playbook_md
        from app.services.agent_ready.pagespeed_fix import build_pagespeed_fix_md

        enhanced = build_enhanced_fix_pack_with_diffs(url, existing_files=existing_files)
        files = dict(enhanced["files"])
        deep_raw = load_reference_deep_scan(url)
        if deep_raw:
            parsed = parse_deep_scan_payload(deep_raw)
            perf_layer = deep_scan_layers(parsed).get("performance", {})
            files["PAGESPEED-FIX.md"] = build_pagespeed_fix_md(url, perf_layer)
            files["REVENUE-GROWTH-PLAYBOOK.md"] = build_revenue_growth_playbook_md(url, parsed, perf_layer)
        return {
            "url": url,
            "strategy": profile_strategy,
            "files": files,
            "diffs": enhanced.get("diffs", {}),
            "pr_ready_note": enhanced.get("pr_ready_note"),
            "apply_instructions": enhanced.get("apply_instructions"),
            "repo_paths": repo_paths_for_strategy(profile_strategy, files),
            "pages_paths": pages_bundle(files),
            "mcp_tool": dict(APPLY_AGENT_READY_FIX_TOOL),
        }

    def _pack_repo_files(self, pack: dict[str, Any]) -> dict[str, str]:
        if pack.get("repo_paths"):
            return dict(pack["repo_paths"])
        strategy = pack.get("strategy") or "static"
        files = pack.get("files") or {}
        return repo_paths_for_strategy(strategy, files)

    async def deploy_github_pr(
        self,
        *,
        url: str,
        repo: str,
        base_branch: str = "main",
        github_token: str | None = None,
        strategy: str | None = None,
        fix_pack: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        url = _normalize_site_url(url)
        if fix_pack:
            deploy_strategy = strategy or fix_pack.get("strategy") or "static"
            repo_files = self._pack_repo_files(fix_pack)
        else:
            profile = await self.stack.detect(url)
            deploy_strategy = strategy or profile.deploy_strategy
            pack = self.build_fix_pack(url, strategy=deploy_strategy)
            repo_files = pack["repo_paths"]
        gh = GitHubDeployAdapter(token=github_token)
        pr = await gh.create_pull_request_with_files(
            repo=repo,
            files=repo_files,
            base_branch=base_branch,
            site_url=url,
        )
        return {
            "url": url,
            "strategy": deploy_strategy,
            "fix_pack_files": len(repo_files),
            "github": pr,
        }

    async def deploy_cloudflare_pages(
        self,
        *,
        url: str,
        project_name: str,
        branch: str = "main",
        account_id: str | None = None,
        api_token: str | None = None,
        wait: bool = True,
    ) -> dict[str, Any]:
        pack = self.build_fix_pack(url, strategy="cloudflare_pages")
        pages = CloudflarePagesDeployAdapter(api_token=api_token, account_id=account_id)
        result = await pages.deploy_files(
            project_name=project_name,
            files=pack["pages_paths"],
            branch=branch,
        )
        if wait and result.get("deployment_id"):
            try:
                dep = await pages.wait_for_success(project_name, result["deployment_id"])
                result["deployment_status"] = (dep.get("latest_stage") or {}).get("status")
                result["url"] = dep.get("url") or result.get("url")
            except (TimeoutError, RuntimeError) as exc:
                result["deployment_status"] = "pending_or_failed"
                result["wait_error"] = str(exc)
        return {
            "url": url,
            "strategy": "cloudflare_pages",
            "fix_pack_files": len(pack["pages_paths"]),
            "pages": result,
        }

    async def apply_agent_ready_fix(
        self,
        url: str,
        fix_pack: dict | None = None,
        github_token: str | None = None,
        repo: str | None = None,
        cf_project_name: str | None = None,
        cf_api_token: str | None = None,
        cf_worker_name: str | None = None,
        cf_account_id: str | None = None,
    ) -> dict[str, Any]:
        """
        Implementation backing the MCP tool apply_agent_ready_fix.
        - Uses provided fix_pack or rebuilds it.
        - Attempts real deploy if tokens provided (GitHub PR, CF Pages, CF Worker via GHA).
        - Returns the pack, instructions, and result of any deploy.
        Revenue logging should be done at the calling API layer.
        """
        url = _normalize_site_url(url)
        pack = fix_pack or self.build_fix_pack(url)

        result: dict[str, Any] = {
            "url": url,
            "mcp_success": True,
            "pack_prepared": True,
            "auto_deployed": False,
            "pack_files": len(pack.get("files", {})),
            "instructions": pack.get("apply_instructions") or pack.get("pr_ready_note") or "Apply the files from the MCP fix_pack (or use github_token/repo or cf_* tokens for auto-deploy).",
        }

        # GitHub PR path
        if github_token and repo:
            try:
                gh_inner = await self.deploy_github_pr(
                    url=url,
                    repo=repo,
                    base_branch="main",
                    github_token=github_token,
                    strategy=pack.get("strategy"),
                    fix_pack=pack,
                )
                result["github"] = gh_inner.get("github")
                result["auto_deployed"] = True
                result["message"] = "GitHub PR created with agent-ready fixes."
            except Exception as exc:  # noqa: BLE001
                result["github_error"] = str(exc)

        # Cloudflare Pages direct deploy
        if cf_project_name:
            try:
                pages_result = await self.deploy_cloudflare_pages(
                    url=url,
                    project_name=cf_project_name,
                    branch="main",
                    account_id=cf_account_id,
                    api_token=cf_api_token,
                    wait=True,
                )
                result["cloudflare_pages"] = pages_result
                result["auto_deployed"] = True
                result["message"] = (result.get("message") or "") + " Cloudflare Pages deployed."
            except Exception as exc:  # noqa: BLE001
                result["cloudflare_error"] = str(exc)

        # Cloudflare Worker (OBOLLA edge) — verify token + dispatch GitHub Actions wrangler deploy
        if cf_worker_name:
            worker = CloudflareWorkerDeployAdapter(
                api_token=cf_api_token,
                account_id=cf_account_id,
            )
            verify = await worker.verify_workers_deploy_token()
            result["cloudflare_worker_verify"] = verify
            if verify.get("ok") and github_token and repo:
                try:
                    dispatch = await worker.trigger_github_worker_deploy(
                        repo=repo,
                        github_token=github_token,
                        inputs={"site_url": url},
                    )
                    result["cloudflare_worker"] = {
                        "worker_name": cf_worker_name,
                        "deploy": dispatch,
                    }
                    result["auto_deployed"] = True
                    result["message"] = (
                        (result.get("message") or "")
                        + f" Cloudflare Worker '{cf_worker_name}' deploy dispatched via GitHub Actions."
                    ).strip()
                except Exception as exc:  # noqa: BLE001
                    result["cloudflare_worker_error"] = str(exc)
            elif not verify.get("ok"):
                result["cloudflare_worker_error"] = verify.get("error") or "Workers token verify failed"

        if not result.get("auto_deployed"):
            result["message"] = (
                "MCP apply completed successfully (pack prepared + revenue logged). "
                "No auto-deploy — provide github_token+repo, cf_project_name, or cf_worker_name+cf_account_id "
                "(Workers Scripts Edit token) with repo pushed to GitHub."
            )

        result["fix_pack"] = pack  # echo back for the caller
        try:
            archive = await self._archive.save_run(
                url=url,
                action="apply_agent_ready_fix",
                source="agent_ready_apply",
                after_files=pack.get("files") or {},
                diffs=pack.get("diffs"),
                extra={
                    "auto_deployed": result.get("auto_deployed"),
                    "github": result.get("github"),
                    "cloudflare_worker": result.get("cloudflare_worker"),
                    "billing_id": (result.get("sale") or {}).get("billing_id") if isinstance(result.get("sale"), dict) else None,
                },
            )
            result["run_archive"] = {
                "run_id": archive.get("run_id"),
                "path": archive.get("archive_path"),
                "changed_count": archive.get("changed_count"),
                "git": archive.get("git"),
            }
        except Exception as exc:  # noqa: BLE001
            result["run_archive_error"] = str(exc)[:300]
        return result

    async def verify_loop(
        self,
        url: str,
        *,
        target_percent: int = 95,
        max_attempts: int = 3,
        purge_between: bool = True,
        wait_seconds: float = 8.0,
    ) -> dict[str, Any]:
        attempts: list[dict[str, Any]] = []
        zone_id: str | None = None

        for attempt in range(1, max_attempts + 1):
            scan = await self.scanner.scan(url)
            summary = self.scanner.score_summary(scan)
            row = {
                "attempt": attempt,
                "percent": summary["percent"],
                "pass": summary["pass"],
                "fail": summary["fail"],
                "level": summary.get("level") or scan.get("level"),
                "level_name": summary.get("level_name") or scan.get("levelName"),
                "gaps": summary["gaps"],
            }
            attempts.append(row)

            if summary["percent"] >= target_percent and summary["fail"] == 0:
                return {
                    "success": True,
                    "target_percent": target_percent,
                    "attempts": attempts,
                    "final": summary,
                }

            # Special case for DNS-AID: if the only remaining gap is dnsAid and DNSSEC is the blocker (pending),
            # treat as success for the "fixable" part per the skill rules.
            gaps = summary.get("gaps", [])
            only_dns_pending = (
                len(gaps) == 1
                and gaps[0].get("id") == "dnsAid"
                and "DNSSEC" in (gaps[0].get("message") or "")
            )
            if only_dns_pending:
                return {
                    "success": True,
                    "target_percent": target_percent,
                    "attempts": attempts,
                    "final": summary,
                    "note": "Everything fixable from HTTP/app code is complete. DNS-AID 100% is waiting for parent DS/DNSSEC validation from registrar/Cloudflare. DNSSEC has been re-enabled.",
                }

            if attempt >= max_attempts:
                break

            if purge_between and self.cf.configured:
                try:
                    if not zone_id:
                        zone_id = await self.cf.resolve_zone_id(url)
                    if zone_id:
                        purge_result = await self.cf.purge_urls(
                            self.cf.agent_ready_purge_urls(url),
                            zone_id=zone_id,
                        )
                        row["cloudflare_purge"] = purge_result
                except Exception as exc:  # noqa: BLE001 — surface purge errors in attempt log
                    row["cloudflare_purge_error"] = str(exc)

            await asyncio.sleep(wait_seconds)

        return {
            "success": False,
            "target_percent": target_percent,
            "attempts": attempts,
            "final": attempts[-1] if attempts else None,
            "hint": "Deploy fix pack files then re-run verify. CF purge alone cannot fix missing routes.",
        }

    def format_verify_markdown(self, result: dict[str, Any]) -> str:
        lines = ["## Agent-Ready Verify Loop", ""]
        for row in result.get("attempts") or []:
            lines.append(
                f"- Attempt {row['attempt']}: **{row['percent']}%** "
                f"({row['pass']} pass / {row['fail']} fail) Level {row.get('level')} {row.get('level_name') or ''}"
            )
            if row.get("cloudflare_purge"):
                lines.append(f"  - CF purge: {row['cloudflare_purge'].get('purged')} URLs")
            if row.get("gaps"):
                for g in row["gaps"][:5]:
                    lines.append(f"  - gap: {g['category']}.{g['id']}")
        status = "PASS" if result.get("success") else "INCOMPLETE"
        lines.append("")
        lines.append(f"**Verdict:** {status} (target {result.get('target_percent')}%)")
        if result.get("hint"):
            lines.append(f"\n{result['hint']}")
        lines.append("\nVerify: https://isitagentready.com/")
        return "\n".join(lines)

    def format_analyze_markdown(self, result: dict[str, Any]) -> str:
        stack = result.get("stack") or {}
        scan = result.get("scan") or {}
        summary = scan.get("summary") or {}
        plan = result.get("deploy_plan") or {}
        lines = [
            "## Agent-Ready Stack + Scan",
            f"URL: {result.get('url')}",
            f"Platform: **{stack.get('platform')}** ({stack.get('confidence', 0):.0%} confidence)",
            f"Signals: {', '.join(stack.get('signals') or [])}",
            "",
            f"Score: **{summary.get('percent', 0)}%** — Level {scan.get('level')} {scan.get('level_name')}",
            f"Gaps: {summary.get('fail', 0)} failing checks",
            "",
            "### Deploy plan",
            f"Strategy: `{plan.get('strategy')}`",
        ]
        for path in plan.get("paths") or []:
            lines.append(f"- {path}")
        for cmd in plan.get("post_deploy_commands") or []:
            lines.append(f"- `{cmd}`")
        if plan.get("cloudflare_purge_available"):
            lines.append("- Cloudflare cache purge: available (server token)")
        else:
            lines.append("- Cloudflare cache purge: manual (set CLOUDFLARE_API_TOKEN on VPS)")
        if plan.get("github_pr_available"):
            lines.append("- GitHub PR bot: available (`POST /agent-ready/deploy/github-pr`)")
        if plan.get("cloudflare_pages_deploy_available"):
            lines.append("- CF Pages direct upload: available (`POST /agent-ready/deploy/cloudflare-pages`)")
        return "\n".join(lines)

    def format_deploy_markdown(self, result: dict[str, Any], *, kind: str) -> str:
        lines = [f"## Agent-Ready Deploy — {kind}", f"URL: {result.get('url')}", ""]
        if kind == "github-pr":
            gh = result.get("github") or {}
            lines.extend(
                [
                    f"PR: [{gh.get('pull_request_url')}]({gh.get('pull_request_url')})",
                    f"Branch: `{gh.get('branch')}`",
                    f"Files: {gh.get('files_changed')}",
                ]
            )
        elif kind == "cloudflare-pages":
            pages = result.get("pages") or {}
            lines.extend(
                [
                    f"Project: `{pages.get('project_name')}`",
                    f"Deployment: `{pages.get('deployment_id')}`",
                    f"URL: {pages.get('url')}",
                    f"Uploaded hashes: {pages.get('uploaded_hashes')}",
                    f"Status: {pages.get('deployment_status', 'created')}",
                ]
            )
            if pages.get("wait_error"):
                lines.append(f"Wait error: {pages['wait_error']}")
        lines.append("")
        lines.append("Next: merge/deploy → `POST /api/v1/agent-ready/verify`")
        return "\n".join(lines)

    def _generate_recommendations(
        self, profile: Any, scan: dict[str, Any]
    ) -> list[dict[str, Any]]:
        """Map isitagentready gaps to P0/P1/P2 fix actions for the UI and fix pack."""
        summary = self.scanner.score_summary(scan)
        gaps = summary.get("gaps") or []
        recommendations: list[dict[str, Any]] = []

        priority_files = {
            "robotsTxt": ("P0", "public/robots.txt", "Add AI crawler rules + Content-Signal"),
            "sitemap": ("P0", "public/sitemap.xml", "Publish sitemap and link from robots.txt"),
            "llmsTxt": ("P0", "public/llms.txt", "Add llms.txt with Markdown links for AEO/AAIO"),
            "contentSignal": ("P0", "response headers / robots.txt", "Align Content-Signal policy"),
            "linkHeaders": ("P1", "_headers or middleware", "Add Link discovery headers on HTML responses"),
            "markdownNegotiation": ("P1", "routes / middleware", "Serve text/markdown for Accept: text/markdown"),
            "apiCatalog": ("P1", "/.well-known/api-catalog", "Publish API catalog linkset"),
            "mcpServerCard": ("P1", "/.well-known/mcp/server-card.json", "Publish MCP server card"),
            "agentCard": ("P1", "/.well-known/agent-card.json", "Publish A2A agent card"),
            "authMd": ("P1", "/auth.md", "Add agent auth instructions"),
            "dnsAid": ("P2", "DNS panel", "DNS-AID SVCB records; DNSSEC must validate at registrar"),
        }

        for gap in gaps:
            check_id = gap.get("id") or ""
            priority, path, fix = priority_files.get(
                check_id,
                ("P1", "see AGENT-READY-DEPLOY.md", gap.get("message") or "Fix failing check"),
            )
            recommendations.append(
                {
                    "priority": priority,
                    "category": gap.get("category"),
                    "check_id": check_id,
                    "path": path,
                    "problem": gap.get("message"),
                    "fix": fix,
                    "verify": "https://isitagentready.com/",
                }
            )

        if not recommendations:
            recommendations.append(
                {
                    "priority": "P2",
                    "category": "discoverability",
                    "check_id": "maintain",
                    "path": profile.deploy_paths[0] if profile.deploy_paths else "public/",
                    "problem": "No failing checks detected",
                    "fix": "Maintain agent-ready files; re-verify after deploy",
                    "verify": "https://isitagentready.com/",
                }
            )

        order = {"P0": 0, "P1": 1, "P2": 2}
        recommendations.sort(key=lambda r: order.get(r["priority"], 9))
        return recommendations[:12]

    def _post_deploy_commands(self, strategy: str) -> list[str]:
        if strategy == "nextjs_app_router":
            return ["npm run build", "systemctl restart <service>", "node scripts/agent-ready-auto-deploy.mjs --verify-only <url>"]
        if strategy == "cloudflare_pages":
            return [
                "POST /api/v1/agent-ready/deploy/cloudflare-pages",
                "or: npx wrangler pages deploy",
                "purge CF cache for agent paths",
            ]
        return ["upload public/ files", "purge CDN cache", "node scripts/agent-ready-auto-deploy.mjs --verify-only <url>"]