import json
from functools import lru_cache

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "invest-agent"
    database_url: str = "postgresql+asyncpg://invest:invest_local@postgres:5432/invest_agent"
    redis_url: str = "redis://redis:6379/0"
    portfolio_cash: float = 10_000.0
    portfolio_value: float = 50_000.0
    confidence_threshold: float = 0.50
    model_path: str = ""
    telegram_bot_token: str = ""
    telegram_chat_id: str = ""
    price_source: str = "mock"
    allow_mock_price_fallback: bool = True
    cors_origins: list[str] = ["http://localhost:3000"]
    frontend_url: str = "http://localhost:3000"
    secret_key: str = "changeme"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    admin_username: str = "admin"
    admin_password: str = "changeme"
    polygon_api_key: str = ""
    news_source: str = "mock"
    news_api_key: str = ""
    news_api_url: str = "https://finnhub.io/api/v1"
    kelly_odds: float = 2.0
    sector_cap_pct: float = 0.25
    min_allocation_usd: float = 10.0
    rate_limit_requests: int = 100
    rate_limit_window_seconds: int = 60
    paper_trading_mode: bool = True
    paper_auto_approve: bool = True
    ml_min_outcomes: int = 50
    research_disclaimer: str = (
        "Research signal only. Not financial advice. Past performance does not guarantee future results."
    )
    stale_ingest_minutes: int = 15
    environment: str = "development"

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors(cls, v: object) -> list[str]:
        if isinstance(v, str):
            try:
                return json.loads(v)
            except (json.JSONDecodeError, ValueError):
                return [v]
        return v  # type: ignore[return-value]


@lru_cache
def get_settings() -> Settings:
    return Settings()
