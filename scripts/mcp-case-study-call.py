#!/usr/bin/env python3
"""Call OBOLLA MCP with fix_pack from case study file."""
from __future__ import annotations

import json
import sys
import urllib.error
import urllib.request

DEFAULT_CASE_FILE = r"D:\AgentNexus\Obolla cast study\MCP json to your ai after2.txt"
MCP_URLS = (
    "https://obolla.com/api/v1/mcp",
    "https://obolla.com/mcp",
)


def extract_fix_pack(text: str) -> dict:
    marker = "fix_pack: {"
    start = text.index(marker) + len("fix_pack: ")
    end_marker = "\n\nTool definition (for reference):"
    chunk = text[start : text.index(end_marker)].strip()
    return json.loads(chunk)


def call_mcp(case_file: str) -> dict:
    text = open(case_file, encoding="utf-8").read()
    fix_pack = extract_fix_pack(text)
    url = fix_pack.get("url") or "https://obolla.com"
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {
            "name": "apply_agent_ready_fix",
            "arguments": {
                "url": url,
                "fix_pack": fix_pack,
            },
        },
    }
    data = json.dumps(payload).encode("utf-8")
    body: dict = {}
    status = 0
    used_url = MCP_URLS[0]
    last_err: str | None = None
    for mcp_url in MCP_URLS:
        req = urllib.request.Request(
            mcp_url,
            data=data,
            headers={
                "Content-Type": "application/json",
                "User-Agent": "OBOLLA-CaseStudy-MCP/1.0",
                "Accept": "application/json",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=120) as resp:
                body = json.loads(resp.read().decode("utf-8"))
                status = resp.status
                used_url = mcp_url
                break
        except urllib.error.HTTPError as exc:
            status = exc.code
            raw = exc.read().decode("utf-8", errors="replace")
            last_err = f"{mcp_url} HTTP {status}: {raw[:500]}"
            try:
                body = json.loads(raw)
            except json.JSONDecodeError:
                body = {"error": {"message": raw[:2000], "code": status}}
            if status not in (403, 502, 503):
                used_url = mcp_url
                break
        except Exception as exc:  # noqa: BLE001
            last_err = f"{mcp_url}: {exc}"

    summary: dict = {
        "case_file": case_file,
        "mcp_url": used_url,
        "last_error": last_err,
        "mcp_http": status,
        "file_count": len(fix_pack.get("files") or {}),
        "jsonrpc": body,
    }
    if body.get("result", {}).get("content"):
        inner = body["result"]["content"][0].get("text", "")
        try:
            summary["parsed"] = json.loads(inner)
        except json.JSONDecodeError:
            summary["parsed_text"] = inner[:4000]
    return summary


def main() -> int:
    case_file = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_CASE_FILE
    summary = call_mcp(case_file)
    print(json.dumps(summary, indent=2, default=str))
    if summary.get("jsonrpc", {}).get("error"):
        return 1
    parsed = summary.get("parsed") or {}
    if parsed.get("error") or parsed.get("detail"):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())