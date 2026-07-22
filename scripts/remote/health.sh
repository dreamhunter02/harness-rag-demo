#!/usr/bin/env bash
set -euo pipefail

# shellcheck source=common.sh
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/common.sh"
require_env HARNESS1_REMOTE_HOST
REMOTE_HOST="${1:-$HARNESS1_REMOTE_HOST}"
CONTAINER_NAME="${HARNESS1_CONTAINER_NAME:-harness1-vllm}"
REMOTE_PORT="${HARNESS1_REMOTE_PORT:-8000}"

ssh "$REMOTE_HOST" bash -s -- "$CONTAINER_NAME" "$REMOTE_PORT" <<'REMOTE'
set -euo pipefail
docker ps --filter "name=$1" --format "{{.Status}}"
curl --fail --silent --show-error "http://127.0.0.1:$2/health"
REMOTE
echo "Harness-1 remote inference is ready."
