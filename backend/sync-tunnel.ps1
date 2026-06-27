# Start FastAPI + Cloudflare quick tunnel, then update Worker BACKEND_URL secret.
# Run from repo root: .\backend\sync-tunnel.ps1

param(
    [string]$Origin = "http://127.0.0.1:8000",
    [int]$BackendWaitSeconds = 20,
    [int]$TunnelWaitSeconds = 45
)

$ErrorActionPreference = "Stop"
$BackendDir = $PSScriptRoot
$RepoRoot = Split-Path $BackendDir -Parent

function Test-BackendHealth {
    param([string]$Url)
    try {
        $resp = Invoke-WebRequest -Uri "$Url/docs" -UseBasicParsing -TimeoutSec 3
        return $resp.StatusCode -ge 200 -and $resp.StatusCode -lt 500
    } catch {
        return $false
    }
}

function Get-ListenerOnPort {
    param([int]$Port)
    Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue |
        Select-Object -ExpandProperty OwningProcess -Unique
}

Write-Host "== AgentNexus backend tunnel sync ==" -ForegroundColor Cyan

if (-not (Test-BackendHealth $Origin)) {
    $existing = Get-ListenerOnPort 8000
    if ($existing) {
        Write-Host "Port 8000 in use (PID $existing) but health check failed - restarting..." -ForegroundColor Yellow
        $existing | ForEach-Object { Stop-Process -Id $_ -Force -ErrorAction SilentlyContinue }
        Start-Sleep -Seconds 2
    }

    Write-Host "Starting backend on $Origin ..." -ForegroundColor Cyan
    $backendJob = Start-Job -ScriptBlock {
        param($Dir)
        Set-Location $Dir
        $env:PYTHONPATH = $Dir
        & "$Dir\.venv\Scripts\python.exe" run.py
    } -ArgumentList $BackendDir

    $deadline = (Get-Date).AddSeconds($BackendWaitSeconds)
    while ((Get-Date) -lt $deadline) {
        if (Test-BackendHealth $Origin) {
            Write-Host "Backend is up." -ForegroundColor Green
            break
        }
        Start-Sleep -Seconds 1
    }
    if (-not (Test-BackendHealth $Origin)) {
        Receive-Job $backendJob -ErrorAction SilentlyContinue | Write-Host
        throw "Backend did not become healthy within ${BackendWaitSeconds}s"
    }
} else {
    Write-Host "Backend already healthy at $Origin" -ForegroundColor Green
}

$cloudflaredPath = $null
$cloudflaredCmd = Get-Command cloudflared -ErrorAction SilentlyContinue
if ($cloudflaredCmd) {
    $cloudflaredPath = $cloudflaredCmd.Source
} else {
    $fallback = "C:\Program Files (x86)\cloudflared\cloudflared.exe"
    if (Test-Path $fallback) { $cloudflaredPath = $fallback } else { throw "cloudflared not found in PATH" }
}

Write-Host "Starting Cloudflare quick tunnel -> $Origin" -ForegroundColor Cyan
$tunnelLog = Join-Path $env:TEMP "agentnexus-tunnel-$(Get-Date -Format 'yyyyMMddHHmmss').log"
$tunnelProc = Start-Process -FilePath $cloudflaredPath -ArgumentList @(
    "tunnel", "--url", $Origin, "--no-autoupdate"
) -RedirectStandardOutput $tunnelLog -PassThru -WindowStyle Hidden

$tunnelUrl = $null
$deadline = (Get-Date).AddSeconds($TunnelWaitSeconds)
while ((Get-Date) -lt $deadline) {
    if (Test-Path $tunnelLog) {
        $content = Get-Content $tunnelLog -Raw -ErrorAction SilentlyContinue
        if ($content -match '(https://[a-zA-Z0-9-]+\.trycloudflare\.com)') {
            $tunnelUrl = $Matches[1]
            break
        }
    }
    if ($tunnelProc.HasExited) { break }
    Start-Sleep -Milliseconds 500
}

if (-not $tunnelUrl) {
    if (Test-Path $tunnelLog) { Get-Content $tunnelLog | Write-Host }
    throw "Could not read trycloudflare.com URL within ${TunnelWaitSeconds}s"
}

Write-Host "Tunnel URL: $tunnelUrl" -ForegroundColor Green

Set-Location $RepoRoot
Write-Host "Updating Worker secret BACKEND_URL ..." -ForegroundColor Cyan
$tunnelUrl | npx wrangler secret put BACKEND_URL
if ($LASTEXITCODE -ne 0) { throw "wrangler secret put BACKEND_URL failed" }

Write-Host ""
Write-Host "Done. API proxy should work at:" -ForegroundColor Green
Write-Host "  https://agentnexus.mrgeo888.workers.dev/api/v1/auth/login" -ForegroundColor White
Write-Host ""
Write-Host "Keep this tunnel process running (PID $($tunnelProc.Id))." -ForegroundColor Yellow
Write-Host "Log: $tunnelLog" -ForegroundColor DarkGray