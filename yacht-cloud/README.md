# Yacht Cloud API

Backend API for Yacht mobile:

- JWT auth (register/login/refresh) + optional dev bootstrap endpoint
- free-tier quota enforcement
- remote Docker execution endpoints
- Stripe subscription checkout + webhook tier upgrades

## Run

```bash
cd yacht-cloud
python3 -m venv .venv
. .venv/bin/activate
pip install -e .
cp .env.example .env
uvicorn yacht_cloud.main:app --reload --port 8090
```

## Important

- Use `DATABASE_URL` for Postgres in production (e.g. `postgresql+psycopg://...`). If unset, `YACHT_DB_PATH` is used for local SQLite.
- Set `STRIPE_SECRET_KEY`, `STRIPE_WEBHOOK_SECRET`, and `STRIPE_PRICE_PRO_MONTHLY`.
- Set `REMOTE_DOCKER_HOST` (+ optional `REMOTE_DOCKER_TOKEN`) for container execution.
- Set `YACHT_JWT_SECRET` and token TTL env vars.
- Set `YACHT_ENV=prod` to disable `dev-login`.
- Set `RATE_LIMIT_PER_MINUTE=0` if you want to rely on proxy/WAF rate limiting.
- If running behind a proxy, set `TRUST_PROXY_HEADERS=true` to honor `X-Forwarded-For`.
