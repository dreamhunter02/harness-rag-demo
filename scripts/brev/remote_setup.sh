#!/usr/bin/env bash
set -euo pipefail

MODEL_ID="${HARNESS1_HF_MODEL:-pat-jj/harness-1}"
APP_DIR="${HARNESS1_REMOTE_DIR:-$PWD/harness-1-serving}"

if ! command -v nvidia-smi >/dev/null 2>&1; then
  echo "A CUDA-capable NVIDIA GPU is required." >&2
  exit 1
fi
nvidia-smi

if ! command -v uv >/dev/null 2>&1; then
  curl -LsSf https://astral.sh/uv/install.sh | sh
  export PATH="$HOME/.local/bin:$PATH"
fi

if [[ ! -d "$APP_DIR/.git" ]]; then
  git clone https://github.com/pat-jj/harness-1.git "$APP_DIR"
fi
git -C "$APP_DIR" fetch --all --prune
git -C "$APP_DIR" checkout 8ac4012167858f6478fb2a8fd840e4550e2af161

cd "$APP_DIR"
uv sync --extra vllm

mkdir -p logs
if [[ -f run/vllm.pid ]] && kill -0 "$(cat run/vllm.pid)" 2>/dev/null; then
  echo "vLLM is already running with PID $(cat run/vllm.pid)"
  exit 0
fi
mkdir -p run

export HARNESS1_HF_MODEL="$MODEL_ID"
export VLLM_USE_DEEP_GEMM=0
export VLLM_MOE_USE_DEEP_GEMM=0

nohup uv run --with 'vllm==0.20.2' vllm serve "$HARNESS1_HF_MODEL" \
  --served-model-name harness-1 \
  --host 127.0.0.1 \
  --port 8000 \
  --tensor-parallel-size 1 \
  --max-model-len 32768 \
  --max-num-batched-tokens 16384 \
  --trust-remote-code \
  --moe-backend triton \
  >logs/vllm.log 2>&1 &
echo $! >run/vllm.pid
echo "Started vLLM with PID $(cat run/vllm.pid). Follow $APP_DIR/logs/vllm.log."
