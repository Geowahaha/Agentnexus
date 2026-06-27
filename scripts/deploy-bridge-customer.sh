#!/usr/bin/env bash
# Deploy AgentNexus Local Bridge on a customer Linux VPS (remote support).
set -euo pipefail

PAIRING_CODE="${1:-}"
DEVICE_NAME="${2:-Customer-VPS}"
API_BASE="${3:-https://obolla.com}"
ALLOW_WRITE="${4:-1}"

if [[ -z "$PAIRING_CODE" ]]; then
  echo "Usage: $0 <PAIRING_CODE> [device_name] [api_base] [allow_write=1]"
  exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
BRIDGE_DIR="$REPO_ROOT/packages/bridge"

command -v node >/dev/null || { echo "Node.js 18+ required"; exit 1; }

cd "$BRIDGE_DIR"
npm install --omit=dev

PAIR_ARGS=(index.mjs pair "$PAIRING_CODE" --name "$DEVICE_NAME" --api "$API_BASE")
if [[ "$ALLOW_WRITE" == "1" ]]; then
  PAIR_ARGS+=(--allow-write)
fi

echo "Pairing $DEVICE_NAME with $API_BASE ..."
node "${PAIR_ARGS[@]}"

UNIT=/etc/systemd/system/agentnexus-bridge.service
sudo tee "$UNIT" >/dev/null <<EOF
[Unit]
Description=AgentNexus Local Bridge
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=$(whoami)
WorkingDirectory=$BRIDGE_DIR
ExecStart=$(command -v node) index.mjs connect --api $API_BASE
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable --now agentnexus-bridge
sudo systemctl status agentnexus-bridge --no-pager
echo "Bridge online as $DEVICE_NAME"