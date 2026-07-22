#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

if [[ -f .env.local ]]; then
  set -a
  # shellcheck disable=SC1091
  source .env.local
  set +a
elif [[ -f .env ]]; then
  set -a
  # shellcheck disable=SC1091
  source .env
  set +a
fi

UV_BIN="${UV_BIN:-$(command -v uv || true)}"
PNPM_BIN="${PNPM_BIN:-$(command -v pnpm || true)}"
[[ -n "$UV_BIN" ]] || { echo "uv is required: https://docs.astral.sh/uv/"; exit 1; }
[[ -n "$PNPM_BIN" ]] || { echo "pnpm is required: https://pnpm.io/installation"; exit 1; }

"$UV_BIN" sync --group dev
"$PNPM_BIN" --dir frontend install --frozen-lockfile
"$PNPM_BIN" --dir frontend run build

TUNNEL_PID=""
cleanup() {
  [[ -z "$TUNNEL_PID" ]] || kill "$TUNNEL_PID" 2>/dev/null || true
}
trap cleanup EXIT INT TERM

if [[ -n "${HARNESS1_REMOTE_HOST:-}" ]] && ! nc -z 127.0.0.1 8001 2>/dev/null; then
  scripts/dgx/tunnel.sh "$HARNESS1_REMOTE_HOST" &
  TUNNEL_PID=$!
fi

"$UV_BIN" run uvicorn demo.main:app --host 127.0.0.1 --port "${DEMO_PORT:-8787}"
