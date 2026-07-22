#!/usr/bin/env bash
set -euo pipefail

BREV_BIN="${BREV_BIN:-/opt/homebrew/bin/brev}"
INSTANCE_NAME="${BREV_INSTANCE_NAME:-harness-1-demo}"
LOCAL_PORT="${HARNESS1_LOCAL_PORT:-8001}"
REMOTE_PORT="${HARNESS1_REMOTE_PORT:-8000}"

while true; do
  echo "Forwarding 127.0.0.1:$LOCAL_PORT to $INSTANCE_NAME:127.0.0.1:$REMOTE_PORT"
  "$BREV_BIN" port-forward "$INSTANCE_NAME" -p "$LOCAL_PORT:$REMOTE_PORT" || true
  echo "Tunnel disconnected; retrying in 3 seconds." >&2
  sleep 3
done
