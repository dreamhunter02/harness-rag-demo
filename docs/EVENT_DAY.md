# Event-day runbook

## Before travel

1. Copy `.env.example` to `.env.local` and set the frontier, optional embedding, and remote-inference variables for the target environment.
2. Verify passwordless access with `ssh -o BatchMode=yes "$HARNESS1_REMOTE_HOST" hostname` after loading `.env.local`.
3. Build the local slice: `uv run python -m demo.build_corpus --distractors 20000 --seed 42`.
4. Start the remote vLLM service with `scripts/remote/deploy.sh` and verify `scripts/remote/health.sh`.
5. Start the full local demo with `scripts/demo.sh`, then open `http://127.0.0.1:8787`.
6. Run `uv run python scripts/prevalidate_demo.py --rounds 2`. It waits for Harness readiness, retries transient provider failures, and requires both questions to pass twice on both systems with no more than 12 actions.
7. Successful runs replace their matching replay JSONL files. Confirm all four replays carry the persistent `DEMO REPLAY` marker.

## Thirty minutes before the talk

- Connect power and disable sleep, notifications, VPN switching, and automatic OS updates.
- Confirm network access, start the remote tunnel, and leave one terminal showing health output.
- Prewarm the index with one search and both models with the shortest selected question.
- Confirm the browser is at 100% zoom and the UI fits the projector without scrolling.
- Keep the deck, this runbook, and a second browser tab at `/api/health` open.

## On stage

1. State that this is a disclosed **BrowseComp+ gold-evidence demo slice plus distractors**, not a full benchmark or benchmark score.
2. Select a question and system, then press **Run**.
3. Narrate actions on the left and externalized Harness-1 state on the right.
4. Describe telemetry only after it appears; cost and throughput are measured estimates, not promises.
5. If a live run fails, use **Replay last successful run**. Explicitly call out the persistent replay banner.

## Failure recovery

- **Tunnel or vLLM unavailable:** run `scripts/remote/tunnel.sh` in a separate terminal and `scripts/remote/health.sh`; wait for `/api/health` to show `harness1_vllm.ready: true`, then retry or use replay.
- **Frontier or embedding API error:** verify the corresponding base URL, model, API key, and network access; use the matching replay if recovery would interrupt the talk.
- **Browser stream reconnect:** reload the page and rerun. The API supports event replay after a sequence cursor, and the UI deduplicates sequences.
- **Hung run:** cancel it in the UI. The backend also enforces `RUN_TIMEOUT_SECONDS`.
- **All live services unavailable:** use replay and keep the `DEMO REPLAY · NOT A LIVE MEASUREMENT` label visible.

After the event, run `scripts/remote/stop.sh` if the remote GPU should be released.
