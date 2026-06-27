# Local Agent Bridge — Design Document

**Status:** Phase 2 — workflow + write/execute integration
**Author:** AgentNexus  
**Date:** 2026-06-19

## Summary

Local Agent Bridge lets AgentNexus cloud act as the **brain** (planning, LLM, billing) while a small **Bridge app** on the user's machine acts as the **hands** (read files, list directories, later: shell, write, MCP stdio). Access is **opt-in only**: outbound WebSocket from the client, scoped device tokens, revocable pairing.

Inspired by Grok Remote Support / TeamViewer agent model — not full machine access.

## Goals (Phase 1 MVP)

- Pair a local machine via 6-digit code (5 min TTL)
- Maintain outbound WSS from Bridge → Cloudflare `BridgeHub` Durable Object
- Invoke `bridge.list_dir` and `bridge.read_file` on a connected device from the web UI
- List / revoke devices; audit log stub

## Non-Goals (Phase 1)

- Shell execution, file writes, MCP stdio proxy
- Native OS consent popup (web-based test invoke first)
- LangGraph workflow integration (Phase 2)

## Architecture

```
Browser (/bridge) ──REST──► FastAPI (pairing, devices, invoke)
                                │
                                └──HTTP──► CF Worker /internal/bridge/dispatch
                                              │
Bridge CLI ──WSS outbound──► BridgeHub DO ◄──┘
     │
     └── list_dir / read_file (cwd-scoped)
```

## Key Decisions

| Decision | Rationale |
|----------|-----------|
| Outbound WSS only | Firewall-friendly; no inbound tunnel to user machine |
| Device token (hashed in DB) | Simple auth; revocable per device |
| BridgeHub per `user_id` | Mirrors `NotificationHub`; one DO routes to N devices |
| Reuse `INTERNAL_NOTIFY_SECRET` | Same trust boundary as edge publish; header `X-Bridge-Secret` |
| Phase 1 tools: read-only | Minimize risk while proving the pipe works |
| Pairing code in PostgreSQL | Backend owns identity; Worker only routes |

## Wire Protocol (WebSocket)

**Device → Cloud**

```json
{ "type": "hello", "device_id": "uuid", "device_name": "George-PC" }
{ "type": "tool_result", "request_id": "uuid", "ok": true, "result": {} }
{ "type": "tool_result", "request_id": "uuid", "ok": false, "error": "message" }
{ "type": "pong" }
```

**Cloud → Device**

```json
{ "type": "welcome", "device_id": "uuid" }
{ "type": "tool_call", "request_id": "uuid", "tool": "list_dir", "args": { "path": "." } }
{ "type": "ping" }
```

## Security

- Default: **read-only** capabilities (`list_dir`, `read_file`)
- Paths resolved under `allowed_roots` (default: user home / cwd at pair time)
- `..` and symlink escape blocked in Bridge CLI
- Device revoke → token hash invalidated immediately
- All invokes logged in `bridge_audit_events`

## API (Phase 1)

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/bridge/pairing-codes` | User JWT | Create 6-digit code |
| POST | `/bridge/pair` | None | Exchange code → `device_token` |
| GET | `/bridge/devices` | User JWT | List devices |
| DELETE | `/bridge/devices/{id}` | User JWT | Revoke device |
| POST | `/bridge/devices/{id}/invoke` | User JWT | Test tool call |
| POST | `/bridge/device-session` | `X-Bridge-Secret` | Worker validates device token |

## PR Plan

### PR1 — Protocol + Worker BridgeHub ✅ (this sprint)
- `bridge-hub.ts`, `bridge-handlers.ts`, wrangler DO binding

### PR2 — Backend pairing + devices
- Migration `019_local_agent_bridge`
- `bridge_repository`, `bridge_service`, `/api/v1/bridge/*`

### PR3 — Bridge CLI
- `packages/bridge` — `npx agentnexus-bridge pair <code>`

### PR4 — Frontend `/bridge`
- Pairing UI, device list, test invoke

### PR5 — ToolResolver integration ✅ Phase 2
- `source: bridge` in `ToolResolver`
- Auto-inject `bridge.*` tools when `bridge_device_id` in workflow context
- Agent run UI device selector

### PR6 — Write/execute ✅ Phase 2 (terminal consent)
- `bridge.write_file`, `bridge.run_command`
- CLI prompts `[y/N]` per dangerous action
- `--allow-write` at pair time

### PR7 — Native tray + web consent queue (Phase 3)
- Tauri tray app, in-browser approve/deny for write/run