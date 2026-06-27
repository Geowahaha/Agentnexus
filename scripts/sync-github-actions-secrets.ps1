# Sync .env values to GitHub Actions encrypted repo secrets (never echoes secrets).
param(
    [string]$Repo = "Geowahaha/Agentnexus",
    [string]$RepoRoot = (Split-Path $PSScriptRoot -Parent),
    [string[]]$SecretNames = @("OBOLLA_GITHUB_PAT", "CLOUDFLARE_API_TOKEN", "CLOUDFLARE_ACCOUNT_ID")
)

$ErrorActionPreference = "Stop"
. (Join-Path $PSScriptRoot "lib\secure-env.ps1")

$ghPat = Get-GithubPat -RepoRoot $RepoRoot
if (-not (Test-GithubPat -Token $ghPat)) { throw "GITHUB_TOKEN in .env is invalid or expired" }

$cf = Get-RepoEnvValue -Key "CLOUDFLARE_API_TOKEN" -RepoRoot $RepoRoot
$acct = Get-RepoEnvValue -Key "CLOUDFLARE_ACCOUNT_ID" -RepoRoot $RepoRoot
if (-not $acct) {
    $wr = Join-Path $RepoRoot "wrangler.jsonc"
    if (Test-Path $wr) {
        $raw = Get-Content $wr -Raw
        if ($raw -match '"account_id"\s*:\s*"([^"]+)"') { $acct = $Matches[1] }
    }
}

# GitHub forbids secret names starting with GITHUB_ (reserved for Actions built-in token).
$values = @{
    OBOLLA_GITHUB_PAT     = $ghPat
    CLOUDFLARE_API_TOKEN  = $cf
    CLOUDFLARE_ACCOUNT_ID = $acct
}

$owner, $name = $Repo -split "/", 2
$headers = @{
    Authorization        = "Bearer $ghPat"
    Accept               = "application/vnd.github+json"
    "X-GitHub-Api-Version" = "2022-11-28"
}

$backendPy = Join-Path $RepoRoot "backend\.venv\Scripts\python.exe"
if (-not (Test-Path $backendPy)) { $backendPy = "python" }
& $backendPy -c "import nacl" 2>$null
if ($LASTEXITCODE -ne 0) {
    $pip = Join-Path (Split-Path $backendPy -Parent) "pip.exe"
    if (Test-Path $pip) { & $pip install pynacl -q }
    else { & $backendPy -m pip install pynacl -q }
}

$pk = Invoke-RestMethod -Uri "https://api.github.com/repos/$owner/$name/actions/secrets/public-key" -Headers $headers

function Encrypt-GhSecret([string]$Value) {
    & $backendPy -c @"
from nacl import encoding, public
import base64, sys
pk = base64.b64decode('$($pk.key)')
sealed = public.SealedBox(public.PublicKey(pk)).encrypt(sys.argv[1].encode())
print(base64.b64encode(sealed).decode())
"@ $Value
}

foreach ($secretName in $SecretNames) {
    $plain = $values[$secretName]
    if (-not $plain) {
        Write-Host "Skip $secretName (not in .env)" -ForegroundColor Yellow
        continue
    }
    $enc = Encrypt-GhSecret $plain
    $body = @{ encrypted_value = $enc; key_id = $pk.key_id } | ConvertTo-Json
    Invoke-RestMethod -Uri "https://api.github.com/repos/$owner/$name/actions/secrets/$secretName" `
        -Method Put -Headers $headers -Body $body -ContentType "application/json"
    Write-Host "Set Actions secret: $secretName" -ForegroundColor Green
}

# Verify names exist (values are never returned by API)
$list = Invoke-RestMethod -Uri "https://api.github.com/repos/$owner/$name/actions/secrets" -Headers $headers
$names = $list.secrets | ForEach-Object { $_.name }
foreach ($secretName in $SecretNames) {
    if ($names -contains $secretName) {
        Write-Host "Verified secret present: $secretName" -ForegroundColor DarkGray
    }
}

Write-Host "GitHub Actions secrets sync complete for $Repo" -ForegroundColor Cyan
Write-Host "CLOUDFLARE_API_TOKEN needs Workers Scripts Edit for deploy-obolla.yml wrangler deploy." -ForegroundColor Yellow