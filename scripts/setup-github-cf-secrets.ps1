# Back-compat wrapper — sync Cloudflare + GitHub tokens to Actions secrets.
param(
    [string]$Repo = "Geowahaha/Agentnexus",
    [string]$EnvFile = (Join-Path (Split-Path $PSScriptRoot -Parent) ".env")
)

$ErrorActionPreference = "Stop"
$RepoRoot = Split-Path $PSScriptRoot -Parent
& (Join-Path $PSScriptRoot "sync-github-actions-secrets.ps1") -Repo $Repo -RepoRoot $RepoRoot