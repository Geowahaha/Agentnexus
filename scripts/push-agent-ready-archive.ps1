# Commit and push agent-ready-sites/ run archives to git.
param(
    [string]$RepoRoot = (Split-Path $PSScriptRoot -Parent),
    [switch]$PushOnly,
    [switch]$NoPush
)

$ErrorActionPreference = "Stop"
$ArchiveDir = Join-Path $RepoRoot "agent-ready-sites"

if (-not (Test-Path $ArchiveDir)) {
    Write-Host "No archive dir yet: $ArchiveDir" -ForegroundColor Yellow
    exit 0
}

Push-Location $RepoRoot
try {
    if (-not (Test-Path ".git")) {
        throw "Not a git repo: $RepoRoot"
    }

    $status = git status --porcelain -- agent-ready-sites 2>&1
    if (-not $PushOnly -and $status) {
        git add agent-ready-sites
        $msg = "agent-ready: archive sync $(Get-Date -Format 'yyyy-MM-ddTHH:mm:ssZ')"
        git commit -m $msg
        if ($LASTEXITCODE -ne 0) {
            $combined = (git status --porcelain -- agent-ready-sites) -join "`n"
            if (-not $combined) {
                Write-Host "Nothing new to commit under agent-ready-sites/" -ForegroundColor DarkGray
            } else {
                throw "git commit failed"
            }
        } else {
            Write-Host "Committed archive changes." -ForegroundColor Green
        }
    } elseif (-not $PushOnly) {
        Write-Host "agent-ready-sites/ already clean — nothing to commit." -ForegroundColor DarkGray
    }

    if (-not $NoPush) {
        git push
        if ($LASTEXITCODE -ne 0) { throw "git push failed" }
        Write-Host "Pushed agent-ready-sites/ to origin." -ForegroundColor Green
    }
} finally {
    Pop-Location
}