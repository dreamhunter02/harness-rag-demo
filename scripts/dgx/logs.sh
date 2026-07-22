#!/usr/bin/env bash
set -euo pipefail

REMOTE_HOST="${1:-${HARNESS1_REMOTE_HOST:-teamdgxa100}}"
LINES="${HARNESS1_LOG_LINES:-100}"
ssh "$REMOTE_HOST" docker logs --tail "$LINES" -f harness1-vllm
