# Set CLOUDFLARE_API_TOKEN + CLOUDFLARE_ACCOUNT_ID on GitHub repo for deploy-obolla.yml
param(
    [string]$Repo = "Geowahaha/Agentnexus",
    [string]$EnvFile = (Join-Path (Split-Path $PSScriptRoot -Parent) ".env")
)

$ErrorActionPreference = "Stop"

function Read-EnvKey($path, $key) {
    foreach ($line in Get-Content $path -Encoding UTF8) {
        if ($line -match "^\s*$([regex]::Escape($key))\s*=\s*(.+)\s*$") {
            return $Matches[1].Trim().Trim('"').Trim("'")
        }
    }
    return $null
}

$gh = Read-EnvKey $EnvFile "GITHUB_TOKEN"
$cf = Read-EnvKey $EnvFile "CLOUDFLARE_API_TOKEN"
$acct = Read-EnvKey $EnvFile "CLOUDFLARE_ACCOUNT_ID"
if (-not $acct) {
    $wr = Get-Content (Join-Path (Split-Path $PSScriptRoot -Parent) "wrangler.jsonc") -Raw
    if ($wr -match '"account_id"\s*:\s*"([^"]+)"') { $acct = $Matches[1] }
}
if (-not $gh -or -not $cf -or -not $acct) { throw "Need GITHUB_TOKEN, CLOUDFLARE_API_TOKEN, account_id in env or wrangler.jsonc" }

$owner, $name = $Repo -split "/", 2
$headers = @{
    Authorization = "Bearer $gh"
    Accept        = "application/vnd.github+json"
    "X-GitHub-Api-Version" = "2022-11-28"
}

$pk = Invoke-RestMethod -Uri "https://api.github.com/repos/$owner/$name/actions/secrets/public-key" -Headers $headers
$keyBytes = [Convert]::FromBase64String($pk.key)

function Seal-Secret([string]$Plain) {
    $libsodium = Join-Path $env:LOCALAPPDATA "Programs/Python/Python312/Lib/site-packages/nacl"
    if (-not (Get-Module -ListAvailable Sodium -ErrorAction SilentlyContinue)) {
        python -c "from nacl import encoding, public; import base64, sys; pk=base64.b64decode(sys.argv[1]); pub=public.PublicKey(pk); sealed=public.SealedBox(pub).encrypt(sys.argv[2].encode()); print(base64.b64encode(sealed).decode())" $pk.key $Plain
    }
}

# Use Python pynacl (usually available in backend venv)
$backendPy = Join-Path (Split-Path $PSScriptRoot -Parent) "backend\.venv\Scripts\python.exe"
if (-not (Test-Path $backendPy)) { $backendPy = "python" }

function Encrypt-GhSecret([string]$Value) {
    & $backendPy -c @"
from nacl import encoding, public
import base64, sys
pk = base64.b64decode('$($pk.key)')
sealed = public.SealedBox(public.PublicKey(pk)).encrypt(sys.argv[1].encode())
print(base64.b64encode(sealed).decode())
"@ $Value
}

foreach ($pair in @{ CLOUDFLARE_API_TOKEN = $cf; CLOUDFLARE_ACCOUNT_ID = $acct }.GetEnumerator()) {
    $enc = Encrypt-GhSecret $pair.Value
    $body = @{ encrypted_value = $enc; key_id = $pk.key_id } | ConvertTo-Json
    Invoke-RestMethod -Uri "https://api.github.com/repos/$owner/$name/actions/secrets/$($pair.Key)" -Method Put -Headers $headers -Body $body -ContentType "application/json"
    Write-Host "Set secret $($pair.Key)" -ForegroundColor Green
}

Write-Host "Note: CLOUDFLARE_API_TOKEN must include Workers Scripts Edit for GHA deploy." -ForegroundColor Yellow