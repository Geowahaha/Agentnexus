$ErrorActionPreference = 'Stop'
$RepoRoot = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$BridgeDir = Join-Path $RepoRoot 'packages\bridge'
$ApiBase = 'https://obolla.com'

$existing = Get-CimInstance Win32_Process -Filter "Name='node.exe'" -ErrorAction SilentlyContinue |
  Where-Object { $_.CommandLine -match 'index\.mjs connect' -and $_.CommandLine -match 'agentnexus|bridge' }

if ($existing) {
  Write-Host "Bridge connect already running (PID $($existing.ProcessId))"
  exit 0
}

Start-Process -FilePath 'node' -ArgumentList "index.mjs connect --api `"$ApiBase`"" `
  -WorkingDirectory $BridgeDir -WindowStyle Hidden
Write-Host "Started George-PC bridge connect -> $ApiBase"