# Keep AgentNexus backend + Cloudflare tunnel running for production edge proxy.
param(
    [string]$RepoRoot = (Split-Path $PSScriptRoot -Parent),
    [string]$BackendUrl = "",
    [switch]$SkipSecretUpdate,
    [switch]$UseNamedTunnel
)

$ErrorActionPreference = "Stop"
$StateDir = Join-Path $RepoRoot ".production"
$StateFile = Join-Path $StateDir "stack.json"
New-Item -ItemType Directory -Force -Path $StateDir | Out-Null

function Test-BackendHealth([string]$Url = "http://127.0.0.1:8000") {
    try {
        $r = Invoke-WebRequest -Uri "$Url/docs" -UseBasicParsing -TimeoutSec 4
        return $r.StatusCode -ge 200 -and $r.StatusCode -lt 500
    } catch { return $false }
}

function Get-CloudflaredPath() {
    $cmd = Get-Command cloudflared -ErrorAction SilentlyContinue
    if ($cmd) { return $cmd.Source }
    $fallback = "C:\Program Files (x86)\cloudflared\cloudflared.exe"
    if (Test-Path $fallback) { return $fallback }
    throw "cloudflared not found"
}

Write-Host "== AgentNexus production stack ==" -ForegroundColor Cyan

$namedState = Join-Path $RepoRoot ".production\named-tunnel.json"
if ($UseNamedTunnel -or ((-not $BackendUrl) -and (Test-Path $namedState))) {
    Write-Host "Using named tunnel (run scripts/setup-named-tunnel.ps1 if not configured yet)..." -ForegroundColor Cyan
    $setupArgs = @{}
    if ($SkipSecretUpdate) { $setupArgs.SkipSecretUpdate = $true }
    & (Join-Path $RepoRoot "scripts\setup-named-tunnel.ps1") @setupArgs
    exit $LASTEXITCODE
}

if (-not (Test-BackendHealth)) {
    Write-Host "Starting backend..." -ForegroundColor Cyan
    $backendDir = Join-Path $RepoRoot "backend"
    $python = Join-Path $backendDir ".venv\Scripts\python.exe"
    $backendProc = Start-Process -FilePath "powershell.exe" `
        -ArgumentList @(
            "-NoProfile", "-Command",
            "`$env:PYTHONPATH='$backendDir'; Set-Location '$backendDir'; & '$python' run.py"
        ) -WindowStyle Hidden -PassThru
    $deadline = (Get-Date).AddSeconds(25)
    while ((Get-Date) -lt $deadline) {
        if (Test-BackendHealth) { break }
        Start-Sleep -Seconds 1
    }
    if (-not (Test-BackendHealth)) { throw "Backend failed to start" }
} else {
    $backendProc = $null
    Write-Host "Backend already running" -ForegroundColor Green
}

$tunnelUrl = $BackendUrl
if (-not $tunnelUrl) {
    $cf = Get-CloudflaredPath
    $tunnelLog = Join-Path $StateDir "tunnel.log"
    if (Test-Path $tunnelLog) { Remove-Item $tunnelLog -Force }
    $tunnelProc = Start-Process -FilePath "cmd.exe" -ArgumentList @(
        "/c", "`"$cf`" tunnel --url http://127.0.0.1:8000 --no-autoupdate > `"$tunnelLog`" 2>&1"
    ) -PassThru -WindowStyle Hidden
    $deadline = (Get-Date).AddSeconds(60)
    while ((Get-Date) -lt $deadline) {
        if (Test-Path $tunnelLog) {
            $content = Get-Content $tunnelLog -Raw -ErrorAction SilentlyContinue
            if ($content -and $content -match '(https://[a-zA-Z0-9-]+\.trycloudflare\.com)') {
                $tunnelUrl = $Matches[1]
                break
            }
        }
        if ($tunnelProc.HasExited) { break }
        Start-Sleep -Milliseconds 500
    }
    if (-not $tunnelUrl) { throw "Tunnel URL not found. See $tunnelLog" }
} else {
    $tunnelProc = $null
}

Write-Host "Tunnel: $tunnelUrl" -ForegroundColor Green

if (-not $SkipSecretUpdate) {
    Set-Location $RepoRoot
    $tunnelUrl | npx wrangler secret put BACKEND_URL --env=""
    if ($LASTEXITCODE -ne 0) { throw "Failed to update BACKEND_URL secret" }
}

$state = @{
    started_at = (Get-Date).ToUniversalTime().ToString("o")
    backend_pid = if ($backendProc) { $backendProc.Id } else { $null }
    tunnel_pid = if ($tunnelProc) { $tunnelProc.Id } else { $null }
    tunnel_url = $tunnelUrl
    worker_url = "https://agentnexus.mrgeo888.workers.dev"
}
$state | ConvertTo-Json | Set-Content $StateFile -Encoding UTF8

Write-Host "Stack state: $StateFile" -ForegroundColor DarkGray
Write-Host "Production edge: $($state.worker_url)" -ForegroundColor Green