#!/usr/bin/env bash
set -euo pipefail

# shellcheck source=common.sh
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/common.sh"
require_env HARNESS1_REMOTE_HOST
REMOTE_HOST="${1:-$HARNESS1_REMOTE_HOST}"
CONTAINER_NAME="${HARNESS1_CONTAINER_NAME:-harness1-vllm}"
ssh "$REMOTE_HOST" docker stop "$CONTAINER_NAME" >/dev/null
echo "Harness-1 stopped; checkpoint cache retained."
