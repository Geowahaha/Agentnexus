# Fix www.obolla.com for Cloudflare Workers apex (AAAA 100::).
# 1) Ensure www DNS matches apex (AAAA 100::, proxied)
# 2) Add 301 redirect www -> apex if Workers custom domain cannot be attached via API

param(
    [switch]$RedirectOnly
)

$ErrorActionPreference = "Stop"
$ZoneName = "obolla.com"
$ApexHost = "obolla.com"

if (-not $env:CLOUDFLARE_API_TOKEN) {
    $cfCandidates = @(
        "D:\successcasting.com\.env.cf.txt",
        "D:\successcasting.com\.env.cf",
        "D:\AgentNexus\.dev.vars"
    )
    foreach ($path in $cfCandidates) {
        if (-not (Test-Path $path)) { continue }
        foreach ($line in Get-Content $path) {
            if ($line -match '^\s*(CLOUDFLARE_API_TOKEN|CF_API_TOKEN)\s*=\s*(.+)\s*$') {
                $env:CLOUDFLARE_API_TOKEN = $Matches[2].Trim().Trim('"')
            }
        }
        if ($env:CLOUDFLARE_API_TOKEN) { break }
    }
}

if (-not $env:CLOUDFLARE_API_TOKEN) {
    throw "CLOUDFLARE_API_TOKEN not set."
}

$headers = @{
    Authorization = "Bearer $($env:CLOUDFLARE_API_TOKEN)"
    "Content-Type" = "application/json"
}

$zones = Invoke-RestMethod -Uri "https://api.cloudflare.com/client/v4/zones?name=$ZoneName" -Headers $headers
if (-not $zones.success -or $zones.result.Count -eq 0) {
    throw "Zone not found: $ZoneName"
}
$zoneId = $zones.result[0].id
Write-Host "Zone $ZoneName : $zoneId"

function Remove-DnsRecord([object]$Record) {
    if (-not $Record) { return }
    $null = Invoke-RestMethod -Method DELETE `
        -Uri "https://api.cloudflare.com/client/v4/zones/$zoneId/dns_records/$($Record.id)" `
        -Headers $headers
    Write-Host "Removed $($Record.type) $($Record.name)"
}

function Ensure-WwwAaaa() {
    $dns = Invoke-RestMethod -Uri "https://api.cloudflare.com/client/v4/zones/$zoneId/dns_records?per_page=100" -Headers $headers
    $www = $dns.result | Where-Object { $_.name -eq "www.$ZoneName" } | Select-Object -First 1
    if ($www -and $www.type -eq "AAAA" -and $www.content -eq "100::" -and $www.proxied) {
        Write-Host "www DNS already AAAA 100:: (proxied)"
        return
    }
    Remove-DnsRecord $www
    $body = @{
        type = "AAAA"
        name = "www"
        content = "100::"
        proxied = $true
        ttl = 1
    } | ConvertTo-Json
    $created = Invoke-RestMethod -Method POST `
        -Uri "https://api.cloudflare.com/client/v4/zones/$zoneId/dns_records" `
        -Headers $headers -Body $body
    if (-not $created.success) {
        throw "Failed to create www AAAA: $($created.errors | ConvertTo-Json -Compress)"
    }
    Write-Host "Created AAAA www.$ZoneName -> 100:: (proxied)"
}

function Ensure-WwwRedirect() {
    $phase = "http_request_dynamic_redirect"
    $entryUri = "https://api.cloudflare.com/client/v4/zones/$zoneId/rulesets/phases/$phase/entrypoint"
    try {
        $entry = Invoke-RestMethod -Uri $entryUri -Headers $headers
    } catch {
        Write-Host "Redirect ruleset API unavailable ($($_.Exception.Message)); skip redirect."
        return
    }

    $targetHost = "www.$ZoneName"
    $rules = @($entry.result.rules)
    $existing = $rules | Where-Object {
        $_.expression -match [regex]::Escape($targetHost)
    } | Select-Object -First 1
    if ($existing) {
        Write-Host "Redirect rule for $targetHost already exists"
        return
    }

    $newRule = @{
        expression = "(http.host eq `"$targetHost`")"
        description = "Redirect www.obolla.com to apex"
        action = "redirect"
        action_parameters = @{
            from_value = @{
                status_code = 301
                preserve_query_string = $true
                target_url = @{
                    expression = "concat(`"https://$ApexHost`", http.request.uri.path)"
                }
            }
        }
    }

    if ($entry.result.id) {
        $rules += $newRule
        $body = @{ rules = $rules } | ConvertTo-Json -Depth 12
        $updated = Invoke-RestMethod -Method PUT -Uri "https://api.cloudflare.com/client/v4/zones/$zoneId/rulesets/$($entry.result.id)" `
            -Headers $headers -Body $body
        if (-not $updated.success) {
            throw "Redirect ruleset update failed"
        }
        Write-Host "Added 301 redirect $targetHost -> https://$ApexHost"
        return
    }

    $body = @{
        rules = @($newRule)
    } | ConvertTo-Json -Depth 12
    $created = Invoke-RestMethod -Method PUT -Uri $entryUri -Headers $headers -Body $body
    if (-not $created.success) {
        throw "Redirect ruleset create failed: $($created.errors | ConvertTo-Json -Compress)"
    }
    Write-Host "Created redirect ruleset: www -> apex"
}

if (-not $RedirectOnly) {
    Ensure-WwwAaaa
}
Ensure-WwwRedirect
Write-Host "Done. Test: https://www.$ZoneName/"