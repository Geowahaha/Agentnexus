#!/bin/sh
set -e

echo "[entrypoint] Running migrations..."
alembic upgrade head

# Production tuning: use multiple workers if WORKERS env >1
# Note: for heavy async use prefer 1-2 workers + high concurrency. Default 1 for safety.
WORKERS=${WORKERS:-1}
HOST=${HOST:-0.0.0.0}
PORT=${PORT:-8000}

echo "[entrypoint] Starting uvicorn (workers=$WORKERS) on $HOST:$PORT"

if [ "$WORKERS" -gt 1 ]; then
  exec uvicorn app.main:app --host "$HOST" --port "$PORT" --workers "$WORKERS" --proxy-headers --forwarded-allow-ips='*'
else
  exec python run.py
fi