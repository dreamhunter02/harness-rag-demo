# Event-day runbook

## Before travel

1. Copy `.env.example` to `.env.local`, set `FRONTIER_API_KEY` and `EMBEDDING_API_KEY`, and retain `HARNESS1_REMOTE_HOST=teamdgxa100`.
2. Verify passwordless access with `ssh -o BatchMode=yes teamdgxa100 hostname`.
3. Build the local slice: `uv run python -m demo.build_corpus --distractors 20000 --seed 42`.
4. Start the DGX vLLM service with `scripts/dgx/deploy.sh` and verify `scripts/dgx/health.sh`.
5. Start the full local demo with `scripts/demo.sh`, then open `http://127.0.0.1:8787`.
6. Run `uv run python scripts/prevalidate_demo.py --rounds 2`. It waits for Harness readiness, retries transient provider failures, and requires both questions to pass twice on both systems with no more than 12 actions.
7. Successful runs replace their matching replay JSONL files. Confirm all four replays carry the persistent `DEMO REPLAY` marker.

## Thirty minutes before the talk

- Connect power and disable sleep, notifications, VPN switching, and automatic OS updates.
- Use the NVIDIA network, start the DGX tunnel, and leave one terminal showing health output.
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

- **Tunnel or vLLM unavailable:** run `scripts/dgx/tunnel.sh` in a separate terminal and `scripts/dgx/health.sh`; wait for `/api/health` to show `harness1_vllm.ready: true`, then retry or use replay.
- **Inference Hub error:** verify `FRONTIER_API_KEY`, `EMBEDDING_API_KEY`, and network access; use the matching replay if recovery would interrupt the talk.
- **Browser stream reconnect:** reload the page and rerun. The API supports event replay after a sequence cursor, and the UI deduplicates sequences.
- **Hung run:** cancel it in the UI. The backend also enforces `RUN_TIMEOUT_SECONDS`.
- **All live services unavailable:** use replay and keep the `DEMO REPLAY · NOT A LIVE MEASUREMENT` label visible.

After the event, stop `harness1-vllm` if the shared GPU is needed by another user.
