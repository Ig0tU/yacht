from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Settings:
    env: str = os.getenv("YACHT_ENV", "dev")
    database_url: str = os.getenv("DATABASE_URL", "")
    db_path: str = os.getenv("YACHT_DB_PATH", "./data/yacht.db")
    jwt_secret: str = os.getenv("YACHT_JWT_SECRET", "change-me-now")
    access_token_minutes: int = int(os.getenv("ACCESS_TOKEN_MINUTES", "30"))
    refresh_token_days: int = int(os.getenv("REFRESH_TOKEN_DAYS", "30"))
    rate_limit_per_minute: int = int(os.getenv("RATE_LIMIT_PER_MINUTE", "120"))
    trust_proxy_headers: bool = os.getenv("TRUST_PROXY_HEADERS", "false").lower() in ("1", "true", "yes")

    free_runs_per_day: int = int(os.getenv("FREE_RUNS_PER_DAY", "25"))
    free_pulls_per_day: int = int(os.getenv("FREE_PULLS_PER_DAY", "40"))
    free_compose_up_per_day: int = int(os.getenv("FREE_COMPOSE_UP_PER_DAY", "10"))

    remote_docker_host: str = os.getenv("REMOTE_DOCKER_HOST", "")
    remote_docker_token: str = os.getenv("REMOTE_DOCKER_TOKEN", "")
    remote_docker_api_version: str = os.getenv("REMOTE_DOCKER_API_VERSION", "v1.43")
    remote_docker_timeout_seconds: float = float(os.getenv("REMOTE_DOCKER_TIMEOUT_SECONDS", "20"))

    stripe_secret_key: str = os.getenv("STRIPE_SECRET_KEY", "")
    stripe_webhook_secret: str = os.getenv("STRIPE_WEBHOOK_SECRET", "")
    stripe_price_pro_monthly: str = os.getenv("STRIPE_PRICE_PRO_MONTHLY", "")
    stripe_success_url: str = os.getenv("STRIPE_SUCCESS_URL", "https://example.com/billing/success")
    stripe_cancel_url: str = os.getenv("STRIPE_CANCEL_URL", "https://example.com/billing/cancel")

    def resolved_database_url(self) -> str:
        if self.database_url:
            return self.database_url
        path = Path(self.db_path).expanduser()
        return f"sqlite:///{path}"

    def validate(self) -> None:
        if self.env == "prod" and self.jwt_secret == "change-me-now":
            raise RuntimeError("YACHT_JWT_SECRET must be set in production")


settings = Settings()
settings.validate()
