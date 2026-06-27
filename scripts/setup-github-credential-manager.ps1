# Remove embedded GitHub tokens from git remote; store credentials in Git Credential Manager.
param(
    [string]$Repo = "Geowahaha/Agentnexus",
    [string]$RepoRoot = (Split-Path $PSScriptRoot -Parent),
    [string]$EnvFile = "",
    [string]$Username = "Geowahaha",
    [switch]$UseGitTokenFromBackend
)

$ErrorActionPreference = "Stop"
if (-not $EnvFile) { $EnvFile = Join-Path $RepoRoot ".env" }

function Read-EnvKey($path, $key) {
    if (-not (Test-Path $path)) { return $null }
    foreach ($line in Get-Content $path -Encoding UTF8) {
        if ($line -match "^\s*$([regex]::Escape($key))\s*=\s*(.+)\s*$") {
            return $Matches[1].Trim().Trim('"').Trim("'")
        }
    }
    return $null
}

$token = Read-EnvKey $EnvFile "GITHUB_TOKEN"
if ($UseGitTokenFromBackend) {
    $backendToken = Read-EnvKey (Join-Path $RepoRoot "backend\.env") "GIT_TOKEN"
    if ($backendToken) { $token = $backendToken }
}
if (-not $token) { throw "GITHUB_TOKEN (or GIT_TOKEN with -UseGitTokenFromBackend) missing" }

Push-Location $RepoRoot
try {
    if (-not (Test-Path ".git")) { throw "Not a git repo: $RepoRoot" }

    git config --global credential.helper manager
    git remote set-url origin "https://github.com/$Repo.git"

    $credInput = @"
protocol=https
host=github.com
username=$Username
password=$token

"@
    $credInput | git credential-manager store

    $probe = git ls-remote origin HEAD 2>&1
    if ($LASTEXITCODE -ne 0) { throw "git ls-remote failed: $probe" }

    Write-Host "Git remote cleaned (no token in URL)." -ForegroundColor Green
    Write-Host "Credentials stored in Git Credential Manager." -ForegroundColor Green
    Write-Host "Remote: https://github.com/$Repo.git" -ForegroundColor DarkGray
} finally {
    Pop-Location
}