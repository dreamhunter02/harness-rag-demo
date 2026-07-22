#!/usr/bin/env bash
set -euo pipefail

REMOTE_HOST="${1:-${HARNESS1_REMOTE_HOST:-teamdgxa100}}"
ssh "$REMOTE_HOST" 'docker stop harness1-vllm >/dev/null; echo "Harness-1 stopped; checkpoint cache retained."'
