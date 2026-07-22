#!/usr/bin/env bash
set -euo pipefail

# shellcheck source=common.sh
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/common.sh"
require_env HARNESS1_REMOTE_HOST
REMOTE_HOST="${1:-$HARNESS1_REMOTE_HOST}"
LINES="${HARNESS1_LOG_LINES:-100}"
CONTAINER_NAME="${HARNESS1_CONTAINER_NAME:-harness1-vllm}"
ssh "$REMOTE_HOST" docker logs --tail "$LINES" -f "$CONTAINER_NAME"
