from __future__ import annotations

import time
import uuid
from collections import defaultdict, deque

import stripe
from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse

from .auth import require_user
from .compose_runtime import compose_up_from_yaml
from .config import settings
from .db import (
    create_user_with_password,
    get_user_by_email,
    get_or_create_user,
    init_db,
    set_user_customer,
    set_user_tier_by_customer,
    verify_password,
)
from .quota import enforce_and_record, quota_status
from .remote_exec import RemoteDocker, RemoteDockerError, get_remote
from .schemas import CheckoutRequest, ComposeUpRequest, LoginRequest, PullRequest, RefreshRequest, RegisterRequest, RunRequest
from .tokens import issue_pair_for_user, refresh_tokens

app = FastAPI(title="Yacht Cloud API", version="0.1.0")

stripe.api_key = settings.stripe_secret_key or None
_rate_buckets: dict[str, deque[float]] = defaultdict(deque)


@app.on_event("startup")
def startup() -> None:
    init_db()


def _client_ip(request: Request) -> str:
    if settings.trust_proxy_headers:
        forwarded = request.headers.get("x-forwarded-for")
        if forwarded:
            return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


@app.middleware("http")
async def security_middleware(request: Request, call_next):
    # Simple in-process IP rate limit for API abuse control.
    if settings.rate_limit_per_minute > 0:
        ip = _client_ip(request)
        now = time.time()
        bucket = _rate_buckets[ip]
        while bucket and now - bucket[0] > 60:
            bucket.popleft()
        if len(bucket) >= settings.rate_limit_per_minute:
            return JSONResponse(status_code=429, content={"detail": "rate limit exceeded"})
        bucket.append(now)

    request_id = request.headers.get("x-request-id") or str(uuid.uuid4())
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["X-Request-ID"] = request_id
    if settings.rate_limit_per_minute > 0:
        response.headers["X-RateLimit-Limit-Minute"] = str(settings.rate_limit_per_minute)
        response.headers["X-RateLimit-Remaining"] = str(max(0, settings.rate_limit_per_minute - len(bucket)))
    return response


@app.get("/health")
def health() -> dict:
    return {"ok": True, "env": settings.env}


@app.post("/v1/auth/register")
def register(req: RegisterRequest) -> dict:
    email = req.email.lower()
    if get_user_by_email(email):
        raise HTTPException(status_code=409, detail="email already exists")
    user = create_user_with_password(email, req.password)
    if not user:
        raise HTTPException(status_code=409, detail="email already exists")
    return {"user": {"id": user["id"], "email": user["email"], "tier": user["tier"]}, **issue_pair_for_user(user)}


@app.post("/v1/auth/login")
def login(req: LoginRequest) -> dict:
    user = verify_password(req.email.lower(), req.password)
    if not user:
        raise HTTPException(status_code=401, detail="invalid credentials")
    return {"user": {"id": user["id"], "email": user["email"], "tier": user["tier"]}, **issue_pair_for_user(user)}


@app.post("/v1/auth/refresh")
def refresh(req: RefreshRequest) -> dict:
    pair = refresh_tokens(req.refresh_token)
    if not pair:
        raise HTTPException(status_code=401, detail="invalid refresh token")
    return pair


@app.post("/v1/auth/dev-login")
def dev_login(req: LoginRequest) -> dict:
    # Keep for internal/testing speed; disable in production by policy.
    if settings.env == "prod":
        raise HTTPException(status_code=403, detail="dev-login disabled in prod")
    user = get_or_create_user(req.email.lower())
    return {"user": {"id": user["id"], "email": user["email"], "tier": user["tier"]}, **issue_pair_for_user(user)}


@app.get("/v1/me")
def me(user: dict = Depends(require_user)) -> dict:
    return {"id": user["id"], "email": user["email"], "tier": user["tier"], "quota": quota_status(user)}


@app.get("/v1/remote/status")
def remote_status(user: dict = Depends(require_user)) -> dict:
    _ = user
    remote = RemoteDocker(get_remote())
    try:
        return {"ping": remote.ping(), "host": settings.remote_docker_host}
    except RemoteDockerError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail) from exc


@app.post("/v1/images/pull")
def pull_image(req: PullRequest, user: dict = Depends(require_user)) -> dict:
    enforce_and_record(user, "pull")
    remote = RemoteDocker(get_remote())
    try:
        remote.pull(req.image)
        return {"ok": True, "image": req.image}
    except RemoteDockerError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail) from exc


@app.post("/v1/containers/run")
def run_container(req: RunRequest, user: dict = Depends(require_user)) -> dict:
    enforce_and_record(user, "run")
    remote = RemoteDocker(get_remote())
    try:
        cid = remote.run(req.image, req.command, req.env)
        return {"ok": True, "container_id": cid, "image": req.image}
    except RemoteDockerError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail) from exc


@app.post("/v1/compose/up")
def compose_up(req: ComposeUpRequest, user: dict = Depends(require_user)) -> dict:
    enforce_and_record(user, "compose_up")
    remote = RemoteDocker(get_remote())
    try:
        started = compose_up_from_yaml(remote, req.compose_yaml)
        return {"ok": True, "count": len(started), "started": started}
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RemoteDockerError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail) from exc


@app.get("/v1/quota")
def quota(user: dict = Depends(require_user)) -> dict:
    return quota_status(user)


@app.post("/v1/billing/checkout-session")
def checkout(req: CheckoutRequest | None = None, user: dict = Depends(require_user)) -> dict:
    if not settings.stripe_secret_key or not settings.stripe_price_pro_monthly:
        raise HTTPException(status_code=400, detail="stripe is not configured")

    customer = user.get("stripe_customer_id")
    if not customer:
        c = stripe.Customer.create(email=user["email"], metadata={"user_id": user["id"]})
        customer = c["id"]
        set_user_customer(user["id"], customer)

    try:
        session = stripe.checkout.Session.create(
            mode="subscription",
            customer=customer,
            line_items=[{"price": settings.stripe_price_pro_monthly, "quantity": 1}],
            success_url=(req.return_url if req else None) or settings.stripe_success_url,
            cancel_url=settings.stripe_cancel_url,
        )
        return {"url": session["url"], "id": session["id"]}
    except Exception as exc:  # pragma: no cover
        raise HTTPException(status_code=502, detail=f"stripe error: {exc}") from exc


@app.post("/v1/billing/webhook")
async def stripe_webhook(request: Request) -> JSONResponse:
    if not settings.stripe_webhook_secret:
        raise HTTPException(status_code=400, detail="webhook secret missing")
    payload = await request.body()
    sig = request.headers.get("stripe-signature", "")
    try:
        event = stripe.Webhook.construct_event(payload, sig, settings.stripe_webhook_secret)
    except Exception as exc:  # pragma: no cover
        raise HTTPException(status_code=400, detail=f"invalid webhook: {exc}") from exc

    typ = event.get("type", "")
    obj = event.get("data", {}).get("object", {})
    if typ == "checkout.session.completed":
        customer = obj.get("customer")
        subscription_id = obj.get("subscription")
        if customer:
            set_user_tier_by_customer(customer, "pro", subscription_id)
    elif typ in ("customer.subscription.deleted", "customer.subscription.paused"):
        customer = obj.get("customer")
        if customer:
            set_user_tier_by_customer(customer, "free", None)

    return JSONResponse({"received": True, "type": typ})


@app.get("/v1/billing/config")
def billing_config(user: dict = Depends(require_user)) -> dict:
    _ = user
    return {
        "enabled": bool(settings.stripe_secret_key and settings.stripe_price_pro_monthly),
        "price_id": settings.stripe_price_pro_monthly,
    }


@app.exception_handler(Exception)
async def unhandled_exception(_: Request, exc: Exception) -> JSONResponse:
    payload = {"detail": "internal error"}
    if settings.env != "prod":
        payload["error"] = str(exc)
    return JSONResponse(status_code=500, content=payload)
