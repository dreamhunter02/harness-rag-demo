#!/usr/bin/env bash
set -euo pipefail

BASE_URL="${HARNESS1_BASE_URL:-http://127.0.0.1:8001/v1}"
ROOT_URL="${BASE_URL%/v1}"

curl --fail --silent --show-error "$ROOT_URL/health" >/dev/null
python3 - "$BASE_URL" <<'PY'
import json
import sys
import urllib.request

base = sys.argv[1].rstrip("/")
payload = {
    "model": "harness-1",
    "prompt": "Say OK.",
    "max_tokens": 4,
    "temperature": 0.0,
    "stream": False,
    "return_token_ids": True,
}
request = urllib.request.Request(
    f"{base}/completions",
    data=json.dumps(payload).encode(),
    headers={"Content-Type": "application/json"},
    method="POST",
)
with urllib.request.urlopen(request, timeout=120) as response:
    data = json.load(response)
choice = data["choices"][0]
tokens = choice.get("token_ids") or choice.get("tokens") or choice.get("text_token_ids")
if not tokens:
    raise SystemExit("vLLM returned text but no generated token IDs")
print("Harness-1 vLLM ready; generated token IDs:", len(tokens))
PY
