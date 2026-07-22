#!/usr/bin/env bash
set -euo pipefail

REMOTE_HOST="${HARNESS1_REMOTE_HOST:-teamdgxa100}"
GPU_UUID="${HARNESS1_GPU_UUID:-GPU-d59ff461-e13a-bca4-e6df-a61f4ee95331}"
IMAGE="${HARNESS1_VLLM_IMAGE:-vllm/vllm-openai:v0.13.0}"
MODEL="${HARNESS1_HF_MODEL:-pat-jj/harness-1}"
REMOTE_ROOT="${HARNESS1_REMOTE_ROOT:-/raid/home/vikalluru/harness-rag-demo}"

ssh "$REMOTE_HOST" bash -s -- "$GPU_UUID" "$IMAGE" "$MODEL" "$REMOTE_ROOT" <<'REMOTE'
set -euo pipefail
GPU_UUID="$1"
IMAGE="$2"
MODEL="$3"
REMOTE_ROOT="$4"

mkdir -p "$REMOTE_ROOT/hf-cache" "$REMOTE_ROOT/logs"
if ! docker container inspect harness1-vllm >/dev/null 2>&1 && \
   nvidia-smi --query-compute-apps=gpu_uuid --format=csv,noheader | grep -Fxq "$GPU_UUID"; then
  echo "Configured GPU $GPU_UUID is already occupied; refusing to deploy." >&2
  exit 2
fi
if docker container inspect harness1-vllm >/dev/null 2>&1; then
  docker rm -f harness1-vllm >/dev/null
fi
docker run -d \
  --name harness1-vllm \
  --restart on-failure:3 \
  --runtime nvidia \
  -e "NVIDIA_VISIBLE_DEVICES=$GPU_UUID" \
  -e HF_HOME=/root/.cache/huggingface \
  -e VLLM_USE_DEEP_GEMM=0 \
  -e VLLM_MOE_USE_DEEP_GEMM=0 \
  -v "$REMOTE_ROOT/hf-cache:/root/.cache/huggingface" \
  -p 127.0.0.1:8000:8000 \
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

echo "Harness-1 deployment started on $REMOTE_HOST. Run scripts/dgx/health.sh to monitor it."
