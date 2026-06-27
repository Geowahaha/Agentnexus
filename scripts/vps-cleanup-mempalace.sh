#!/bin/bash
set -euo pipefail
echo "=== DISK BEFORE ==="
df -h /
BEFORE=$(df / --output=avail -B1 | tail -1)

echo "=== STOP & DISABLE: mempalace ==="
systemctl stop mempalace-trader.service 2>/dev/null || true
systemctl disable mempalace-trader.service 2>/dev/null || true
systemctl stop mempalace-hermes-autotune.timer 2>/dev/null || true
systemctl disable mempalace-hermes-autotune.timer 2>/dev/null || true
systemctl stop mempalace-hermes-autotune.service 2>/dev/null || true
systemctl disable mempalace-hermes-autotune.service 2>/dev/null || true

echo "=== STOP & DISABLE: hermes gateways ==="
export XDG_RUNTIME_DIR=/run/user/0
systemctl --user stop hermes-gateway.service 2>/dev/null || true
systemctl --user disable hermes-gateway.service 2>/dev/null || true
AGENT_UID=$(id -u agentuser)
sudo -u agentuser env XDG_RUNTIME_DIR=/run/user/${AGENT_UID} systemctl --user stop hermes-gateway.service 2>/dev/null || true
sudo -u agentuser env XDG_RUNTIME_DIR=/run/user/${AGENT_UID} systemctl --user disable hermes-gateway.service 2>/dev/null || true
pkill -f "hermes_cli.main gateway" 2>/dev/null || true
sleep 1

echo "=== STOP & DISABLE: ollama ==="
systemctl stop ollama.service 2>/dev/null || true
systemctl disable ollama.service 2>/dev/null || true

echo "=== STOP & REMOVE: visibility-engine-api ==="
docker stop visibility-engine-api 2>/dev/null || true
docker rm visibility-engine-api 2>/dev/null || true

echo "=== REMOVE FILES ==="
rm -rf /opt/mempalace_ai
rm -rf /usr/local/lib/hermes-agent
rm -rf /root/.hermes
rm -rf /home/agentuser/.hermes
rm -rf /opt/visibility-engine-api
rm -rf /home/agentuser/.cache
rm -f /etc/systemd/system/mempalace-trader.service
rm -f /etc/systemd/system/mempalace-hermes-autotune.service
rm -f /etc/systemd/system/mempalace-hermes-autotune.timer
rm -f /root/.config/systemd/user/hermes-gateway.service
rm -rf /root/.config/systemd/user/default.target.wants/hermes-gateway.service
rm -f /home/agentuser/.config/systemd/user/hermes-gateway.service
rm -rf /home/agentuser/.config/systemd/user/default.target.wants/hermes-gateway.service
rm -rf /usr/share/ollama/.ollama/models 2>/dev/null || true
rm -rf /var/lib/ollama 2>/dev/null || true

echo "=== DOCKER: remove unused images ==="
docker rmi n8nio/n8n:latest 2>/dev/null || true
docker rmi visibility-engine-api_visibility-engine-api:latest 2>/dev/null || true
docker image prune -f 2>/dev/null || true

systemctl daemon-reload
export XDG_RUNTIME_DIR=/run/user/0
systemctl --user daemon-reload 2>/dev/null || true
sudo -u agentuser env XDG_RUNTIME_DIR=/run/user/${AGENT_UID} systemctl --user daemon-reload 2>/dev/null || true

echo "=== VERIFY ==="
pgrep -af mempalace || echo "no mempalace procs"
pgrep -af hermes_cli || echo "no hermes procs"

echo "=== SERVICE HEALTH ==="
systemctl is-active successcasting-web.service nginx mysql
docker ps --format "{{.Names}}: {{.Status}}" | grep -E "blutenstein|factory-api|n8n"

echo "=== HTTP SMOKE ==="
curl -s -o /dev/null -w "successcasting:%{http_code}\n" -H "Host: www.successcasting.com" http://127.0.0.1/
curl -s -o /dev/null -w "factory-health:%{http_code}\n" http://127.0.0.1:5000/healthz
curl -s -o /dev/null -w "blutenstein:%{http_code}\n" -H "Host: app.blutenstein.com" http://127.0.0.1:8080/

echo "=== DISK AFTER ==="
df -h /
AFTER=$(df / --output=avail -B1 | tail -1)
FREED=$(( (AFTER - BEFORE) / 1024 / 1024 ))
echo "Freed this pass: ${FREED} MB"