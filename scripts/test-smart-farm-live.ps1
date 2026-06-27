# Live smoke test: Smart Farm HTTP ingest + schema + health
param(
    [string]$DeviceKey = $env:SMART_FARM_DEVICE_KEY,
    [string]$BaseUrl = "https://obolla.com/api/v1/smart-farm"
)

$ErrorActionPreference = "Stop"

Write-Host "== Smart Farm live test ==" -ForegroundColor Cyan

$schema = Invoke-RestMethod -Uri "$BaseUrl/schema/japanese-melon" -TimeoutSec 30
Write-Host "Schema channels: $($schema.channels.Count)" -ForegroundColor Green

if (-not $DeviceKey) {
    Write-Host "Skip ingest (set SMART_FARM_DEVICE_KEY or -DeviceKey)" -ForegroundColor Yellow
    exit 0
}

$body = @{
    readings = @(
        @{ channel = "temp_day_c"; value = 27.8; unit = "celsius" },
        @{ channel = "humidity_pct"; value = 62 },
        @{ channel = "uv_index"; value = 3.9 }
    )
    growth_stage = "fruiting"
    harvest_cycle_day = 41
} | ConvertTo-Json -Depth 5

$headers = @{ "X-Device-Key" = $DeviceKey; "Content-Type" = "application/json" }
$ingest = Invoke-RestMethod -Method Post -Uri "$BaseUrl/ingest" -Headers $headers -Body $body -TimeoutSec 30
Write-Host "Ingest OK: $($ingest.readings_ingested) readings, farm=$($ingest.farm_id)" -ForegroundColor Green

$health = Invoke-RestMethod -Uri "https://obolla.com/health" -TimeoutSec 15
if (-not $health.backend_reachable) { throw "backend not reachable" }
Write-Host "Health: backend_reachable=$($health.backend_reachable)" -ForegroundColor Green