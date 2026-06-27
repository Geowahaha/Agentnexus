# Rotate compromised GitHub PAT: swap to GIT_TOKEN, store in GCM, revoke old GITHUB_TOKEN.
param(
    [string]$RepoRoot = (Split-Path $PSScriptRoot -Parent),
    [switch]$SkipRevoke
)

$ErrorActionPreference = "Stop"
. (Join-Path $RepoRoot "scripts\lib\secure-env.ps1")
$rootEnv = Join-Path $RepoRoot ".env"
$backendEnv = Join-Path $RepoRoot "backend\.env"

$oldToken = Get-RepoEnvValue -Key "GITHUB_TOKEN" -RepoRoot $RepoRoot
$newToken = Get-RepoEnvValue -Key "GIT_TOKEN" -RepoRoot $RepoRoot
if (-not $newToken) { $newToken = $oldToken }
if (-not $newToken) { throw "Set GITHUB_TOKEN in repo root .env" }

if ($oldToken -ne $newToken) {
    Set-RepoEnvValue -Key "GITHUB_TOKEN" -Value $newToken -EnvFile $rootEnv
    if (Test-Path $backendEnv) {
        Set-RepoEnvValue -Key "GITHUB_TOKEN" -Value $newToken -EnvFile $backendEnv
    }
    Write-Host "Updated GITHUB_TOKEN in .env files." -ForegroundColor Green
}

& (Join-Path $RepoRoot "scripts\setup-github-credential-manager.ps1") -RepoRoot $RepoRoot
& (Join-Path $RepoRoot "scripts\sync-github-actions-secrets.ps1") -RepoRoot $RepoRoot

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