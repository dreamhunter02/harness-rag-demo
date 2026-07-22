#!/usr/bin/env bash
set -euo pipefail

# shellcheck source=common.sh
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/common.sh"

require_env HARNESS1_REMOTE_HOST
require_env HARNESS1_GPU_DEVICE
require_env HARNESS1_REMOTE_ROOT

REMOTE_HOST="$HARNESS1_REMOTE_HOST"
GPU_DEVICE="$HARNESS1_GPU_DEVICE"
IMAGE="${HARNESS1_VLLM_IMAGE:-vllm/vllm-openai:v0.13.0}"
MODEL="${HARNESS1_HF_MODEL:-pat-jj/harness-1}"
REMOTE_ROOT="$HARNESS1_REMOTE_ROOT"
CONTAINER_NAME="${HARNESS1_CONTAINER_NAME:-harness1-vllm}"
REMOTE_PORT="${HARNESS1_REMOTE_PORT:-8000}"

ssh "$REMOTE_HOST" bash -s -- "$GPU_DEVICE" "$IMAGE" "$MODEL" "$REMOTE_ROOT" "$CONTAINER_NAME" "$REMOTE_PORT" <<'REMOTE'
set -euo pipefail
GPU_DEVICE="$1"
IMAGE="$2"
MODEL="$3"
REMOTE_ROOT="$4"
CONTAINER_NAME="$5"
REMOTE_PORT="$6"

mkdir -p "$REMOTE_ROOT/hf-cache" "$REMOTE_ROOT/logs"
if docker container inspect "$CONTAINER_NAME" >/dev/null 2>&1; then
  docker rm -f "$CONTAINER_NAME" >/dev/null
fi
docker run -d \
  --name "$CONTAINER_NAME" \
  --restart on-failure:3 \
  --gpus "device=$GPU_DEVICE" \
  -e HF_HOME=/root/.cache/huggingface \
  -e VLLM_USE_DEEP_GEMM=0 \
  -e VLLM_MOE_USE_DEEP_GEMM=0 \
  -v "$REMOTE_ROOT/hf-cache:/root/.cache/huggingface" \
  -p "127.0.0.1:$REMOTE_PORT:8000" \
  --ipc=host \
  "$IMAGE" "$MODEL" \
  --served-model-name harness-1 \
  --host 0.0.0.0 \
  --port 8000 \
  --tensor-parallel-size 1 \
  --max-model-len 32768 \
  --max-num-batched-tokens 16384 \
  --trust-remote-code
REMOTE

echo "Harness-1 deployment started on the configured remote host. Run scripts/remote/health.sh to monitor it."
