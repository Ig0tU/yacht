from __future__ import annotations

import secrets
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from typing import Iterator

from passlib.context import CryptContext
from sqlalchemy import Column, DateTime, Index, Integer, MetaData, String, Table, create_engine, func, inspect, select, text
from sqlalchemy.engine import Connection
from sqlalchemy.exc import IntegrityError

from .config import settings

pwd_ctx = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")

metadata = MetaData()

users = Table(
    "users",
    metadata,
    Column("id", String, primary_key=True),
    Column("email", String, unique=True, nullable=False),
    Column("token", String, unique=True),
    Column("password_hash", String),
    Column("tier", String, nullable=False, server_default="free"),
    Column("stripe_customer_id", String),
    Column("stripe_subscription_id", String),
    Column("created_at", DateTime(timezone=True), nullable=False),
)

usage_events = Table(
    "usage_events",
    metadata,
    Column("id", String, primary_key=True),
    Column("user_id", String, nullable=False),
    Column("kind", String, nullable=False),
    Column("amount", Integer, nullable=False, server_default="1"),
    Column("created_at", DateTime(timezone=True), nullable=False),
)

refresh_tokens = Table(
    "refresh_tokens",
    metadata,
    Column("id", String, primary_key=True),
    Column("user_id", String, nullable=False),
    Column("token_hash", String, nullable=False),
    Column("expires_at", DateTime(timezone=True), nullable=False),
    Column("revoked", Integer, nullable=False, server_default="0"),
    Column("created_at", DateTime(timezone=True), nullable=False),
)

Index("idx_users_email", users.c.email)
Index("idx_users_stripe_customer", users.c.stripe_customer_id)
Index("idx_refresh_token_hash", refresh_tokens.c.token_hash)
Index("idx_usage_user_kind_created", usage_events.c.user_id, usage_events.c.kind, usage_events.c.created_at)


def _utc_now() -> datetime:
    return datetime.now(timezone.utc).replace(microsecond=0)


def _engine_args() -> dict:
    url = settings.resolved_database_url()
    if url.startswith("sqlite:"):
        return {"connect_args": {"check_same_thread": False}}
    return {}


engine = create_engine(settings.resolved_database_url(), pool_pre_ping=True, future=True, **_engine_args())


@contextmanager
def get_conn() -> Iterator[Connection]:
    with engine.begin() as conn:
        yield conn


def init_db() -> None:
    metadata.create_all(engine)
    _safe_add_column("users", "password_hash", "TEXT")
    _safe_add_column("users", "token", "TEXT")


def _safe_add_column(table: str, column: str, col_type: str) -> None:
    inspector = inspect(engine)
    cols = {c["name"] for c in inspector.get_columns(table)}
    if column in cols:
        return
    with engine.begin() as conn:
        conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {column} {col_type}"))


def get_or_create_user(email: str) -> dict:
    now = _utc_now()
    with get_conn() as conn:
        row = conn.execute(select(users).where(users.c.email == email)).mappings().first()
        if row:
            return dict(row)
        user_id = f"user_{secrets.token_hex(8)}"
        token = f"yacht_{secrets.token_hex(24)}"
        try:
            conn.execute(
                users.insert().values(
                    id=user_id,
                    email=email,
                    token=token,
                    tier="free",
                    created_at=now,
                )
            )
        except IntegrityError:
            row = conn.execute(select(users).where(users.c.email == email)).mappings().first()
            if row:
                return dict(row)
            raise RuntimeError("failed to create or fetch user")
        row = conn.execute(select(users).where(users.c.id == user_id)).mappings().first()
        if row:
            return dict(row)
        raise RuntimeError("failed to create user")


def get_user_by_token(token: str) -> dict | None:
    with get_conn() as conn:
        row = conn.execute(select(users).where(users.c.token == token)).mappings().first()
        return dict(row) if row else None


def get_user_by_email(email: str) -> dict | None:
    with get_conn() as conn:
        row = conn.execute(select(users).where(users.c.email == email)).mappings().first()
        return dict(row) if row else None


def get_user_by_id(user_id: str) -> dict | None:
    with get_conn() as conn:
        row = conn.execute(select(users).where(users.c.id == user_id)).mappings().first()
        return dict(row) if row else None


def create_user_with_password(email: str, password: str) -> dict | None:
    now = _utc_now()
    user_id = f"user_{secrets.token_hex(8)}"
    opaque_token = f"yacht_{secrets.token_hex(24)}"
    password_hash = pwd_ctx.hash(password)
    with get_conn() as conn:
        try:
            conn.execute(
                users.insert().values(
                    id=user_id,
                    email=email,
                    token=opaque_token,
                    password_hash=password_hash,
                    tier="free",
                    created_at=now,
                )
            )
        except IntegrityError:
            return None
        row = conn.execute(select(users).where(users.c.id == user_id)).mappings().first()
        return dict(row) if row else None


def verify_password(email: str, password: str) -> dict | None:
    user = get_user_by_email(email)
    if not user:
        return None
    pw_hash = user.get("password_hash")
    if not pw_hash:
        return None
    if not pwd_ctx.verify(password, pw_hash):
        return None
    return user


def store_refresh_token(user_id: str, token_hash: str, expires_at: datetime) -> str:
    rid = f"rt_{secrets.token_hex(8)}"
    with get_conn() as conn:
        conn.execute(
            refresh_tokens.insert().values(
                id=rid,
                user_id=user_id,
                token_hash=token_hash,
                expires_at=expires_at,
                revoked=0,
                created_at=_utc_now(),
            )
        )
    return rid


def find_valid_refresh_token(token_hash: str) -> dict | None:
    now = _utc_now()
    with get_conn() as conn:
        row = (
            conn.execute(
                select(refresh_tokens).where(
                    refresh_tokens.c.token_hash == token_hash,
                    refresh_tokens.c.revoked == 0,
                    refresh_tokens.c.expires_at > now,
                )
            )
            .mappings()
            .first()
        )
        return dict(row) if row else None


def revoke_refresh_token(token_hash: str) -> None:
    with get_conn() as conn:
        conn.execute(
            refresh_tokens.update()
            .where(refresh_tokens.c.token_hash == token_hash)
            .values(revoked=1)
        )


def set_user_tier_by_customer(customer_id: str, tier: str, subscription_id: str | None) -> None:
    with get_conn() as conn:
        conn.execute(
            users.update()
            .where(users.c.stripe_customer_id == customer_id)
            .values(tier=tier, stripe_subscription_id=subscription_id)
        )


def set_user_customer(user_id: str, customer_id: str) -> None:
    with get_conn() as conn:
        conn.execute(
            users.update().where(users.c.id == user_id).values(stripe_customer_id=customer_id)
        )


def add_usage(user_id: str, kind: str, amount: int = 1) -> None:
    with get_conn() as conn:
        conn.execute(
            usage_events.insert().values(
                id=f"evt_{secrets.token_hex(8)}",
                user_id=user_id,
                kind=kind,
                amount=amount,
                created_at=_utc_now(),
            )
        )


def usage_today(user_id: str) -> dict[str, int]:
    now = _utc_now()
    start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    end = start + timedelta(days=1)
    with get_conn() as conn:
        rows = (
            conn.execute(
                select(usage_events.c.kind, func.coalesce(func.sum(usage_events.c.amount), 0))
                .where(
                    usage_events.c.user_id == user_id,
                    usage_events.c.created_at >= start,
                    usage_events.c.created_at < end,
                )
                .group_by(usage_events.c.kind)
            )
            .all()
        )
    out = {"run": 0, "pull": 0, "compose_up": 0}
    for kind, total in rows:
        out[str(kind)] = int(total)
    return out
