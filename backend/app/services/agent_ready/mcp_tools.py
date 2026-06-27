"""Shared MCP tool definitions for agent-ready apply (OBOLLA + fix pack metadata)."""

from __future__ import annotations

from typing import Any

APPLY_AGENT_READY_FIX_TOOL: dict[str, Any] = {
    "name": "apply_agent_ready_fix",
    "description": (
        "Securely apply the generated agent-ready fix pack (full SEO + AEO + AAIO) "
        "without needing local Bridge. Pass scoped tokens for PR/deploy. "
        "Revenue is auto-logged to OBOLLA moat on success."
    ),
    "inputSchema": {
        "type": "object",
        "properties": {
            "url": {"type": "string"},
            "fix_pack": {"type": "object"},
            "github_token": {
                "type": ["string", "null"],
                "description": "For GitHub PR apply",
            },
            "repo": {
                "type": ["string", "null"],
                "description": "GitHub owner/repo (required if using github_token)",
            },
            "cf_project_name": {"type": ["string", "null"]},
            "cf_api_token": {"type": ["string", "null"]},
            "cf_worker_name": {
                "type": ["string", "null"],
                "description": "Cloudflare Worker script name (e.g. agentnexus). Triggers GHA deploy when repo+github_token provided.",
            },
            "cf_account_id": {
                "type": ["string", "null"],
                "description": "Cloudflare account id for Workers API verify",
            },
        },
        "required": ["url", "fix_pack"],
    },
}