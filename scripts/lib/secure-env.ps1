# Secure env access for OBOLLA scripts — never print secret values.
param()

function Get-RepoEnvValue {
    param(
        [Parameter(Mandatory)][string]$Key,
        [string]$RepoRoot = (Split-Path (Split-Path $PSScriptRoot -Parent) -Parent),
        [string[]]$EnvFiles = @(),
        [string[]]$FallbackKeys = @()
    )

    if (-not $EnvFiles.Count) {
        $EnvFiles = @(
            (Join-Path $RepoRoot ".env"),
            (Join-Path $RepoRoot "backend\.env")
        )
    }

    foreach ($file in $EnvFiles) {
        if (-not (Test-Path $file)) { continue }
        foreach ($line in Get-Content $file -Encoding UTF8) {
            if ($line -match "^\s*$([regex]::Escape($Key))\s*=\s*(.+)\s*$") {
                $val = $Matches[1].Trim().Trim('"').Trim("'")
                if ($val) { return $val }
            }
        }
    }

    foreach ($alt in $FallbackKeys) {
        $v = Get-RepoEnvValue -Key $alt -RepoRoot $RepoRoot -EnvFiles $EnvFiles
        if ($v) { return $v }
    }

    return $null
}

function Get-GithubPat {
    param([string]$RepoRoot = (Split-Path (Split-Path $PSScriptRoot -Parent) -Parent))
    $token = Get-RepoEnvValue -Key "GITHUB_TOKEN" -RepoRoot $RepoRoot -FallbackKeys @("GIT_TOKEN")
    if (-not $token) {
        throw "GITHUB_TOKEN not found in .env or backend/.env (gitignored). Add GITHUB_TOKEN=ghp_... to repo root .env"
    }
    return $token
}

function Set-RepoEnvValue {
    param(
        [Parameter(Mandatory)][string]$Key,
        [Parameter(Mandatory)][string]$Value,
        [string]$EnvFile
    )
    $lines = if (Test-Path $EnvFile) { Get-Content $EnvFile -Encoding UTF8 } else { @() }
    $found = $false
    $out = foreach ($line in $lines) {
        if ($line -match "^\s*$([regex]::Escape($Key))\s*=") {
            $found = $true
            "$Key=$Value"
        } else {
            $line
        }
    }
    if (-not $found) { $out += "$Key=$Value" }
    Set-Content -Path $EnvFile -Value $out -Encoding UTF8
}

function Test-GithubPat {
    param([string]$Token)
    try {
        $null = Invoke-RestMethod -Uri "https://api.github.com/user" -Headers @{
            Authorization = "Bearer $Token"
            Accept        = "application/vnd.github+json"
        } -TimeoutSec 20
        return $true
    } catch {
        return $false
    }
}