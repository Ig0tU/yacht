from __future__ import annotations

from fastapi import HTTPException

from .config import settings
from .db import add_usage, usage_today


def enforce_and_record(user: dict, kind: str) -> None:
    if user["tier"] == "pro":
        add_usage(user["id"], kind, 1)
        return

    limits = {
        "run": settings.free_runs_per_day,
        "pull": settings.free_pulls_per_day,
        "compose_up": settings.free_compose_up_per_day,
    }
    if kind not in limits:
        raise HTTPException(status_code=400, detail=f"unknown usage kind: {kind}")

    totals = usage_today(user["id"])
    if totals.get(kind, 0) >= limits[kind]:
        raise HTTPException(
            status_code=402,
            detail=f"free-tier limit reached for {kind}; upgrade to pro",
        )
    add_usage(user["id"], kind, 1)


def quota_status(user: dict) -> dict:
    totals = usage_today(user["id"])
    limits = {
        "run": None if user["tier"] == "pro" else settings.free_runs_per_day,
        "pull": None if user["tier"] == "pro" else settings.free_pulls_per_day,
        "compose_up": None if user["tier"] == "pro" else settings.free_compose_up_per_day,
    }
    return {"tier": user["tier"], "used_today": totals, "limits": limits}
