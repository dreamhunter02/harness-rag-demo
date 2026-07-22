#!/usr/bin/env bash
set -euo pipefail

# shellcheck source=common.sh
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/common.sh"
BASE_URL="${HARNESS1_BASE_URL:-http://127.0.0.1:8001/v1}"
python3 - "$BASE_URL" <<'PY'
import json
import sys
import time
import urllib.request

base_url = sys.argv[1].rstrip("/")
payload = {
    "model": "harness-1",
    "prompt": "Say OK.",
    "max_tokens": 4,
    "temperature": 0.0,
    "stream": False,
    "return_token_ids": True,
}
request = urllib.request.Request(
    f"{base_url}/completions",
    data=json.dumps(payload).encode(),
    headers={"Content-Type": "application/json"},
    method="POST",
)
started = time.perf_counter()
with urllib.request.urlopen(request, timeout=180) as response:
    result = json.load(response)
choice = result["choices"][0]
token_ids = choice.get("token_ids")
if not token_ids:
    raise SystemExit("Smoke test failed: response omitted generated token IDs")
print(
    json.dumps(
        {
            "ready": True,
            "latency_seconds": round(time.perf_counter() - started, 3),
            "generated_token_ids": token_ids,
            "usage": result.get("usage"),
        },
        indent=2,
    )
)
PY
