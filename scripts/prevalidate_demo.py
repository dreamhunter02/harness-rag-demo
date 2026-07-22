#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path


def request_json(url: str, payload: dict | None = None) -> dict | list:
    body = json.dumps(payload).encode() if payload is not None else None
    request = urllib.request.Request(
        url,
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST" if body else "GET",
    )
    with urllib.request.urlopen(request, timeout=10) as response:
        return json.load(response)


def wait_for_run(base_url: str, run_id: str, timeout: int) -> dict:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            record = request_json(f"{base_url}/api/runs/{run_id}")
        except (TimeoutError, urllib.error.URLError):
            time.sleep(1)
            continue
        if record["status"] not in {"queued", "running"}:
            return record
        time.sleep(1)
    raise TimeoutError(f"Run {run_id} did not finish within {timeout}s")


def wait_for_harness(base_url: str, timeout: int) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            health = request_json(f"{base_url}/api/health")
            if health["components"]["harness1_vllm"]["ready"]:
                return
        except (TimeoutError, urllib.error.URLError):
            pass
        time.sleep(2)
    raise TimeoutError("Harness-1 vLLM did not become ready before prevalidation")


def main() -> int:
    parser = argparse.ArgumentParser(description="Prevalidate both live demo systems twice.")
    parser.add_argument("--base-url", default="http://127.0.0.1:8787")
    parser.add_argument("--rounds", type=int, default=2)
    parser.add_argument("--attempts", type=int, default=2)
    parser.add_argument("--timeout", type=int, default=240)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("fixtures/prevalidation.json"),
    )
    args = parser.parse_args()
    questions = request_json(f"{args.base_url}/api/questions")
    results = []
    for round_number in range(1, args.rounds + 1):
        for question in questions:
            for system in ("gpt4o", "harness1"):
                if system == "harness1":
                    wait_for_harness(args.base_url, args.timeout)
                passed = False
                for attempt in range(1, args.attempts + 1):
                    if system == "harness1":
                        wait_for_harness(args.base_url, args.timeout)
                    created = request_json(
                        f"{args.base_url}/api/runs",
                        {
                            "question_id": question["id"],
                            "system": system,
                            "mode": "live",
                        },
                    )
                    record = wait_for_run(args.base_url, created["id"], args.timeout)
                    result = record.get("result") or {}
                    metrics = record.get("metrics") or {}
                    passed = (
                        record["status"] == "completed"
                        and result.get("verified") is True
                        and metrics.get("action_count", 99) <= 12
                    )
                    if passed:
                        break
                row = {
                    "round": round_number,
                    "question_id": question["id"],
                    "system": system,
                    "attempts": attempt,
                    "passed": passed,
                    "status": record["status"],
                    "answer": result.get("answer"),
                    "evidence_document_ids": result.get("evidence_document_ids"),
                    "action_count": metrics.get("action_count"),
                    "total_seconds": metrics.get("total_seconds"),
                    "error": record.get("error"),
                }
                results.append(row)
                print(json.dumps(row), flush=True)
    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "rounds": args.rounds,
        "passed": all(item["passed"] for item in results),
        "results": results,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n")
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
