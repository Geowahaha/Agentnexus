# Install AgentNexus Bridge to start at Windows logon (system tray + connect).
param(
    [string]$ApiBase = "https://agentnexus.mrgeo888.workers.dev"
)

$ErrorActionPreference = "Stop"
$TrayDir = $PSScriptRoot
$BridgeDir = Join-Path (Split-Path $TrayDir -Parent) "bridge"
$TaskName = "AgentNexusBridge"

if (-not (Test-Path (Join-Path $BridgeDir "index.mjs"))) {
    throw "Bridge CLI not found at $BridgeDir"
}

$action = New-ScheduledTaskAction -Execute "powershell.exe" -Argument `
    "-NoProfile -ExecutionPolicy Bypass -File `"$(Join-Path $TrayDir 'tray.ps1')`" -ApiBase `"$ApiBase`""
$trigger = New-ScheduledTaskTrigger -AtLogOn
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable
Register-ScheduledTask -TaskName $TaskName -Action $action -Trigger $trigger -Settings $settings -Force | Out-Null

Write-Host "Installed scheduled task: $TaskName" -ForegroundColor Green
Write-Host "Bridge tray will start at next logon." -ForegroundColor Cyan
Write-Host "Start now: powershell -File `"$(Join-Path $TrayDir 'tray.ps1')`"" -ForegroundColor Yellow