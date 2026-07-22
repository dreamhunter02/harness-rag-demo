#!/usr/bin/env bash
set -euo pipefail

REMOTE_HOST="${1:-${HARNESS1_REMOTE_HOST:-teamdgxa100}}"
LOCAL_PORT="${HARNESS1_LOCAL_PORT:-8001}"

while true; do
  echo "Forwarding 127.0.0.1:$LOCAL_PORT to $REMOTE_HOST:8000"
  ssh -N \
    -o ExitOnForwardFailure=yes \
    -o ServerAliveInterval=20 \
    -o ServerAliveCountMax=3 \
    -L "127.0.0.1:$LOCAL_PORT:127.0.0.1:8000" \
    "$REMOTE_HOST" || true
  echo "Tunnel disconnected; retrying in 2 seconds."
  sleep 2
done
