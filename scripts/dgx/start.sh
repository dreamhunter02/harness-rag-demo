#!/usr/bin/env bash
set -euo pipefail

REMOTE_HOST="${1:-${HARNESS1_REMOTE_HOST:-teamdgxa100}}"
ssh "$REMOTE_HOST" 'docker start harness1-vllm >/dev/null; docker ps --filter name=harness1-vllm --format "{{.Status}}"'
