# Yacht Mobile MVP

`yacht` is a Docker-compatible-leaning mobile runtime shim with three execution intents:

- local: rootless `proot` execution when image profile is compatible
- remote: explicit offload recommendation for incompatible workloads
- auto: choose local or remote recommendation from hydration score

This MVP includes:

- OCI/Docker registry `pull`
- local metadata `inspect`
- compatibility `hydrate`
- guarded `run` with optional local `proot`
- remote Docker API connection (`remote connect`, `remote status`)
- Compose subset (`compose up`)

## Quickstart

```bash
cd yacht-mobile
python3 -m venv .venv
. .venv/bin/activate
pip install -e .
yacht pull alpine:3.19
yacht inspect alpine:3.19
yacht hydrate alpine:3.19
yacht run alpine:3.19 -- echo hello
yacht remote connect --host https://docker.example.com --token <token>
yacht compose up -f docker-compose.yml
```

## Notes

- Local execution requires `proot` in `PATH`.
- If compatibility is low, Yacht prints a remote-offload recommendation.
- Cache directory: `~/.yacht/`
- Remote mode uses Docker Engine HTTP API (`v1.43` by default).
