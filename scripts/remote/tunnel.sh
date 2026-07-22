#!/usr/bin/env bash
set -euo pipefail

# shellcheck source=common.sh
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/common.sh"
require_env HARNESS1_REMOTE_HOST
REMOTE_HOST="${1:-$HARNESS1_REMOTE_HOST}"
LOCAL_PORT="${HARNESS1_LOCAL_PORT:-8001}"
REMOTE_PORT="${HARNESS1_REMOTE_PORT:-8000}"

while true; do
  echo "Forwarding local port $LOCAL_PORT to the configured remote inference service."
  ssh -N \
    -o ExitOnForwardFailure=yes \
    -o ServerAliveInterval=20 \
    -o ServerAliveCountMax=3 \
    -L "127.0.0.1:$LOCAL_PORT:127.0.0.1:$REMOTE_PORT" \
    "$REMOTE_HOST" || true
  echo "Tunnel disconnected; retrying in 2 seconds."
  sleep 2
done
