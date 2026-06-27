#!/bin/sh
set -e
mkdir -p /farm-data/mosquitto /mosquitto/data /farm-data/mosquitto/certs
if [ ! -f /farm-data/mosquitto/passwd ]; then
  : > /farm-data/mosquitto/passwd
fi
if [ ! -f /farm-data/mosquitto/acl ]; then
  : > /farm-data/mosquitto/acl
fi
chmod 755 /farm-data/mosquitto
chmod 600 /farm-data/mosquitto/passwd
chmod 600 /farm-data/mosquitto/acl
chown -R mosquitto:mosquitto /farm-data/mosquitto 2>/dev/null || true
if [ -f /mosquitto/certs/server.crt ]; then
  cp /mosquitto/certs/ca.crt /mosquitto/certs/server.crt /mosquitto/certs/server.key /farm-data/mosquitto/certs/
  chown -R mosquitto:mosquitto /farm-data/mosquitto/certs
  chmod 644 /farm-data/mosquitto/certs/ca.crt /farm-data/mosquitto/certs/server.crt
  chmod 640 /farm-data/mosquitto/certs/server.key
elif [ ! -f /farm-data/mosquitto/certs/server.crt ]; then
  echo "WARN: MQTT TLS certs missing — only internal listener may work"
fi
exec /usr/sbin/mosquitto -c /mosquitto/config/mosquitto.conf