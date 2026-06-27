# Deploy AgentNexus to Cloudflare Workers + static assets (agentnexus.mrgeo888.workers.dev)
# Prerequisites: npm install, wrangler login, backend running or BACKEND_URL secret set

param(
    [switch]$PagesOnly,
    [switch]$DryRun
)

Set-Location $PSScriptRoot

if (-not (Test-Path "node_modules")) {
    Write-Host "Installing root dependencies..." -ForegroundColor Cyan
    npm install
}

Write-Host "Building frontend..." -ForegroundColor Cyan
npm run build:frontend
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

if ($PagesOnly) {
    $args = @("pages", "deploy", "frontend/dist", "--project-name=agentnexus", "--branch=main")
    if ($DryRun) { $args += "--dry-run" }
    npx wrangler @args
    exit $LASTEXITCODE
}

Write-Host "Deploying Worker + assets (agentnexus)..." -ForegroundColor Cyan
if ($DryRun) {
    npx wrangler deploy --dry-run
} else {
    npx wrangler deploy
}
exit $LASTEXITCODE