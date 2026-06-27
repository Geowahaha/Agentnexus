# Add a CNAME DNS record pointing a hostname to the AgentNexus named tunnel.
# Requires CLOUDFLARE_API_TOKEN with Zone:DNS:Edit (or DNS Write).
#
# Usage:
#   $env:CLOUDFLARE_API_TOKEN = "<token>"
#   powershell -File scripts/add-tunnel-hostname.ps1 -Hostname agentnexus-api.aibotauth.com -ZoneName aibotauth.com

param(
    [string]$Hostname = "agentnexus-api.aibotauth.com",
    [string]$ZoneName = "aibotauth.com",
    [string]$TunnelId = "ca530862-141d-449e-9a9e-e1fb9f2eec2e",
    [string]$ApiToken = ""
)

$ErrorActionPreference = "Stop"
if (-not $ApiToken) { $ApiToken = $env:CLOUDFLARE_API_TOKEN }
if (-not $ApiToken) {
    Write-Host "Missing API token. Create one at:" -ForegroundColor Yellow
    Write-Host "  https://dash.cloudflare.com/profile/api-tokens" -ForegroundColor White
    Write-Host "Permissions: Zone > DNS > Edit (zone: $ZoneName)" -ForegroundColor White
    Write-Host ""
    Write-Host "Or add manually in DNS dashboard:" -ForegroundColor Yellow
    Write-Host "  Type:    CNAME" -ForegroundColor White
    Write-Host "  Name:    agentnexus-api" -ForegroundColor White
    Write-Host "  Target:  $TunnelId.cfargotunnel.com" -ForegroundColor White
    Write-Host "  Proxy:   Enabled" -ForegroundColor White
    exit 1
}

$headers = @{
    Authorization = "Bearer $ApiToken"
    "Content-Type" = "application/json"
}

$zones = Invoke-RestMethod -Uri "https://api.cloudflare.com/client/v4/zones?name=$ZoneName" -Headers $headers
if (-not $zones.success) { throw ($zones.errors | ForEach-Object { $_.message }) -join "; " }
$zoneId = ($zones.result | Where-Object { $_.name -eq $ZoneName } | Select-Object -First 1).id
if (-not $zoneId) { throw "Zone not found: $ZoneName" }

$cnameTarget = "$TunnelId.cfargotunnel.com"
$recordName = if ($Hostname.EndsWith(".$ZoneName")) {
    $Hostname.Substring(0, $Hostname.Length - $ZoneName.Length - 1)
} else { $Hostname }

$dnsBase = "https://api.cloudflare.com/client/v4/zones/$zoneId/dns_records"
$existing = Invoke-RestMethod -Uri "$dnsBase?type=CNAME&name=$Hostname" -Headers $headers
$body = @{
    type = "CNAME"
    proxied = $true
    name = $recordName
    content = $cnameTarget
}

if ($existing.result -and $existing.result.Count -gt 0) {
    $recId = $existing.result[0].id
    $resp = Invoke-RestMethod -Uri "$dnsBase/$recId" -Headers $headers -Method PUT -Body ($body | ConvertTo-Json)
} else {
    $resp = Invoke-RestMethod -Uri $dnsBase -Headers $headers -Method POST -Body ($body | ConvertTo-Json)
}

if (-not $resp.success) { throw ($resp.errors | ForEach-Object { $_.message }) -join "; " }
Write-Host "DNS ready: https://$Hostname -> $cnameTarget" -ForegroundColor Green
Write-Host "Test: Invoke-WebRequest https://$Hostname/" -ForegroundColor Cyan