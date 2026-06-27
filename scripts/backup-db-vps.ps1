# Simple production DB backup for AgentNexus Postgres on VPS.
# Produces timestamped .sql dump locally under .production/
param(
    [string]$VpsHost = "43.128.75.149",
    [string]$VpsUser = "root",
    [string]$SshKey = "$env:USERPROFILE\.ssh\ssh-key-2026-03-21_Oracle_Geomonkey.key",
    [string]$Container = "agentnexus-postgres",
    [string]$DbName = "agentnexus",
    [string]$DbUser = "agentnexus"
)

$ErrorActionPreference = "Stop"
$RepoRoot = Split-Path $PSScriptRoot -Parent
$OutDir = Join-Path $RepoRoot ".production"
if (-not (Test-Path $OutDir)) { New-Item -ItemType Directory -Path $OutDir | Out-Null }

if (-not (Test-Path $SshKey)) { throw "SSH key not found: $SshKey" }

$ts = Get-Date -Format "yyyyMMdd-HHmmss"
$remoteDump = "/tmp/agentnexus-$ts.sql"
$localDump = Join-Path $OutDir "agentnexus-$ts.sql"

$sshBase = @("-i", $SshKey, "-o", "BatchMode=yes", "-o", "StrictHostKeyChecking=accept-new")
$target = "${VpsUser}@${VpsHost}"

Write-Host "Backing up $DbName from $VpsHost (container $Container)..." -ForegroundColor Cyan

& ssh @sshBase $target "docker exec $Container pg_dump -U $DbUser -d $DbName --clean --if-exists > $remoteDump"
if ($LASTEXITCODE -ne 0) { throw "pg_dump on VPS failed" }

& scp @sshBase "${target}:$remoteDump" $localDump
if ($LASTEXITCODE -ne 0) { throw "scp dump failed" }

& ssh @sshBase $target "rm -f $remoteDump"

Write-Host "Backup saved: $localDump" -ForegroundColor Green
Write-Host "Size: $((Get-Item $localDump).Length) bytes" -ForegroundColor DarkGray

# Keep last 10 backups locally
Get-ChildItem $OutDir -Filter "agentnexus-*.sql" | Sort-Object LastWriteTime -Descending | Select-Object -Skip 10 | Remove-Item -Force -ErrorAction SilentlyContinue

Write-Host "Done. Restore example on VPS:"
Write-Host "  cat $localDump | ssh ... 'docker exec -i $Container psql -U $DbUser -d $DbName'" -ForegroundColor DarkGray