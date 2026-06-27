# AgentNexus Bridge Tray (Phase 3+)

Windows system-tray companion for Local Agent Bridge.

## Features (Current)
- Runs `agentnexus-bridge connect` in the background
- Tray icon with online/disconnected status
- Open AgentNexus `/bridge` from context menu
- Auto-restart connect if the process exits
- Optional logon scheduled task
- Supports expanded tools: search_files, get_file_info, browse_page (stub), run_local_llm (stub), execute_in_app (stub)

## Coming Soon
- Browser control (Playwright/Puppeteer integration)
- Local LLM (Ollama/llama.cpp)
- App-specific automation (VSCode, Excel, etc.)

Web consent (approve write/run in browser) works when you keep AgentNexus open in a tab.

## Install (Windows)

```powershell
powershell -ExecutionPolicy Bypass -File install-windows.ps1
```

Starts at next logon. To run now:

```powershell
powershell -ExecutionPolicy Bypass -File tray.ps1
```

## Manual connect (all platforms)

```bash
cd ../bridge
npm install
node index.mjs connect
```