#!/usr/bin/env bash
# Generate self-signed MQTT TLS certs on VPS (idempotent).
set -euo pipefail
cd /opt/agentnexus/mosquitto/certs 2>/dev/null || cd "$(dirname "$0")/../backend/mosquitto/certs"
mkdir -p .
if [[ -f server.crt && -f server.key && -f ca.crt ]]; then
  echo "MQTT TLS certs already exist"
  exit 0
fi
openssl req -new -x509 -days 825 -extensions v3_ca -keyout ca.key -out ca.crt -nodes \
  -subj "/CN=OBOLLA Smart Farm MQTT CA"
openssl req -new -nodes -out server.csr -keyout server.key \
  -subj "/CN=43.128.75.149"
openssl x509 -req -in server.csr -CA ca.crt -CAkey ca.key -CAcreateserial -out server.crt -days 825
chmod 644 ca.crt server.crt
chmod 600 server.key ca.key
rm -f server.csr
echo "MQTT TLS certs generated in $(pwd)"