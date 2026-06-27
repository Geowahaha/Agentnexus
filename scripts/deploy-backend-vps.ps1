# Deploy AgentNexus FastAPI backend to production VPS (Docker + migrations).
param(
    [string]$VpsHost = "43.128.75.149",
    [string]$VpsUser = "root",
    [string]$SshKey = "$env:USERPROFILE\.ssh\ssh-key-2026-03-21_Oracle_Geomonkey.key",
    [string]$RemoteDir = "/opt/agentnexus",
    [switch]$SkipBuild
)

$ErrorActionPreference = "Stop"
$RepoRoot = Split-Path $PSScriptRoot -Parent
$BackendDir = Join-Path $RepoRoot "backend"
$Archive = Join-Path $RepoRoot ".production\agentnexus-backend-deploy.tar.gz"

if (-not (Test-Path $SshKey)) { throw "SSH key not found: $SshKey" }

Write-Host "== Deploy backend to VPS $VpsHost ==" -ForegroundColor Cyan

Push-Location $BackendDir
try {
    if (Test-Path $Archive) { Remove-Item $Archive -Force }
    & tar -czf $Archive `
        --exclude=.venv `
        --exclude=__pycache__ `
        --exclude=.pytest_cache `
        --exclude="*.pyc" `
        .
} finally {
    Pop-Location
}

$sshBase = @("-i", $SshKey, "-o", "BatchMode=yes", "-o", "StrictHostKeyChecking=accept-new")
$target = "${VpsUser}@${VpsHost}"

Write-Host "Uploading backend archive..." -ForegroundColor Cyan
& scp @sshBase $Archive "${target}:/tmp/agentnexus-backend-deploy.tar.gz"
if ($LASTEXITCODE -ne 0) { throw "scp failed" }

$remoteScript = @'
set -euo pipefail
cd /opt/agentnexus
cp .env /tmp/agentnexus.env.bak
tar -xzf /tmp/agentnexus-backend-deploy.tar.gz -C /opt/agentnexus
cp /tmp/agentnexus.env.bak .env
mkdir -p mosquitto/certs agent-ready-sites
chmod +x scripts/setup-mqtt-tls-vps.sh mosquitto/docker-entrypoint.sh 2>/dev/null || true
bash scripts/setup-mqtt-tls-vps.sh || true
ufw allow 8883/tcp comment 'MQTT TLS Smart Farm' 2>/dev/null || true
docker volume create agentnexus_agentnexus_data 2>/dev/null || true
docker run --rm -v agentnexus_agentnexus_data:/farm-data alpine sh -c 'mkdir -p /farm-data/mosquitto && touch /farm-data/mosquitto/passwd /farm-data/mosquitto/acl' || true
docker-compose -f docker-compose.prod.yml down || true
docker rm -f agentnexus-api 2>/dev/null || true
if [ "$SKIP_BUILD" = "1" ]; then
  docker-compose -f docker-compose.prod.yml up -d
else
  docker-compose -f docker-compose.prod.yml up -d --build
fi
docker-compose -f docker-compose.prod.yml ps
docker exec agentnexus-api alembic current
for i in $(seq 1 45); do
  if curl -sf http://127.0.0.1:8000/docs >/dev/null; then
    echo "API healthy on VPS"
    exit 0
  fi
  sleep 2
done
echo "API health check timed out"
exit 1
'@

if ($SkipBuild) { $env:SKIP_BUILD = "1" } else { $env:SKIP_BUILD = "0" }
$remoteScript = $remoteScript -replace '\$SKIP_BUILD', $env:SKIP_BUILD

Write-Host "Extracting + rebuilding on VPS..." -ForegroundColor Cyan
$remoteScript | & ssh @sshBase $target "bash -s"
if ($LASTEXITCODE -ne 0) { throw "remote deploy failed" }

Write-Host "Verifying public API..." -ForegroundColor Cyan
try {
    $vision = Invoke-RestMethod -Uri "https://agentnexus-api.obolla.com/api/v1/community/vision" -TimeoutSec 30
    Write-Host "  community/vision: OK" -ForegroundColor Green
    Write-Host "  manifesto: $($vision.manifesto_th.Substring(0, [Math]::Min(60, $vision.manifesto_th.Length)))..." -ForegroundColor DarkGray
} catch {
    Write-Host "  community/vision check failed: $($_.Exception.Message)" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "Backend VPS deploy complete." -ForegroundColor Green
Write-Host "  API: https://agentnexus-api.obolla.com/docs" -ForegroundColor White
Write-Host "  Edge proxy: https://obolla.com/api/v1/*" -ForegroundColor White