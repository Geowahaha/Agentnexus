# List registered gateway IPs for Tencent Security Group (MQTT 8883 whitelist).
param(
    [string]$Token = $env:OBOLLA_TOKEN,
    [string]$BaseUrl = "https://obolla.com/api/v1/smart-farm"
)

if (-not $Token) {
    Write-Host "Set OBOLLA_TOKEN (Bearer JWT) or pass -Token" -ForegroundColor Yellow
    exit 1
}

$headers = @{ Authorization = "Bearer $Token" }
$manifest = Invoke-RestMethod -Uri "$BaseUrl/mqtt-whitelist" -Headers $headers -TimeoutSec 30

Write-Host "== MQTT whitelist for Tencent SG ==" -ForegroundColor Cyan
Write-Host "VPS: $($manifest.vps_host):$($manifest.mqtt_tls_port)"
Write-Host $manifest.tencent_sg_note
Write-Host ""
Write-Host "Unique IPs to allow (TCP 8883 inbound):" -ForegroundColor Green
$manifest.unique_ips | ForEach-Object { Write-Host "  $_" }
Write-Host ""
Write-Host "By farm:" -ForegroundColor Cyan
$manifest.gateway_ips | Format-Table ip, label, farm_name, organization_name -AutoSize