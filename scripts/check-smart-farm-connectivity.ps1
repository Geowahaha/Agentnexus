# Diagnose Smart Farm connectivity: HTTP edge vs direct MQTT port on Tencent VPS.
param(
    [string]$VpsHost = "43.128.75.149",
    [string]$EdgeUrl = "https://obolla.com",
    [string]$DeviceKey = $env:SMART_FARM_DEVICE_KEY
)

$ErrorActionPreference = "Continue"
Write-Host "== Smart Farm connectivity check ==" -ForegroundColor Cyan
Write-Host "VPS: $VpsHost (Tencent CVM)" -ForegroundColor DarkGray
Write-Host ""

function Test-TcpPort([string]$HostName, [int]$Port) {
    try {
        $r = Test-NetConnection -ComputerName $HostName -Port $Port -WarningAction SilentlyContinue
        [pscustomobject]@{ Target = "${HostName}:${Port}"; Open = [bool]$r.TcpTestSucceeded }
    } catch {
        [pscustomobject]@{ Target = "${HostName}:${Port}"; Open = $false }
    }
}

$rows = @(
    Test-TcpPort $VpsHost 443
    Test-TcpPort $VpsHost 8883
)
$rows | Format-Table -AutoSize

Write-Host "Edge health..." -ForegroundColor Cyan
try {
    $health = Invoke-RestMethod -Uri "$EdgeUrl/health" -TimeoutSec 15
    Write-Host "  backend_reachable: $($health.backend_reachable)" -ForegroundColor $(if ($health.backend_reachable) { "Green" } else { "Red" })
} catch {
    Write-Host "  FAILED: $_" -ForegroundColor Red
}

Write-Host "HTTP ingest path (recommended)..." -ForegroundColor Cyan
try {
    $schema = Invoke-RestMethod -Uri "$EdgeUrl/api/v1/smart-farm/schema/japanese-melon" -TimeoutSec 15
    Write-Host "  schema OK — $($schema.channels.Count) channels" -ForegroundColor Green
} catch {
    Write-Host "  schema FAILED: $_" -ForegroundColor Red
}

if ($DeviceKey) {
    $body = @{
        readings = @(
            @{ channel = "temp_day_c"; value = 26.5 }
            @{ channel = "humidity_pct"; value = 60 }
        )
    } | ConvertTo-Json -Depth 5
    $headers = @{ "X-Device-Key" = $DeviceKey; "Content-Type" = "application/json" }
    try {
        $ingest = Invoke-RestMethod -Method Post -Uri "$EdgeUrl/api/v1/smart-farm/ingest" -Headers $headers -Body $body -TimeoutSec 20
        Write-Host "  ingest OK — $($ingest.readings_ingested) readings" -ForegroundColor Green
    } catch {
        Write-Host "  ingest FAILED: $_" -ForegroundColor Red
    }
} else {
    Write-Host "  skip ingest (set SMART_FARM_DEVICE_KEY)" -ForegroundColor Yellow
}

$mqttOpen = ($rows | Where-Object { $_.Target -like "*:8883" }).Open
Write-Host ""
if (-not $mqttOpen) {
    Write-Host "MQTT direct (8883): BLOCKED at cloud edge (Tencent Security Group likely)" -ForegroundColor Yellow
    Write-Host "  Fix: Tencent Console -> CVM -> Security Group -> Inbound TCP 8883" -ForegroundColor Yellow
    Write-Host "  Or use HTTP ingest via $EdgeUrl (port 443) — no SG change needed" -ForegroundColor Green
} else {
    Write-Host "MQTT direct (8883): reachable — mqtts://${VpsHost}:8883 can work for IoT" -ForegroundColor Green
}