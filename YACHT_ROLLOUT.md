# Yacht Rollout Plan (Android + Stripe)

## 1) Bring up backend

```bash
cd yacht-cloud
python3 -m venv .venv
. .venv/bin/activate
pip install -e .
cp .env.example .env
uvicorn yacht_cloud.main:app --host 0.0.0.0 --port 8090
```

Set production values in `.env`:

- `REMOTE_DOCKER_HOST`
- `REMOTE_DOCKER_TOKEN` (optional)
- `STRIPE_SECRET_KEY`
- `STRIPE_WEBHOOK_SECRET`
- `STRIPE_PRICE_PRO_MONTHLY`
- `STRIPE_SUCCESS_URL`
- `STRIPE_CANCEL_URL`
- `YACHT_ENV=prod`
- `YACHT_JWT_SECRET` (strong random value)
- `ACCESS_TOKEN_MINUTES`
- `REFRESH_TOKEN_DAYS`
- `RATE_LIMIT_PER_MINUTE`

## 2) Stripe wiring

1. Create product + recurring monthly price in Stripe.
2. Set `STRIPE_PRICE_PRO_MONTHLY`.
3. Add webhook endpoint:
   - URL: `https://<api-domain>/v1/billing/webhook`
   - Events: `checkout.session.completed`, `customer.subscription.deleted`, `customer.subscription.paused`
4. Copy webhook secret to `STRIPE_WEBHOOK_SECRET`.

## 3) Free limit system

Configured by env:

- `FREE_RUNS_PER_DAY`
- `FREE_PULLS_PER_DAY`
- `FREE_COMPOSE_UP_PER_DAY`

Free users receive HTTP `402` when limits are hit.
Pro users are unlimited.

## 4) Android app

1. Point `API_BASE_URL` to production backend.
2. Copy `yacht-android/keystore.properties.example` to `keystore.properties` and fill signing secrets.
2. Build signed AAB:
   - `./gradlew bundleRelease`
3. Upload to Play Console internal testing first.
4. Validate:
   - login
   - quota decrement
   - limit hit paywall behavior
   - Stripe checkout and webhook-driven tier upgrade

## 5) Security hardening before public launch

1. Keep `YACHT_ENV=prod` so `dev-login` is disabled.
   - Use `/v1/auth/register`, `/v1/auth/login`, `/v1/auth/refresh` in clients.
2. Rotate `YACHT_JWT_SECRET` regularly and enforce refresh-token revocation on logout.
3. Restrict backend CORS, add reverse-proxy WAF/rate limiting, and TLS-only ingress.
4. Put remote Docker host behind private network/VPN or strong auth proxy.
5. Add audit logging and abuse detection.
