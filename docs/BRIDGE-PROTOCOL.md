# AgentNexus Bridge Protocol (Draft)

## Goal
Allow cloud-based agents (running on AgentNexus) to securely access and act on a user's local machine with explicit consent.

## Architecture
- **Edge Hub**: Cloudflare Durable Object (BridgeHub) manages live device connections.
- **Backend**: FastAPI validates devices/tokens and dispatches via edge.
- **Client**: Node.js (or tray) maintains persistent WS to edge, executes tools.
- **Consent**: For write/execute tools, approval via browser tab (WebSocket) or local terminal prompt.

## Connection
Client connects with device_token:
`ws://.../api/v1/bridge/ws?device_token=...`

Messages (JSON):

### Server → Client
- `welcome`
- `tool_call` { request_id, tool, args, pre_approved? }
- `ping`

### Client → Server
- `hello`
- `tool_result` { request_id, ok, result?, error? }
- `pong`

## Tools (current + proposed)

| Tool | Args | Consent | Description |
|------|------|---------|-------------|
| list_dir | { path } | No | List directory |
| read_file | { path } | No | Read file content |
| write_file | { path, content } | Yes | Write file |
| run_command | { command, cwd? } | Yes | Run shell command |
| search_files | { root?, query, max_results? } | No | Find files by name/content |
| get_file_info | { path } | No | Stat a path |

Future: 
- `search_in_files`
- `run_local_llm`
- `control_browser` (via local playwright if installed)

## Pairing
1. Web generates 6-digit code (stored in D1, 30min TTL).
2. Client calls POST /api/v1/bridge/pair with code.
3. Backend issues device_id + device_token.
4. Client saves token and connects.

## Security
- Token scoped to device.
- Allowed roots enforced client-side.
- Consent for dangerous actions.
- All cloud-to-device goes through authenticated edge.

## Spec Status
This is internal draft. Can be opened as public spec for third-party bridges.

Version: 0.2 (2026-06)