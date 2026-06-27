# Initial push or update Geowahaha/Agentnexus (secrets stay in .env — gitignored).
param(
    [string]$Repo = "Geowahaha/Agentnexus",
    [string]$EnvFile = (Join-Path (Split-Path $PSScriptRoot -Parent) ".env")
)

$ErrorActionPreference = "Stop"
$RepoRoot = Split-Path $PSScriptRoot -Parent
Set-Location $RepoRoot

function Read-EnvKey($path, $key) {
    foreach ($line in Get-Content $path -Encoding UTF8) {
        if ($line -match "^\s*$([regex]::Escape($key))\s*=\s*(.+)\s*$") {
            return $Matches[1].Trim().Trim('"').Trim("'")
        }
    }
    return $null
}

if (-not (Test-Path ".git")) {
    git init
    git branch -M main
}

$setupCreds = Join-Path $PSScriptRoot "setup-github-credential-manager.ps1"
if (-not (Test-Path $setupCreds)) { throw "Missing $setupCreds" }
& $setupCreds -Repo $Repo -RepoRoot $RepoRoot -EnvFile $EnvFile | Out-Host

git add -A
$status = git status --porcelain
if ($status) {
    git commit -m "chore: AgentNexus / OBOLLA — agent-ready MCP + Worker deploy workflow"
}

git push -u origin main --force
Write-Host "Pushed to https://github.com/$Repo" -ForegroundColor Green