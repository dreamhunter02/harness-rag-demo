# Harness-1 Live Search Demo

Presentation demo comparing Harness-1 20B running behind a state-externalizing retrieval harness with a GPT-4o search baseline.

The local laptop hosts the UI, API, retrieval index, and harness state. A team DGX A100 serves only the Harness-1 checkpoint through vLLM.

## Architecture

- **Laptop:** FastAPI, React, the pinned Harness-1 runtime, hybrid Chroma/BM25 retrieval, telemetry, and SSE streaming.
- **Team DGX A100:** only the `pat-jj/harness-1` 20B checkpoint behind vLLM's raw token-ID completion endpoint.
- **OpenAI:** GPT-4o baseline and `text-embedding-3-small` corpus/query vectors.

The UI shows public actions and Harness state changes, never private reasoning or chain-of-thought. Results are labeled **BrowseComp+ Demo Slice** and are not full benchmark scores.

## Local setup

Requirements: Python 3.11+, `uv`, Node.js, `pnpm`, passwordless SSH to `teamdgxa100`, and Git submodules.

```bash
git submodule update --init --recursive
cp .env.example .env.local
# Add credentials and instance configuration to .env.local.
uv sync --group dev
pnpm --dir frontend install --frozen-lockfile
uv run python -m demo.build_corpus --distractors 20000 --seed 42
```

Never commit `.env` or `.env.local`. Start the production UI and API on one local origin with:

```bash
scripts/demo.sh
```

Then open `http://127.0.0.1:8787`. The six checked-in recovery fixtures are deterministic and explicitly labeled as non-live. Each successful live run automatically replaces the corresponding fixture.

## Verification

```bash
uv run ruff check demo tests scripts/generate_seed_replays.py
uv run pytest
pnpm --dir frontend run typecheck
pnpm --dir frontend test
pnpm --dir frontend run build
```

See [PLAN.md](PLAN.md), [DGX setup](docs/DGX.md), and the [event-day runbook](docs/EVENT_DAY.md).

GPT-4o standard token pricing is dated in `.env.example` and was verified on 2026-07-21 against the official model page. Harness cost uses the configured accelerator rate and allocates only measured model-inference time; the UI notes that idle time, warm-up, storage, and other charges are excluded.
