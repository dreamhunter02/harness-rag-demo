# Remote Harness-1 inference

Only the Harness-1 checkpoint and vLLM run on the remote GPU host. Retrieval, harness state, the API, and the UI remain on the presentation workstation.

## Configuration

Copy `.env.example` to `.env.local` and replace the placeholders. The remote scripts load this ignored file automatically. Set `HARNESS_ENV_FILE=/path/to/another.env` to load a different environment file in CI or automation.

| Variable | Purpose | Required |
| --- | --- | --- |
| `HARNESS1_REMOTE_HOST` | SSH alias or hostname | Yes |
| `HARNESS1_GPU_DEVICE` | GPU index or runtime-supported device identifier | Yes |
| `HARNESS1_REMOTE_ROOT` | Remote cache and log directory | Yes |
| `HARNESS1_VLLM_IMAGE` | vLLM-compatible container image | Default provided |
| `HARNESS1_HF_MODEL` | Model repository or local checkpoint | Default provided |
| `HARNESS1_CONTAINER_NAME` | Remote container name | Default provided |
| `HARNESS1_REMOTE_PORT` | Loopback-only vLLM port on the remote host | Default `8000` |
| `HARNESS1_LOCAL_PORT` | Forwarded port on the workstation | Default `8001` |
| `HARNESS1_BASE_URL` | Local OpenAI-compatible completion URL | Default `http://127.0.0.1:8001/v1` |

Do not put credentials, real hostnames, device assignments, or private paths in tracked files.

## Deploy and connect

```bash
cp .env.example .env.local
# Edit .env.local with your deployment values.

scripts/remote/deploy.sh
scripts/remote/health.sh
scripts/remote/tunnel.sh
```

Run the tunnel in a dedicated terminal. It binds only to local loopback and reconnects after transient SSH failures.

## Validate and operate

```bash
scripts/remote/smoke.sh
scripts/remote/logs.sh
scripts/remote/stop.sh
scripts/remote/start.sh
```

The deployment script replaces only the configured container. The checkpoint cache under `HARNESS1_REMOTE_ROOT` is retained across container restarts.
