$ErrorActionPreference = 'Stop'
$RepoRoot = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$env:AGENTNEXUS_ACCESS_TOKEN = if ($env:AGENTNEXUS_ACCESS_TOKEN) { $env:AGENTNEXUS_ACCESS_TOKEN } else {
  'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIzMjU4NzQ1Ni1iM2ZmLTQ0YTUtOTM3NC0yOGU1ZGUyMTcwNDMiLCJleHAiOjE3ODE4ODcyNzZ9.mYiYu6G2OGjKnhOXlrjN95wfcQJNclkEABakWsoOxRA'
}
Set-Location (Join-Path $RepoRoot 'packages/bridge')
node (Join-Path $RepoRoot 'backend/scripts/test_consent_timeout_production.mjs')