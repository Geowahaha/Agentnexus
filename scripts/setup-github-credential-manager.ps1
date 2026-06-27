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
. (Join-Path $PSScriptRoot "lib\secure-env.ps1")

$token = Get-GithubPat -RepoRoot $RepoRoot
if (-not (Test-GithubPat -Token $token)) { throw "GITHUB_TOKEN in .env is invalid or expired" }

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