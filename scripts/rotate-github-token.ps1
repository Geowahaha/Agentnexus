# Rotate compromised GitHub PAT: swap to GIT_TOKEN, store in GCM, revoke old GITHUB_TOKEN.
param(
    [string]$RepoRoot = (Split-Path $PSScriptRoot -Parent),
    [switch]$SkipRevoke
)

$ErrorActionPreference = "Stop"
$rootEnv = Join-Path $RepoRoot ".env"
$backendEnv = Join-Path $RepoRoot "backend\.env"

function Read-EnvKey($path, $key) {
    if (-not (Test-Path $path)) { return $null }
    foreach ($line in Get-Content $path -Encoding UTF8) {
        if ($line -match "^\s*$([regex]::Escape($key))\s*=\s*(.+)\s*$") {
            return $Matches[1].Trim().Trim('"').Trim("'")
        }
    }
    return $null
}

function Set-EnvKey($path, $key, $value) {
    $lines = if (Test-Path $path) { Get-Content $path -Encoding UTF8 } else { @() }
    $found = $false
    $out = foreach ($line in $lines) {
        if ($line -match "^\s*$([regex]::Escape($key))\s*=") {
            $found = $true
            "$key=$value"
        } else {
            $line
        }
    }
    if (-not $found) { $out += "$key=$value" }
    Set-Content -Path $path -Value $out -Encoding UTF8
}

$oldToken = Read-EnvKey $rootEnv "GITHUB_TOKEN"
$newToken = Read-EnvKey $backendEnv "GIT_TOKEN"
if (-not $newToken) { throw "GIT_TOKEN missing in backend/.env" }
if ($oldToken -eq $newToken) {
    Write-Host "GITHUB_TOKEN already matches GIT_TOKEN." -ForegroundColor DarkGray
} else {
    Set-EnvKey $rootEnv "GITHUB_TOKEN" $newToken
    if (Test-Path $backendEnv) {
        if (-not (Read-EnvKey $backendEnv "GITHUB_TOKEN")) {
            Add-Content -Path $backendEnv -Value "GITHUB_TOKEN=$newToken" -Encoding UTF8
        } else {
            Set-EnvKey $backendEnv "GITHUB_TOKEN" $newToken
        }
    }
    Write-Host "Updated GITHUB_TOKEN in .env files (using GIT_TOKEN)." -ForegroundColor Green
}

& (Join-Path $RepoRoot "scripts\setup-github-credential-manager.ps1") -RepoRoot $RepoRoot -EnvFile $rootEnv

if (-not $SkipRevoke -and $oldToken -and $oldToken -ne $newToken) {
    try {
        $body = @{ credentials = @($oldToken) } | ConvertTo-Json
        $resp = Invoke-WebRequest -Method POST -Uri "https://api.github.com/credentials/revoke" `
            -Body $body -ContentType "application/json" `
            -Headers @{ Accept = "application/vnd.github+json" } -TimeoutSec 30
        if ($resp.StatusCode -eq 202) {
            Write-Host "Revocation requested for exposed GITHUB_TOKEN (HTTP 202)." -ForegroundColor Green
        }
    } catch {
        Write-Host "Credential revoke API failed: $($_.Exception.Message)" -ForegroundColor Yellow
        Write-Host "Revoke manually: https://github.com/settings/tokens" -ForegroundColor Yellow
    }
    Start-Sleep -Seconds 5
    try {
        $null = Invoke-RestMethod -Uri "https://api.github.com/user" -Headers @{ Authorization = "token $oldToken" } -TimeoutSec 15
        Write-Host "Old token may still be active briefly; check https://github.com/settings/tokens" -ForegroundColor Yellow
    } catch {
        Write-Host "Old GITHUB_TOKEN is no longer valid." -ForegroundColor Green
    }
}

Write-Host "Rotation setup complete. Test: git ls-remote origin HEAD" -ForegroundColor Cyan