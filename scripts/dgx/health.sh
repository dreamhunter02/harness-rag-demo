#!/usr/bin/env bash
set -euo pipefail

REMOTE_HOST="${1:-${HARNESS1_REMOTE_HOST:-teamdgxa100}}"

ssh "$REMOTE_HOST" 'docker ps --filter name=harness1-vllm --format "{{.Status}}"; curl --fail --silent --show-error http://127.0.0.1:8000/health; nvidia-smi --query-gpu=index,name,memory.used,memory.free,utilization.gpu --format=csv,noheader | tail -1'
echo "Harness-1 is ready on $REMOTE_HOST."
