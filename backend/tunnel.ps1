# Expose local FastAPI (127.0.0.1:8000) via Cloudflare quick tunnel.
# After start, set BACKEND_URL on the Worker to the printed trycloudflare.com URL.
# For production, replace with a named tunnel + custom hostname.

param(
    [string]$Origin = "http://127.0.0.1:8000"
)

Write-Host "Starting Cloudflare tunnel -> $Origin" -ForegroundColor Cyan
Write-Host "Copy the https://*.trycloudflare.com URL, then run:" -ForegroundColor Yellow
Write-Host '  echo "https://YOUR-TUNNEL.trycloudflare.com" | npx wrangler secret put BACKEND_URL' -ForegroundColor Yellow
cloudflared tunnel --url $Origin