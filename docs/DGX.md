# Team DGX A100 deployment

Harness‑1 runs on `teamdgxa100` inside a Docker container named
`harness1-vllm`. The service uses one A100 80GB and remains bound to the remote
loopback interface. The laptop reaches it only through an SSH tunnel.

## Current placement

- SSH alias: `teamdgxa100`
- vLLM image: `vllm/vllm-openai:v0.13.0` (Harness‑1's documented minimum)
- Model: `pat-jj/harness-1`
- GPU UUID: `GPU-d59ff461-e13a-bca4-e6df-a61f4ee95331`
- Remote endpoint: `127.0.0.1:8000`
- Local endpoint: `127.0.0.1:8001`
- Persistent cache: `/raid/home/vikalluru/harness-rag-demo/hf-cache`

The root filesystem is full, so all persistent model data must stay under
`/raid`. Do not move the cache into `$HOME/.cache` on the root filesystem.

## Operations

```bash
scripts/dgx/deploy.sh
scripts/dgx/health.sh
scripts/dgx/tunnel.sh
```

The deploy script replaces only the `harness1-vllm` container. Before deploying,
confirm the configured GPU is still free with `nvidia-smi` and never select GPUs
occupied by another user's process.

To inspect logs:

```bash
ssh teamdgxa100 docker logs --tail 100 -f harness1-vllm
```

To stop the service without deleting its checkpoint cache:

```bash
ssh teamdgxa100 docker stop harness1-vllm
```
