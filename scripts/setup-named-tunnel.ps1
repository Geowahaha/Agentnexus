# Create a permanent Cloudflare Named Tunnel for the local FastAPI backend.
# Prerequisite (one time): authorize cloudflared in the browser when prompted.
#
# Usage:
#   powershell -File scripts/setup-named-tunnel.ps1
#   powershell -File scripts/setup-named-tunnel.ps1 -Hostname api.example.com -InstallService

param(
    [string]$TunnelName = "agentnexus-backend",
    [string]$Hostname = "agentnexus-api.obolla.com",
    [string]$ZoneName = "obolla.com",
    [string]$Origin = "http://127.0.0.1:8000",
    [string]$AccountId = "1f90db97125afc671357b0054beb3da4",
    [string]$ApiToken = "",
    [switch]$InstallService,
    [switch]$SkipSecretUpdate,
    [switch]$UseApiOnly,
    [int]$LoginWaitSeconds = 180
)

$ErrorActionPreference = "Stop"
$RepoRoot = Split-Path $PSScriptRoot -Parent
$ProdDir = Join-Path $RepoRoot ".production"
$TunnelDir = Join-Path $RepoRoot "cloudflare\tunnel"
$CloudflaredDir = Join-Path $env:USERPROFILE ".cloudflared"
New-Item -ItemType Directory -Force -Path $ProdDir, $TunnelDir, $CloudflaredDir | Out-Null

function Get-CloudflaredPath() {
    $cmd = Get-Command cloudflared -ErrorAction SilentlyContinue
    if ($cmd) { return $cmd.Source }
    $fallback = "C:\Program Files (x86)\cloudflared\cloudflared.exe"
    if (Test-Path $fallback) { return $fallback }
    throw "cloudflared not found. Install from https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/downloads/"
}

function Test-BackendHealth([string]$Url) {
    try {
        $r = Invoke-WebRequest -Uri "$Url/docs" -UseBasicParsing -TimeoutSec 4
        return $r.StatusCode -ge 200 -and $r.StatusCode -lt 500
    } catch { return $false }
}

function Invoke-Cloudflared([string]$Cf, [string[]]$CliArgs) {
    $argText = ($CliArgs | ForEach-Object {
        if ($_ -match '\s') { '"' + ($_ -replace '"', '\"') + '"' } else { $_ }
    }) -join ' '
    $cmd = "`"$Cf`" $argText"
    $raw = cmd /c "$cmd 2>nul"
    if ($raw) { return ($raw | Out-String).Trim() }
    $prev = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    try {
        return ((& $Cf @CliArgs 2>&1 | ForEach-Object { "$_" }) -join "`n").Trim()
    } finally {
        $ErrorActionPreference = $prev
    }
}

function Install-CertFromDownloads([string]$DestCert) {
    $candidates = @(
        (Join-Path $env:USERPROFILE "Downloads\cert.pem"),
        (Join-Path $env:USERPROFILE "Desktop\cert.pem")
    )
    foreach ($src in $candidates) {
        if (Test-Path $src) {
            Copy-Item $src $DestCert -Force
            Write-Host "Installed cert.pem from $src" -ForegroundColor Green
            return $true
        }
    }
    return $false
}

function Ensure-CloudflaredLogin([string]$Cf, [int]$WaitSeconds) {
    $cert = Join-Path $CloudflaredDir "cert.pem"
    if (Test-Path $cert) {
        Write-Host "cloudflared cert.pem: OK" -ForegroundColor Green
        return
    }
    if (Install-CertFromDownloads $cert) { return }

    Write-Host "cloudflared login required (one time)." -ForegroundColor Yellow
    Write-Host "A browser window will open. Select your Cloudflare account and authorize." -ForegroundColor Yellow
    Write-Host "If the cert downloads instead, copy it to: $cert" -ForegroundColor Yellow
    $login = Start-Process -FilePath $Cf -ArgumentList "tunnel", "login" -PassThru -WindowStyle Normal
    $deadline = (Get-Date).AddSeconds($WaitSeconds)
    while ((Get-Date) -lt $deadline) {
        if (Test-Path $cert) {
            Write-Host "Login successful." -ForegroundColor Green
            if (-not $login.HasExited) { Stop-Process -Id $login.Id -Force -ErrorAction SilentlyContinue }
            return
        }
        if (Install-CertFromDownloads $cert) {
            if (-not $login.HasExited) { Stop-Process -Id $login.Id -Force -ErrorAction SilentlyContinue }
            return
        }
        if ($login.HasExited -and -not (Test-Path $cert)) {
            if (Install-CertFromDownloads $cert) { return }
            throw "cloudflared login exited before cert.pem was created. Re-run this script."
        }
        Start-Sleep -Seconds 2
    }
    if (Install-CertFromDownloads $cert) { return }
    throw ('Timed out waiting for cloudflared login (' + $WaitSeconds + 's). Re-run after authorizing in the browser.')
}

function Get-OrCreateTunnel([string]$Cf, [string]$Name) {
    $listJson = Invoke-Cloudflared $Cf @("tunnel", "list", "--output", "json")
    if ($listJson) {
        $existing = $listJson | ConvertFrom-Json
        $match = $existing | Where-Object { $_.name -eq $Name } | Select-Object -First 1
        if ($match) {
            Write-Host "Using existing tunnel '$Name' ($($match.id))" -ForegroundColor Green
            return $match.id
        }
    }

    Write-Host "Creating tunnel '$Name'..." -ForegroundColor Cyan
    $createOut = Invoke-Cloudflared $Cf @("tunnel", "create", $Name)
    if ($createOut) { Write-Host $createOut }
    if ($createOut -match '([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})') {
        return $Matches[1]
    }
    $listJson = Invoke-Cloudflared $Cf @("tunnel", "list", "--output", "json")
    $created = ($listJson | ConvertFrom-Json) | Where-Object { $_.name -eq $Name } | Select-Object -First 1
    if ($created) { return $created.id }
    throw "Failed to parse tunnel ID after create"
}

function Ensure-TunnelCredentials([string]$Cf, [string]$TunnelId) {
    $srcCred = Join-Path $CloudflaredDir "$TunnelId.json"
    if (-not (Test-Path $srcCred)) {
        throw "Credentials file not found: $srcCred"
    }
    $destCred = Join-Path $ProdDir "tunnel-credentials.json"
    Copy-Item $srcCred $destCred -Force
    return $destCred
}

function Get-CfApiHeaders([string]$Token) {
    return @{
        Authorization = "Bearer $Token"
        "Content-Type" = "application/json"
    }
}

function Invoke-CfApi(
    [string]$Method,
    [string]$Uri,
    [hashtable]$Headers,
    [object]$Body = $null
) {
    $params = @{
        Uri = $Uri
        Method = $Method
        Headers = $Headers
    }
    if ($null -ne $Body) {
        $params.Body = ($Body | ConvertTo-Json -Depth 8)
    }
    $resp = Invoke-RestMethod @params
    if (-not $resp.success) {
        $msg = ($resp.errors | ForEach-Object { $_.message }) -join "; "
        throw "Cloudflare API error: $msg"
    }
    return $resp.result
}

function Get-ZoneId([string]$Token, [string]$Name) {
    $headers = Get-CfApiHeaders $Token
    $uri = "https://api.cloudflare.com/client/v4/zones?name=$Name"
    $zones = Invoke-CfApi -Method GET -Uri $uri -Headers $headers
    $zone = $zones | Where-Object { $_.name -eq $Name } | Select-Object -First 1
    if (-not $zone) { throw "Zone not found in account: $Name" }
    return $zone.id
}

function Setup-TunnelViaApi(
    [string]$Token,
    [string]$AcctId,
    [string]$Name,
    [string]$PublicHostname,
    [string]$Zone,
    [string]$ServiceUrl
) {
    $headers = Get-CfApiHeaders $Token
    $base = "https://api.cloudflare.com/client/v4/accounts/$AcctId/cfd_tunnel"

    $existing = Invoke-CfApi -Method GET -Uri $base -Headers $headers
    $tunnel = $existing | Where-Object { $_.name -eq $Name } | Select-Object -First 1
    if (-not $tunnel) {
        Write-Host "Creating tunnel '$Name' via API..." -ForegroundColor Cyan
        $tunnel = Invoke-CfApi -Method POST -Uri $base -Headers $headers -Body @{
            name = $Name
            config_src = "cloudflare"
        }
    } else {
        Write-Host "Using existing tunnel '$Name' ($($tunnel.id))" -ForegroundColor Green
    }

    $tunnelId = $tunnel.id
    $configUri = "$base/$tunnelId/configurations"
    Write-Host "Updating tunnel ingress for $PublicHostname" -ForegroundColor Cyan
    Invoke-CfApi -Method PUT -Uri $configUri -Headers $headers -Body @{
        config = @{
            ingress = @(
                @{ hostname = $PublicHostname; service = $ServiceUrl; originRequest = @{} },
                @{ service = "http_status:404" }
            )
        }
    } | Out-Null

    $zoneId = Get-ZoneId -Token $Token -Name $Zone
    $recordName = if ($PublicHostname.EndsWith(".$Zone")) {
        $PublicHostname.Substring(0, $PublicHostname.Length - $Zone.Length - 1)
    } else { $PublicHostname }
    $cnameTarget = "$tunnelId.cfargotunnel.com"
    $dnsUri = "https://api.cloudflare.com/client/v4/zones/$zoneId/dns_records"
    $records = Invoke-CfApi -Method GET -Uri "$dnsUri?type=CNAME&name=$PublicHostname" -Headers $headers
    if ($records -and $records.Count -gt 0) {
        $rec = $records | Select-Object -First 1
        if ($rec.content -ne $cnameTarget) {
            Invoke-CfApi -Method PUT -Uri "$dnsUri/$($rec.id)" -Headers $headers -Body @{
                type = "CNAME"
                proxied = $true
                name = $recordName
                content = $cnameTarget
            } | Out-Null
            Write-Host "Updated DNS CNAME: $PublicHostname -> $cnameTarget" -ForegroundColor Green
        } else {
            Write-Host "DNS CNAME already correct." -ForegroundColor Green
        }
    } else {
        Invoke-CfApi -Method POST -Uri $dnsUri -Headers $headers -Body @{
            type = "CNAME"
            proxied = $true
            name = $recordName
            content = $cnameTarget
        } | Out-Null
        Write-Host "Created DNS CNAME: $PublicHostname -> $cnameTarget" -ForegroundColor Green
    }

    $tokenResult = Invoke-CfApi -Method GET -Uri "$base/$tunnelId/token" -Headers $headers
    $runToken = if ($tokenResult -is [string]) { $tokenResult } else { $tokenResult.token }
    if (-not $runToken) { throw "Failed to fetch tunnel run token" }

    $credPath = Join-Path $ProdDir "tunnel-run-token.txt"
    Set-Content -Path $credPath -Value $runToken -Encoding UTF8 -NoNewline
    return @{
        tunnel_id = $tunnelId
        run_token = $runToken
        token_file = $credPath
    }
}

function Start-TunnelWithToken([string]$Cf, [string]$RunToken, [string]$ConfigFile, [switch]$AsService) {
    if ($AsService) {
        Write-Host "Installing cloudflared Windows service (token mode)..." -ForegroundColor Cyan
        Invoke-Cloudflared $Cf @("service", "uninstall") | Out-Null
        Invoke-Cloudflared $Cf @("service", "install", $RunToken) | ForEach-Object { Write-Host $_ }
        Write-Host "Service installed. cloudflared will start automatically on boot." -ForegroundColor Green
        return
    }

    Write-Host "Starting tunnel in background (token mode)..." -ForegroundColor Cyan
    $log = Join-Path $ProdDir "named-tunnel.log"
    Start-Process -FilePath $cf -ArgumentList @("tunnel", "--no-autoupdate", "run", "--token", $RunToken) `
        -RedirectStandardOutput $log -RedirectStandardError $log -WindowStyle Hidden | Out-Null
}

function Write-TunnelConfig(
    [string]$TunnelId,
    [string]$CredentialsFile,
    [string]$PublicHostname,
    [string]$DestConfig
) {
    $credPath = $CredentialsFile -replace '\\', '/'
    $lines = @(
        "tunnel: $TunnelId",
        "credentials-file: $credPath",
        "",
        "ingress:",
        "  - hostname: $PublicHostname",
        "    service: http://127.0.0.1:8000",
        "  - service: http_status:404"
    )
    Set-Content -Path $DestConfig -Value $lines -Encoding UTF8
    Copy-Item $DestConfig (Join-Path $CloudflaredDir "config.yml") -Force
}

Write-Host "== AgentNexus named tunnel setup ==" -ForegroundColor Cyan
Write-Host "Hostname: https://$Hostname" -ForegroundColor White
Write-Host "Origin:   $Origin" -ForegroundColor White

$cf = Get-CloudflaredPath
if (-not $ApiToken) { $ApiToken = $env:CLOUDFLARE_API_TOKEN }
$usedApi = $false
$tunnelId = $null
$credFile = $null
$configFile = Join-Path $ProdDir "tunnel-config.yml"
$runToken = $null

if (-not (Test-BackendHealth $Origin)) {
    Write-Host "WARNING: Backend not reachable at $Origin" -ForegroundColor Yellow
    Write-Host "Start it first: cd backend; .\run.ps1" -ForegroundColor Yellow
}

if ($ApiToken) {
    Write-Host "Using Cloudflare API token for tunnel setup." -ForegroundColor Cyan
    $apiResult = Setup-TunnelViaApi -Token $ApiToken -AcctId $AccountId -Name $TunnelName `
        -PublicHostname $Hostname -Zone $ZoneName -ServiceUrl $Origin
    $tunnelId = $apiResult.tunnel_id
    $runToken = $apiResult.run_token
    $credFile = $apiResult.token_file
    $usedApi = $true
} elseif ($UseApiOnly) {
    throw "UseApiOnly set but no API token. Set CLOUDFLARE_API_TOKEN or pass -ApiToken."
} else {
    Ensure-CloudflaredLogin -Cf $cf -WaitSeconds $LoginWaitSeconds
    $tunnelId = Get-OrCreateTunnel -Cf $cf -Name $TunnelName
    $credFile = Ensure-TunnelCredentials -Cf $cf -TunnelId $tunnelId
    Write-TunnelConfig -TunnelId $tunnelId -CredentialsFile $credFile -PublicHostname $Hostname -DestConfig $configFile
    Write-Host "Routing DNS: $Hostname -> tunnel $TunnelName" -ForegroundColor Cyan
    $dnsOut = Invoke-Cloudflared $cf @("tunnel", "route", "dns", $TunnelName, $Hostname)
    if ($dnsOut) { Write-Host $dnsOut }
}

$publicUrl = "https://$Hostname"
if (-not $SkipSecretUpdate) {
    Set-Location $RepoRoot
    Write-Host "Updating Worker secret BACKEND_URL -> $publicUrl" -ForegroundColor Cyan
    $publicUrl | npx wrangler secret put BACKEND_URL --env=""
    if ($LASTEXITCODE -ne 0) { throw "wrangler secret put failed" }
}

if ($usedApi) {
    Start-TunnelWithToken -Cf $cf -RunToken $runToken -ConfigFile $configFile -AsService:$InstallService
} elseif ($InstallService) {
    Write-Host "Installing cloudflared Windows service..." -ForegroundColor Cyan
    Invoke-Cloudflared $cf @("service", "uninstall") | Out-Null
    $svcOut = Invoke-Cloudflared $cf @("service", "install", $configFile)
    if ($svcOut) { Write-Host $svcOut }
    if ($svcOut -match "Access is denied") {
        Write-Host "Service install needs Administrator. Starting tunnel in background instead." -ForegroundColor Yellow
        $log = Join-Path $ProdDir "named-tunnel.log"
        $logErr = Join-Path $ProdDir "named-tunnel-err.log"
        Start-Process -FilePath $cf -ArgumentList @("tunnel", "--no-autoupdate", "--config", $configFile, "run") `
            -RedirectStandardOutput $log -RedirectStandardError $logErr -WindowStyle Hidden | Out-Null
    } else {
        Write-Host "Service installed. cloudflared will start automatically on boot." -ForegroundColor Green
    }
} else {
    Write-Host "Starting tunnel in background (not installed as service)..." -ForegroundColor Cyan
    $log = Join-Path $ProdDir "named-tunnel.log"
    $logErr = Join-Path $ProdDir "named-tunnel-err.log"
    Start-Process -FilePath $cf -ArgumentList @("tunnel", "--no-autoupdate", "--config", $configFile, "run") `
        -RedirectStandardOutput $log -RedirectStandardError $logErr -WindowStyle Hidden | Out-Null
}

Start-Sleep -Seconds 8
try {
    $probe = Invoke-WebRequest -Uri "$publicUrl/docs" -UseBasicParsing -TimeoutSec 20
    Write-Host "Tunnel live: $publicUrl (HTTP $($probe.StatusCode))" -ForegroundColor Green
} catch {
    Write-Host "Tunnel DNS may still be propagating. Test manually: $publicUrl/docs" -ForegroundColor Yellow
}

$state = @{
    tunnel_name = $TunnelName
    tunnel_id = $tunnelId
    hostname = $Hostname
    public_url = $publicUrl
    config_file = $configFile
    credentials_file = $credFile
    setup_mode = if ($usedApi) { "api_token" } else { "cloudflared_cert" }
    updated_at = (Get-Date).ToUniversalTime().ToString("o")
}
$state | ConvertTo-Json | Set-Content (Join-Path $ProdDir "named-tunnel.json") -Encoding UTF8

Write-Host ""
Write-Host "Done." -ForegroundColor Green
Write-Host "Stable backend URL: $publicUrl" -ForegroundColor Green
Write-Host "Worker proxy:       https://agentnexus.mrgeo888.workers.dev/api/v1/*" -ForegroundColor Green
Write-Host ""
Write-Host "To install as Windows service (auto-start on boot):" -ForegroundColor Yellow
Write-Host ('  powershell -File scripts/setup-named-tunnel.ps1 -InstallService') -ForegroundColor White
Write-Host ""
Write-Host "API token alternative (no browser login):" -ForegroundColor Yellow
Write-Host ('  $env:CLOUDFLARE_API_TOKEN = "<token-with-Tunnel-Edit+DNS-Edit>"') -ForegroundColor White
Write-Host ('  powershell -File scripts/setup-named-tunnel.ps1 -InstallService') -ForegroundColor White