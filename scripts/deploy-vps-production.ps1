# Deploy AgentNexus backend to VPS, keep tunnel on VPS only, stop local PC stack.
# Production rule: anything blocking 24/7 features must run here — see .production/PRODUCTION-RULES.md
param(
    [string]$VpsHost = "43.128.75.149",
    [string]$VpsUser = "root",
    [string]$SshKey = "$env:USERPROFILE\.ssh\ssh-key-2026-03-21_Oracle_Geomonkey.key",
    [string]$BackendUrl = "https://agentnexus-api.obolla.com",
    [switch]$SkipBuild,
    [switch]$SkipBackendDeploy,
    [switch]$KeepLocalTunnel
)

$ErrorActionPreference = "Stop"
$RepoRoot = Split-Path $PSScriptRoot -Parent
$ProdDir = Join-Path $RepoRoot ".production"
$CredFile = Join-Path $ProdDir "tunnel-credentials.json"
$TunnelConfig = Join-Path $ProdDir "tunnel-config.yml"

if (-not (Test-Path $SshKey)) { throw "SSH key not found: $SshKey" }
if (-not (Test-Path $CredFile)) { throw "Missing tunnel credentials: $CredFile" }

$sshBase = @("-i", $SshKey, "-o", "BatchMode=yes", "-o", "StrictHostKeyChecking=accept-new")
$target = "${VpsUser}@${VpsHost}"

function Invoke-Vps([string]$Script) {
    ($Script -replace "`r`n", "`n" -replace "`r", "`n") | & ssh @sshBase $target "bash -s"
    if ($LASTEXITCODE -ne 0) { throw "VPS command failed" }
}

function Write-VpsFile([string]$RemotePath, [string]$Content) {
    ($Content -replace "`r`n", "`n" -replace "`r", "`n") | & ssh @sshBase $target "cat > $RemotePath"
    if ($LASTEXITCODE -ne 0) { throw "write $RemotePath failed" }
}

Write-Host "== OBOLLA VPS production (backend + tunnel) ==" -ForegroundColor Cyan
Write-Host "VPS: $VpsHost" -ForegroundColor White
Write-Host "API: $BackendUrl" -ForegroundColor White

Write-Host "`n[1/5] Sync tunnel config to VPS..." -ForegroundColor Cyan
& ssh @sshBase $target "mkdir -p /etc/cloudflared"
if ($LASTEXITCODE -ne 0) { throw "ssh mkdir failed" }
& scp @sshBase $CredFile "${target}:/etc/cloudflared/tunnel-credentials.json"
if ($LASTEXITCODE -ne 0) { throw "scp credentials failed" }

$vpsConfig = @"
tunnel: ca530862-141d-449e-9a9e-e1fb9f2eec2e
credentials-file: /etc/cloudflared/tunnel-credentials.json

ingress:
  - hostname: agentnexus-api.obolla.com
    service: http://127.0.0.1:8000
  - service: http_status:404
"@
Write-VpsFile "/etc/cloudflared/config.yml" $vpsConfig
& ssh @sshBase $target "chmod 600 /etc/cloudflared/tunnel-credentials.json"
if ($LASTEXITCODE -ne 0) { throw "chmod credentials failed" }

$serviceUnit = @'
[Unit]
Description=Cloudflare Tunnel for AgentNexus API
After=network-online.target docker.service
Wants=network-online.target

[Service]
Type=simple
ExecStart=/usr/bin/cloudflared --no-autoupdate tunnel --config /etc/cloudflared/config.yml run
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
'@
Write-VpsFile "/etc/systemd/system/cloudflared-agentnexus.service" $serviceUnit

Invoke-Vps @'
set -euo pipefail
if ! command -v cloudflared >/dev/null 2>&1; then
  curl -fsSL https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb -o /tmp/cloudflared.deb
  dpkg -i /tmp/cloudflared.deb || apt-get install -f -y
fi
systemctl daemon-reload
systemctl enable cloudflared-agentnexus
systemctl restart cloudflared-agentnexus
status=$(systemctl is-active cloudflared-agentnexus || true)
echo "tunnel: $status"
[ "$status" = "active" ] || exit 1
'@

if (-not $SkipBackendDeploy) {
    Write-Host "`n[2/5] Deploy backend (Docker)..." -ForegroundColor Cyan
    $deployArgs = @{}
    if ($SkipBuild) { $deployArgs.SkipBuild = $true }
    & (Join-Path $RepoRoot "scripts\deploy-backend-vps.ps1") @deployArgs
} else {
    Write-Host "`n[2/5] Skipping backend deploy" -ForegroundColor Yellow
}

Write-Host "`n[3/5] Ensure BACKEND_URL Worker secret..." -ForegroundColor Cyan
Set-Location $RepoRoot
$BackendUrl | npx wrangler secret put BACKEND_URL --env=""
if ($LASTEXITCODE -ne 0) { throw "wrangler secret put BACKEND_URL failed" }

if (-not $KeepLocalTunnel) {
    Write-Host "`n[4/5] Stop local PC tunnel + backend..." -ForegroundColor Cyan
    Get-Process cloudflared -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
    Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue |
        Select-Object -ExpandProperty OwningProcess -Unique |
        ForEach-Object { Stop-Process -Id $_ -Force -ErrorAction SilentlyContinue }
    Disable-ScheduledTask -TaskName "AgentNexus-NamedTunnel" -ErrorAction SilentlyContinue | Out-Null
    $localCf = (Get-Process cloudflared -ErrorAction SilentlyContinue | Measure-Object).Count
    $localApi = (Get-NetTCPConnection -LocalPort 8000 -State Listen -ErrorAction SilentlyContinue | Measure-Object).Count
    Write-Host "  local cloudflared: $localCf (want 0)" -ForegroundColor $(if ($localCf -eq 0) { "Green" } else { "Yellow" })
    Write-Host "  local :8000: $localApi (want 0)" -ForegroundColor $(if ($localApi -eq 0) { "Green" } else { "Yellow" })
} else {
    Write-Host "`n[4/5] Keeping local tunnel (--KeepLocalTunnel)" -ForegroundColor Yellow
}

Write-Host "`n[5/5] Smoke tests..." -ForegroundColor Cyan
$health = Invoke-RestMethod -Uri "https://obolla.com/health" -TimeoutSec 20
if (-not $health.backend_reachable) { throw "obolla.com/health backend_reachable=false" }
Write-Host "  /health: backend_reachable=true" -ForegroundColor Green

try {
    Invoke-WebRequest -Method POST -Uri "https://obolla.com/api/v1/creators/me/skills" `
        -ContentType "application/json" `
        -Body '{"name":"smoke","slug":"smoke","description":"smoke","price_usd_per_run":"0.30"}' `
        -UseBasicParsing | Out-Null
    throw "create skill smoke test: expected 401"
} catch {
    $body = $_.ErrorDetails.Message
    if ($body -notmatch "Not authenticated|detail|401") {
        throw "create skill smoke test failed: $($_.Exception.Message)"
    }
}
Write-Host "  POST /creators/me/skills: reachable (auth required)" -ForegroundColor Green

Write-Host ""
Write-Host "VPS production ready. Local PC no longer needed for API." -ForegroundColor Green
Write-Host "  Edge:    https://obolla.com" -ForegroundColor White
Write-Host "  API:     $BackendUrl/docs" -ForegroundColor White
Write-Host "  Redeploy: powershell -File scripts/deploy-vps-production.ps1" -ForegroundColor DarkGray