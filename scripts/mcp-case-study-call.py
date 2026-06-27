#!/usr/bin/env python3
"""Call OBOLLA MCP with fix_pack from case study file."""
import json
import sys
import urllib.request

CASE_FILE = r"D:\AgentNexus\Obolla cast study\MCP json to your ai after.txt"
MCP_URL = "https://obolla.com/mcp"


def extract_fix_pack(text: str) -> dict:
    marker = "fix_pack: {"
    start = text.index(marker) + len("fix_pack: ")
    end_marker = "\n\nTool definition (for reference):"
    chunk = text[start : text.index(end_marker)].strip()
    return json.loads(chunk)


def main() -> int:
    text = open(CASE_FILE, encoding="utf-8").read()
    fix_pack = extract_fix_pack(text)
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {
            "name": "apply_agent_ready_fix",
            "arguments": {
                "url": "obolla.com",
                "fix_pack": fix_pack,
            },
        },
    }
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        MCP_URL,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=120) as resp:
        body = json.loads(resp.read().decode("utf-8"))
    # Parse inner result text
    summary = {"mcp_http": resp.status, "jsonrpc": body}
    if body.get("result", {}).get("content"):
        inner = body["result"]["content"][0].get("text", "")
        try:
            summary["parsed"] = json.loads(inner)
        except json.JSONDecodeError:
            summary["parsed_text"] = inner[:2000]
    print(json.dumps(summary, indent=2, default=str))
    return 0


if __name__ == "__main__":
    sys.exit(main())