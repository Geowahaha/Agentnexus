# AgentNexus Local Bridge

Connect your PC to [AgentNexus](https://agentnexus.mrgeo888.workers.dev) so cloud agents can read/write files and run commands with your consent.

## Install

```bash
cd packages/bridge
npm install
```

## Pair (one time)

1. Open https://agentnexus.mrgeo888.workers.dev/bridge
2. Generate a pairing code
3. Run:

```bash
node index.mjs pair 482913 --name "My-PC" --allow-write
```

## Connect (keep running)

```bash
node index.mjs connect
```

Default API: `https://agentnexus.mrgeo888.workers.dev`

## Windows tray (auto-start at logon)

```powershell
powershell -ExecutionPolicy Bypass -File ..\bridge-tray\install-windows.ps1
```

## Consent (Phase 3)

| Action | Web (logged in) | Terminal | Tray |
|--------|-----------------|----------|------|
| `list_dir` / `read_file` | auto | auto | auto |
| `write_file` / `run_command` | Approve in browser popup | `[y/N]` prompt | `[y/N]` prompt |

Keep a browser tab open on AgentNexus while agents run for fastest web approvals.

## Commands

| Command | Description |
|---------|-------------|
| `pair <CODE>` | Exchange 6-digit code for device token |
| `connect` | Outbound WebSocket to cloud |
| `status` | Show paired device config |