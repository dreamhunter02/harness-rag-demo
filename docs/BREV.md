# Brev model serving

Only the Harness-1 checkpoint and vLLM run on Brev. Retrieval, harness state, API, and UI remain on the presentation laptop.

## Prerequisites

1. Install and authenticate Brev: `/opt/homebrew/bin/brev login`.
2. Confirm an existing 80 GB GPU instance or review the current price before creating one.
3. If Hugging Face later gates the public checkpoint, authenticate on the instance interactively; never put tokens in command arguments or Git.

## Deploy

```bash
export BREV_INSTANCE_NAME=harness-1-demo
./scripts/brev/deploy.sh
```

The script refuses to create a paid instance. If no matching instance exists, it prints the explicit `brev create` command and expected price.

## Connect

```bash
./scripts/brev/tunnel.sh
./scripts/brev/health.sh
```

The tunnel exposes Brev's loopback-only port 8000 as local port 8001 and reconnects after transient disconnects.
