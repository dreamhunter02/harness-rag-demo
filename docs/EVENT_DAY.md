# Event-day runbook

## Before travel

1. Copy `.env.example` to `.env.local` and set `OPENAI_API_KEY`, `BREV_INSTANCE_NAME`, and the exact `BREV_HOURLY_USD` shown by Brev.
2. Authenticate once with `brev login` and verify SSH access.
3. Build the local slice: `uv run python -m demo.build_corpus --distractors 20000 --seed 42`.
4. Start the Brev vLLM service with `scripts/brev/deploy.sh <instance-name>` and verify `scripts/brev/health.sh`.
5. Start the full local demo with `scripts/demo.sh`, then open `http://127.0.0.1:8787`.
6. Run all three questions on both systems. Successful runs replace their matching replay JSONL files. Confirm each replay carries the persistent `DEMO REPLAY` marker.

## Thirty minutes before the talk

- Connect power and disable sleep, notifications, VPN switching, and automatic OS updates.
- Use the presentation network, start the Brev tunnel, and leave one terminal showing health output.
- Prewarm the index with one search and both models with the shortest selected question.
- Confirm the browser is at 100% zoom and the UI fits the projector without scrolling.
- Keep the deck, this runbook, and a second browser tab at `/api/health` open.

## On stage

1. State that this is the disclosed **BrowseComp+ Demo Slice**, not a full benchmark.
2. Select a question and system, then press **Run**.
3. Narrate actions on the left and externalized Harness-1 state on the right.
4. Describe telemetry only after it appears; cost and throughput are measured estimates, not promises.
5. If a live run fails, use **Replay last successful run**. Explicitly call out the persistent replay banner.

## Failure recovery

- **Tunnel or vLLM unavailable:** run `scripts/brev/tunnel.sh <instance-name>` in a separate terminal and `scripts/brev/health.sh`; then retry or use replay.
- **OpenAI error:** verify `OPENAI_API_KEY` and network access; use the matching replay if recovery would interrupt the talk.
- **Browser stream reconnect:** reload the page and rerun. The API supports event replay after a sequence cursor, and the UI deduplicates sequences.
- **Hung run:** cancel it in the UI. The backend also enforces `RUN_TIMEOUT_SECONDS`.
- **All live services unavailable:** use replay and keep the `DEMO REPLAY · NOT A LIVE MEASUREMENT` label visible.

After the event, stop the Brev workload/instance promptly and verify billing status.
