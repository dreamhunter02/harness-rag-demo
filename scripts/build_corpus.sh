#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

UV_BIN="${UV_BIN:-$(command -v uv || true)}"
[[ -n "$UV_BIN" ]] || { echo "uv is required: https://docs.astral.sh/uv/"; exit 1; }

"$UV_BIN" run python -m demo.build_corpus \
  --distractors "${DEMO_DISTRACTOR_COUNT:-20000}" \
  --seed "${DEMO_CORPUS_SEED:-42}"
