# Register a logon Scheduled Task to keep the named tunnel running (no admin required).
param(
    [string]$TaskName = "AgentNexus-NamedTunnel"
)

$RepoRoot = Split-Path $PSScriptRoot -Parent
$Config = Join-Path $RepoRoot ".production\tunnel-config.yml"
$Cf = (Get-Command cloudflared -ErrorAction SilentlyContinue).Source
if (-not $Cf) { $Cf = "C:\Program Files (x86)\cloudflared\cloudflared.exe" }
if (-not (Test-Path $Config)) {
    throw "Missing $Config. Run scripts/setup-named-tunnel.ps1 first."
}

$action = New-ScheduledTaskAction -Execute $Cf -Argument "--no-autoupdate --config `"$Config`" run"
$trigger = New-ScheduledTaskTrigger -AtLogOn -User $env:USERNAME
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable
Register-ScheduledTask -TaskName $TaskName -Action $action -Trigger $trigger -Settings $settings -Force | Out-Null
Write-Host "Scheduled task '$TaskName' registered (runs at logon)." -ForegroundColor Green