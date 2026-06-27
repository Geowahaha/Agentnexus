# DEV ONLY — local PostgreSQL + backend. Production uses VPS (see .production/PRODUCTION-RULES.md).
# Do not use this for obolla.com 24/7; run scripts/deploy-vps-production.ps1 instead.
param(
    [string]$RepoRoot = (Split-Path $PSScriptRoot -Parent)
)

$ErrorActionPreference = "Stop"
$PgCtl = "C:\Program Files\PostgreSQL\18\bin\pg_ctl.exe"
$PgData = "C:\Program Files\PostgreSQL\18\data"
$BackendDir = Join-Path $RepoRoot "backend"
$Python = Join-Path $BackendDir ".venv\Scripts\python.exe"

function Test-PortListening([int]$Port) {
    return [bool](Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue)
}

function Test-BackendHealth() {
    try {
        $r = Invoke-WebRequest -Uri "http://127.0.0.1:8000/docs" -UseBasicParsing -TimeoutSec 4
        return $r.StatusCode -ge 200 -and $r.StatusCode -lt 500
    } catch { return $false }
}

Write-Host "== OBOLLA local stack ==" -ForegroundColor Cyan

if (-not (Test-PortListening 5432)) {
    if (-not (Test-Path $PgCtl)) { throw "PostgreSQL not found at $PgCtl" }
    Write-Host "Starting PostgreSQL..." -ForegroundColor Yellow
    $logDir = Join-Path $PgData "log"
    New-Item -ItemType Directory -Force -Path $logDir | Out-Null
    $pgLog = Join-Path $logDir "agentnexus-start.log"
    & $PgCtl start -D $PgData -l $pgLog -w -t 90
    if (-not (Test-PortListening 5432)) { throw "PostgreSQL failed to start (see $pgLog)" }
    Write-Host "PostgreSQL: OK" -ForegroundColor Green
} else {
    Write-Host "PostgreSQL: already running" -ForegroundColor Green
}

if (-not (Test-BackendHealth)) {
    Write-Host "Starting backend..." -ForegroundColor Yellow
    if (-not (Test-Path $Python)) { throw "Backend venv missing: $Python" }
    Start-Process -FilePath "powershell.exe" -ArgumentList @(
        "-NoProfile", "-Command",
        "`$env:PYTHONPATH='$BackendDir'; Set-Location '$BackendDir'; & '$Python' run.py"
    ) -WindowStyle Hidden | Out-Null
    $deadline = (Get-Date).AddSeconds(45)
    while ((Get-Date) -lt $deadline) {
        if (Test-BackendHealth) { break }
        Start-Sleep -Seconds 1
    }
    if (-not (Test-BackendHealth)) { throw "Backend failed to start on :8000" }
    Write-Host "Backend: OK" -ForegroundColor Green
} else {
    Write-Host "Backend: already running" -ForegroundColor Green
}

$cf = Get-Command cloudflared -ErrorAction SilentlyContinue
if ($cf -and -not (Get-Process cloudflared -ErrorAction SilentlyContinue)) {
    $config = Join-Path $RepoRoot ".production\tunnel-config.yml"
    if (Test-Path $config) {
        Write-Host "Starting cloudflared tunnel..." -ForegroundColor Yellow
        Start-Process -FilePath $cf.Source -ArgumentList @("--no-autoupdate", "--config", $config, "run") -WindowStyle Hidden | Out-Null
        Start-Sleep -Seconds 3
    }
}
if (Get-Process cloudflared -ErrorAction SilentlyContinue) {
    Write-Host "Tunnel: running" -ForegroundColor Green
} else {
    Write-Host "Tunnel: not running (run scripts/setup-named-tunnel.ps1)" -ForegroundColor Yellow
}

try {
    $health = Invoke-RestMethod -Uri "https://obolla.com/health" -TimeoutSec 10
    $ok = $health.backend_reachable
    Write-Host "Edge health: backend_reachable=$ok" -ForegroundColor $(if ($ok) { "Green" } else { "Yellow" })
} catch {
    Write-Host "Edge health check failed: $_" -ForegroundColor Yellow
}

Write-Host "Done. iPhone create flow needs backend_reachable=true." -ForegroundColor Cyan