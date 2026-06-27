# Full production deploy: edge (Worker+SPA) + optional backend stack + smoke tests.
param(
    [switch]$StartStack,
    [string]$BackendUrl = "",
    [switch]$SkipSmoke
)

$ErrorActionPreference = "Stop"
$RepoRoot = Split-Path $PSScriptRoot -Parent
Set-Location $RepoRoot

Write-Host "== AgentNexus production deploy ==" -ForegroundColor Cyan

Write-Host "Deploying OBOLLA edge (Worker + SPA)..." -ForegroundColor Cyan
$obollaArgs = @()
if ($SkipSmoke) { $obollaArgs += "-SkipSmoke" }
& (Join-Path $PSScriptRoot "deploy-obolla.ps1") @obollaArgs
if ($LASTEXITCODE -ne 0) { throw "deploy-obolla.ps1 failed" }

if ($StartStack) {
    & (Join-Path $PSScriptRoot "start-production-stack.ps1") -RepoRoot $RepoRoot -BackendUrl $BackendUrl
} elseif ($BackendUrl) {
    Write-Host "Updating BACKEND_URL secret..." -ForegroundColor Cyan
    $BackendUrl | npx wrangler secret put BACKEND_URL --env=""
    if ($LASTEXITCODE -ne 0) { throw "BACKEND_URL secret update failed" }
}

if (-not $SkipSmoke) {
    Write-Host "Smoke tests..." -ForegroundColor Cyan
    $health = Invoke-RestMethod -Uri "https://agentnexus.mrgeo888.workers.dev/health"
    Write-Host ("  /health status: {0} backend_reachable={1}" -f $health.status, $health.backend_reachable)
    try {
        Invoke-RestMethod -Method POST -Uri "https://agentnexus.mrgeo888.workers.dev/api/v1/auth/login" `
            -ContentType "application/json" -Body '{"email":"smoke@test.com","password":"wrong"}' `
            -SkipHttpErrorCheck | Out-Null
        Write-Host "  /api/v1/auth/login: reachable (JSON response)" -ForegroundColor Green
    } catch {
        if ($_.ErrorDetails.Message -match "detail") {
            Write-Host "  /api/v1/auth/login: reachable (JSON response)" -ForegroundColor Green
        } else {
            throw "API smoke test failed: $($_.Exception.Message)"
        }
    }
}

Write-Host ""
Write-Host "Deployed: https://agentnexus.mrgeo888.workers.dev" -ForegroundColor Green
Write-Host "Bridge UI:  https://agentnexus.mrgeo888.workers.dev/bridge" -ForegroundColor Green
Write-Host ""
Write-Host "Next on user PC:" -ForegroundColor Yellow
Write-Host "  cd packages/bridge && npm install" -ForegroundColor White
Write-Host "  node index.mjs pair <CODE> --allow-write" -ForegroundColor White
Write-Host "  node index.mjs connect" -ForegroundColor White
Write-Host "  (or) powershell packages/bridge-tray/install-windows.ps1" -ForegroundColor White