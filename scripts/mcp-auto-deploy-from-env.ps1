# Call OBOLLA MCP apply_agent_ready_fix with tokens from .env (no token echo).
param(
    [string]$PayloadPath = (Join-Path $PSScriptRoot "..\Obolla cast study\mcp-payload.json"),
    [string]$EnvFile = (Join-Path $PSScriptRoot "..\.env")
)

$ErrorActionPreference = "Stop"

function Read-EnvKey($path, $key) {
    if (-not (Test-Path $path)) { return $null }
    foreach ($line in Get-Content $path -Encoding UTF8) {
        if ($line -match "^\s*$([regex]::Escape($key))\s*=\s*(.+)\s*$") {
            return $Matches[1].Trim().Trim('"').Trim("'")
        }
    }
    return $null
}

$githubToken = Read-EnvKey $EnvFile "GITHUB_TOKEN"
$cfToken = Read-EnvKey $EnvFile "CLOUDFLARE_API_TOKEN"
$repo = "Geowahaha/Agentnexus"
$cfAccount = Read-EnvKey $EnvFile "CLOUDFLARE_ACCOUNT_ID"
if (-not $cfAccount) {
    $wr = Get-Content (Join-Path (Split-Path $PSScriptRoot -Parent) "wrangler.jsonc") -Raw
    if ($wr -match '"account_id"\s*:\s*"([^"]+)"') { $cfAccount = $Matches[1] }
}

if (-not $githubToken) { throw "GITHUB_TOKEN not found in $EnvFile" }
if (-not (Test-Path $PayloadPath)) { throw "Payload not found: $PayloadPath" }

$base = Get-Content -Raw $PayloadPath | ConvertFrom-Json
# stack.detect() requires https:// — bare host breaks GitHub auto-deploy
$base.params.arguments.url = "https://obolla.com"
$base.params.arguments | Add-Member -NotePropertyName github_token -NotePropertyValue $githubToken -Force
$base.params.arguments | Add-Member -NotePropertyName repo -NotePropertyValue $repo -Force
if ($cfToken) {
    $base.params.arguments | Add-Member -NotePropertyName cf_api_token -NotePropertyValue $cfToken -Force
}
if ($cfAccount) {
    $base.params.arguments | Add-Member -NotePropertyName cf_account_id -NotePropertyValue $cfAccount -Force
}
$base.params.arguments | Add-Member -NotePropertyName cf_worker_name -NotePropertyValue "agentnexus" -Force

$body = $base | ConvertTo-Json -Depth 30 -Compress
$r = Invoke-RestMethod -Uri "https://obolla.com/mcp" -Method POST -ContentType "application/json" -Body $body
$parsed = $r.result.content[0].text | ConvertFrom-Json

[ordered]@{
    mcp_success = $parsed.result.mcp_success
    auto_deployed = $parsed.result.auto_deployed
    pack_files = $parsed.result.pack_files
    message = $parsed.result.message
    github = $parsed.result.github
    github_error = $parsed.result.github_error
    cloudflare_worker = $parsed.result.cloudflare_worker
    cloudflare_worker_verify = $parsed.result.cloudflare_worker_verify
    cloudflare_worker_error = $parsed.result.cloudflare_worker_error
    cloudflare_error = $parsed.result.cloudflare_error
    revenue_logged = $parsed.revenue_logged
    billing_id = $parsed.sale.billing_id
    earning_id = $parsed.sale.earning_id
    amount_usd = $parsed.sale.amount_usd
    repo_used = $repo
    cf_token_workers = "403-scoped-DNS/Tunnel-only"
} | ConvertTo-Json -Depth 8