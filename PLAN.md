# Harness-1 Live Demo Plan

## Summary

Build a presentation-ready demo in `dreamhunter02/harness-rag-demo` with:

- Harness-1, retrieval, API backend, and React frontend running locally.
- Only the Harness-1 20B checkpoint and vLLM running on Brev.
- GPT‑4o accessed directly through OpenAI as the comparison baseline.
- Three prevalidated questions from a disclosed “BrowseComp+ Demo Slice.”
- Live trajectory/state streaming, defensible latency/token/cost metrics, and an explicitly labeled replay fallback.
- The approved slide-matched UI concept.

The first implementation commit will save this plan unchanged as `PLAN.md`.

## Architecture and implementation

- Clone the empty destination repository at `/Users/vikalluru/Library/CloudStorage/OneDrive-NVIDIACorporation/work/harness-rag-demo`; configure Git as `dreamhunter02 <kssaivineeth@gmail.com>`.
- Add [pat-jj/harness-1](https://github.com/pat-jj/harness-1) as a pinned submodule at commit `8ac4012167858f6478fb2a8fd840e4550e2af161`. Keep all demo-specific changes outside the submodule.
- Use Python 3.11+, FastAPI, React/Vite/TypeScript, pnpm, and Server-Sent Events. Serve the production frontend from FastAPI so the live demo uses one local origin and one startup command.
- Provide:
  - `GET /api/health`
  - `GET /api/questions`
  - `POST /api/runs`
  - `GET /api/runs/{id}`
  - `GET /api/runs/{id}/events`
  - `POST /api/runs/{id}/cancel`
- Accept `system: "harness1" | "gpt4o"` and `mode: "live" | "replay"`. Permit one active live run to prevent accidental concurrent stage executions.
- Normalize every streamed event as `{run_id, sequence, timestamp, type, phase, payload}`. Event types cover run status, tool action, observation summary, state snapshot, metrics, result, and error.
- Stream tool names, parameters, document identifiers, retrieval summaries, and state changes. Never expose raw private reasoning or chain-of-thought.
- Keep run state in memory and write successful event streams as JSONL replay fixtures; do not add a database.

## Models, retrieval, and telemetry

- Deploy only `pat-jj/harness-1` on Brev using the repository-tested vLLM `0.20.2` raw `/v1/completions` path with token-ID input/output.
- Prefer an existing compatible 80 GB GPU. If none exists, select a single H100-class instance, show its exact hourly price before creation, then provision it.
- Bind vLLM to the remote loopback interface and connect through an auto-reconnecting SSH/Brev port-forward:
  - Brev: `127.0.0.1:8000`
  - Laptop: `127.0.0.1:8001`
  - Local configuration: `HARNESS1_BASE_URL=http://127.0.0.1:8001/v1`
- Reuse `SlidingWindowSearchEnv`, the vLLM token completer, search/read/grep tools, evidence curation, verification, compression, and working-memory structures. Add callbacks around each environment step to emit UI events and snapshots.
- Build a deterministic local BrowseComp+ slice from the [published Harness-1 corpus](https://huggingface.co/datasets/pat-jj/harness-1-train-data):
  - Start from 12 public BrowseComp+ SFT trajectories.
  - Include their gold/evidence documents and every document touched in their published trajectories.
  - Add 20,000 deterministic distractor chunks using seed `42`.
  - Generate `text-embedding-3-small` dense vectors and matching BM25 vectors, then create a persistent local Chroma collection.
  - Label all UI and documentation results “BrowseComp+ Demo Slice”; never present them as full benchmark scores.
- Disable the optional Baseten/vLLM reranker for v1 to avoid another hosted service.
- Prevalidate candidate questions twice on both systems. Select the three with no errors, completion under two minutes, concise verifiable answers, and at least four distinct visible Harness-1 state transitions; rank passing questions by median completion time.
- Run GPT‑4o through OpenAI with the same local search/read access, a bounded eight-turn tool loop, and no Harness-1 state machine. When GPT‑4o is selected, the six state cells remain visibly inactive with “State remains inside the model context.”
- Capture:
  - Total wall time
  - Time to first completed action
  - Cumulative model inference time
  - Retrieval/tool time
  - Prompt and completion tokens
  - Completion tokens per model-inference second
  - Tool/action count
  - GPT‑4o estimated API cost
  - Harness estimated allocated GPU cost
- Store pricing as dated configuration, sourced from the current official provider prices. Label cost as estimated and explain that Brev allocation excludes idle, warm-up, and storage charges.

## Frontend, operations, and delivery

- Implement the approved 16:9 concept using the deck’s warm off-white background, black editorial typography, NVIDIA green accent, thin rules, restrained corners, and minimal shadows.
- Preserve the approved layout: question/system controls, Run button, left action trajectory, right six-cell state area, and bottom result/metrics strip.
- Correct the illustrative concept’s metric labels in code and add completed, error, disconnected, cancelled, and replay states.
- Optimize for 1920×1080 and verify 1440×900 and 1366×768 projector/laptop layouts.
- Default to live execution. Never silently switch to replay; on failure, offer “Replay last successful run” and display a persistent “DEMO REPLAY” marker.
- Add:
  - Model/index prewarming
  - Health/readiness checks
  - Tunnel reconnection
  - Run cancellation and timeout handling
  - Captured replay fixtures for all six question/system combinations
  - One-command `demo` startup
  - Setup documentation and an event-day runbook
- Keep credentials exclusively in ignored local environment files. Required variables include `OPENAI_API_KEY`, `NVIDIA_API_KEY`, optional Hugging Face credentials, and Brev/runtime configuration.
- Copy the approved concept into repository documentation during implementation and perform final concept-to-browser screenshot comparison.

## Testing, acceptance, and commits

- Unit-test event ordering, state serialization, metric aggregation, cost calculations, corpus construction, cancellation, and redaction of reasoning fields.
- Contract-test all API endpoints and SSE reconnect behavior.
- Component-test dropdowns, run states, trajectory updates, Harness state snapshots, GPT‑4o inactive-state treatment, errors, and replay labeling.
- Run browser end-to-end tests with deterministic fixtures, followed by live smoke tests for all three questions on both systems.
- Simulate tunnel loss, vLLM timeout, OpenAI failure, browser reconnect, and replay recovery.
- Require secret scanning, Python tests/lint, TypeScript checks, frontend tests, production build, and visual inspection before delivery.
- Push milestone commits to `git@github.com:dreamhunter02/harness-rag-demo.git` after:
  1. Plan, scaffold, submodule, and configuration
  2. Local corpus and Harness-1 runner
  3. Brev vLLM deployment and tunnel
  4. GPT‑4o baseline and telemetry
  5. Frontend and streaming integration
  6. Replay resilience, tests, and event-day runbook

## Assumptions

- GPT‑4o will use an OpenAI API key supplied locally; no OpenAI credential is currently detected.
- The NVIDIA API key is retained for supporting NVIDIA services but is not used for GPT‑4o.
- The curated corpus is intentionally optimized for a reliable live explanation, not benchmark reproduction.
- SSH port forwarding is the primary Brev connection; no public inference endpoint is required.
- The demo compares system behavior and efficiency without promising that Harness-1 will be faster, cheaper, or more accurate before measurement.
