from __future__ import annotations

import hashlib
import secrets
from datetime import datetime, timedelta, timezone

import jwt

from .config import settings
from .db import (
    find_valid_refresh_token,
    get_user_by_id,
    revoke_refresh_token,
    store_refresh_token,
)


def _now() -> datetime:
    return datetime.now(timezone.utc)


def mint_access_token(user_id: str, email: str, tier: str) -> str:
    exp = _now() + timedelta(minutes=settings.access_token_minutes)
    payload = {"sub": user_id, "email": email, "tier": tier, "type": "access", "exp": exp}
    return jwt.encode(payload, settings.jwt_secret, algorithm="HS256")


def _refresh_hash(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def mint_refresh_token(user_id: str) -> str:
    raw = f"yr_{secrets.token_urlsafe(48)}"
    expires_at = (_now() + timedelta(days=settings.refresh_token_days)).replace(microsecond=0)
    store_refresh_token(user_id, _refresh_hash(raw), expires_at)
    return raw


def parse_access_token(token: str) -> dict | None:
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=["HS256"])
    except Exception:
        return None
    if payload.get("type") != "access":
        return None
    return payload


def refresh_tokens(refresh_token: str) -> dict | None:
    row = find_valid_refresh_token(_refresh_hash(refresh_token))
    if not row:
        return None
    revoke_refresh_token(_refresh_hash(refresh_token))
    user_id = row["user_id"]
    user = get_user_by_id(user_id)
    if not user:
        return None
    return {
        "access_token": mint_access_token(user["id"], user["email"], user["tier"]),
        "refresh_token": mint_refresh_token(user["id"]),
        "token_type": "bearer",
    }
def issue_pair_for_user(user: dict) -> dict:
    return {
        "access_token": mint_access_token(user["id"], user["email"], user["tier"]),
        "refresh_token": mint_refresh_token(user["id"]),
        "token_type": "bearer",
    }
