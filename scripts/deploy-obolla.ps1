# Deploy OBOLLA edge (Cloudflare Worker + SPA on obolla.com).
# Handles CLOUDFLARE_API_TOKEN in .env: scoped DNS/tunnel tokens block wrangler deploy;
# when Workers permission is missing, temporarily moves .env aside and uses OAuth.
param(
    [switch]$SkipBuild,
    [switch]$SkipSmoke,
    [switch]$DryRun,
    [switch]$ForceOAuth
)

$ErrorActionPreference = "Stop"
$RepoRoot = Split-Path $PSScriptRoot -Parent
$EnvFile = Join-Path $RepoRoot ".env"
$EnvBak = Join-Path $RepoRoot ".env.wrangler-deploy-bak"
$WranglerConfig = Join-Path $RepoRoot "wrangler.jsonc"
$PublicUrl = "https://obolla.com"

Set-Location $RepoRoot

function Read-DotEnvValue {
    param([string]$Path, [string]$Key)
    if (-not (Test-Path $Path)) { return $null }
    foreach ($line in Get-Content $Path -Encoding UTF8) {
        if ($line -match "^\s*$([regex]::Escape($Key))\s*=\s*(.+)\s*$") {
            return $Matches[1].Trim().Trim('"').Trim("'")
        }
    }
    return $null
}

function Read-AccountIdFromWrangler {
    if (-not (Test-Path $WranglerConfig)) { return $null }
    $raw = Get-Content $WranglerConfig -Raw -Encoding UTF8
    if ($raw -match '"account_id"\s*:\s*"([^"]+)"') { return $Matches[1] }
    return $null
}

function Get-DeployToken {
    $fromProcess = [Environment]::GetEnvironmentVariable("CLOUDFLARE_API_TOKEN", "Process")
    if (-not [string]::IsNullOrWhiteSpace($fromProcess)) { return $fromProcess.Trim() }
    return Read-DotEnvValue -Path $EnvFile -Key "CLOUDFLARE_API_TOKEN"
}

function Get-AccountId {
    $id = [Environment]::GetEnvironmentVariable("CLOUDFLARE_ACCOUNT_ID", "Process")
    if ([string]::IsNullOrWhiteSpace($id)) {
        $id = Read-DotEnvValue -Path $EnvFile -Key "CLOUDFLARE_ACCOUNT_ID"
    }
    if ([string]::IsNullOrWhiteSpace($id)) {
        $id = Read-AccountIdFromWrangler
    }
    return $id
}

function Test-WorkersDeployToken {
    param([string]$Token, [string]$AccountId)
    if ([string]::IsNullOrWhiteSpace($Token) -or [string]::IsNullOrWhiteSpace($AccountId)) {
        return $false
    }
    try {
        $uri = "https://api.cloudflare.com/client/v4/accounts/$AccountId/workers/scripts"
        $resp = Invoke-RestMethod -Uri $uri -Headers @{ Authorization = "Bearer $Token" } -Method Get
        return [bool]$resp.success
    } catch {
        return $false
    }
}

function Clear-WranglerTokenFromProcess {
    Remove-Item Env:CLOUDFLARE_API_TOKEN -ErrorAction SilentlyContinue
    Remove-Item Env:CF_API_TOKEN -ErrorAction SilentlyContinue
}

function Restore-EnvFileIfBackedUp {
    if ((Test-Path $EnvBak) -and -not (Test-Path $EnvFile)) {
        Rename-Item $EnvBak $EnvFile -Force
        Write-Host "Restored .env from backup." -ForegroundColor DarkGray
    } elseif ((Test-Path $EnvBak) -and (Test-Path $EnvFile)) {
        Write-Warning "Both .env and .env.wrangler-deploy-bak exist — keeping .env; remove backup manually if stale."
    }
}

function Invoke-WranglerDeploy {
    param([string[]]$ExtraArgs)
    $wranglerExe = Join-Path $RepoRoot "node_modules\.bin\wrangler.cmd"
    if (-not (Test-Path $wranglerExe)) {
        throw "wrangler not found — run: npm install (repo root)"
    }
    $wranglerCli = @("deploy", '--env=""') + $ExtraArgs
    Write-Host ("  wrangler {0}" -f ($wranglerCli -join " ")) -ForegroundColor DarkGray
    & $wranglerExe @wranglerCli
    if ($LASTEXITCODE -ne 0) { throw "wrangler deploy failed (exit $LASTEXITCODE)" }
}

function Invoke-OAuthWranglerDeploy {
    param([string[]]$ExtraArgs)
    Restore-EnvFileIfBackedUp
    Clear-WranglerTokenFromProcess

    $movedEnv = $false
    $dotEnvHasToken = $false
    if (Test-Path $EnvFile) {
        $dotEnvHasToken = [bool](Read-DotEnvValue -Path $EnvFile -Key "CLOUDFLARE_API_TOKEN")
    }

    if ($dotEnvHasToken) {
        Write-Host "OAuth deploy: moving .env aside (CLOUDFLARE_API_TOKEN lacks Workers deploy or -ForceOAuth)." -ForegroundColor Yellow
        Rename-Item $EnvFile $EnvBak -Force
        $movedEnv = $true
    }

    try {
        Invoke-WranglerDeploy -ExtraArgs $ExtraArgs
    } finally {
        if ($movedEnv -and (Test-Path $EnvBak)) {
            if (Test-Path $EnvFile) { Remove-Item $EnvFile -Force }
            Rename-Item $EnvBak $EnvFile -Force
            Write-Host "Restored .env after deploy." -ForegroundColor DarkGray
        }
    }
}

Write-Host "== OBOLLA edge deploy (obolla.com) ==" -ForegroundColor Cyan

Restore-EnvFileIfBackedUp

if (-not $SkipBuild) {
    Write-Host "Building frontend..." -ForegroundColor Cyan
    npm run build:frontend
    if ($LASTEXITCODE -ne 0) { throw "frontend build failed" }
} else {
    Write-Host "Skipping frontend build (-SkipBuild)." -ForegroundColor DarkGray
}

$accountId = Get-AccountId
$token = Get-DeployToken
$tokenCanDeploy = (-not $ForceOAuth) -and (Test-WorkersDeployToken -Token $token -AccountId $accountId)

$wranglerArgs = @()
if ($DryRun) { $wranglerArgs += "--dry-run" }

if ($tokenCanDeploy) {
    Write-Host "Deploying with CLOUDFLARE_API_TOKEN (Workers permission OK)..." -ForegroundColor Cyan
    Invoke-WranglerDeploy -ExtraArgs $wranglerArgs
} else {
    if ($ForceOAuth) {
        Write-Host "Deploying with OAuth (-ForceOAuth)..." -ForegroundColor Cyan
    } elseif ([string]::IsNullOrWhiteSpace($token)) {
        Write-Host "No CLOUDFLARE_API_TOKEN — deploying with OAuth session..." -ForegroundColor Cyan
    } else {
        Write-Host "CLOUDFLARE_API_TOKEN is valid but missing Workers Scripts permission — switching to OAuth..." -ForegroundColor Yellow
        Write-Host "  Tip: create a token with Workers Scripts Edit, or run: npx wrangler login" -ForegroundColor DarkGray
    }
    Invoke-OAuthWranglerDeploy -ExtraArgs $wranglerArgs
}

if ($DryRun) {
    Write-Host "Dry run complete (no production upload)." -ForegroundColor Green
    exit 0
}

if (-not $SkipSmoke) {
    Write-Host "Smoke test: $PublicUrl/health" -ForegroundColor Cyan
    $health = Invoke-RestMethod -Uri "$PublicUrl/health" -TimeoutSec 30
    $ok = ($health.status -eq "ok") -and ($health.backend_reachable -eq $true)
    Write-Host ("  status={0} backend_reachable={1}" -f $health.status, $health.backend_reachable) -ForegroundColor $(if ($ok) { "Green" } else { "Red" })
    if (-not $ok) { throw "Health check failed - deploy uploaded but production is not healthy." }
}

Write-Host ""
Write-Host "Deployed: $PublicUrl" -ForegroundColor Green
Write-Host "Worker:   https://agentnexus.mrgeo888.workers.dev" -ForegroundColor Green