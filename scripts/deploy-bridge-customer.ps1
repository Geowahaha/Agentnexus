# Deploy AgentNexus Local Bridge to a customer Windows PC (remote support).
param(
    [Parameter(Mandatory = $true)]
    [string]$PairingCode,
    [string]$DeviceName = "Customer-PC",
    [string]$ApiBase = "https://obolla.com",
    [switch]$AllowWrite,
    [switch]$InstallTray
)

$ErrorActionPreference = "Stop"
$RepoRoot = Split-Path $PSScriptRoot -Parent
$BridgeDir = Join-Path $RepoRoot "packages\bridge"
$TrayDir = Join-Path $RepoRoot "packages\bridge-tray"

if (-not (Get-Command node -ErrorAction SilentlyContinue)) {
    throw "Node.js 18+ required. Install from https://nodejs.org"
}

Set-Location $BridgeDir
if (-not (Test-Path node_modules)) {
    npm install
}

$pairArgs = @("index.mjs", "pair", $PairingCode, "--name", $DeviceName, "--api", $ApiBase)
if ($AllowWrite) { $pairArgs += "--allow-write" }

Write-Host "Pairing $DeviceName with AgentNexus production..." -ForegroundColor Cyan
node @pairArgs
if ($LASTEXITCODE -ne 0) { throw "Pair failed" }

if ($InstallTray) {
    & (Join-Path $TrayDir "install-windows.ps1") -ApiBase $ApiBase
    Write-Host "Tray scheduled task installed. Bridge starts at next logon." -ForegroundColor Green
    Write-Host "Start now: powershell -File `"$(Join-Path $TrayDir 'tray.ps1')`" -ApiBase `"$ApiBase`"" -ForegroundColor Yellow
} else {
    Write-Host ""
    Write-Host "Paired. Keep bridge running:" -ForegroundColor Green
    Write-Host "  cd packages\bridge" -ForegroundColor White
    Write-Host "  node index.mjs connect --api $ApiBase" -ForegroundColor White
}