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

    # Regime-aware lead engine settings
    max_daily_leads: int = 5
    cluster_window_hours: int = 6
    min_ev_usd: float = 0.0
    caution_theme_min_confidence: float = 0.62
    edge_min_samples: int = 20
    edge_shrinkage_weight: float = 0.5
    august_seasonality_enabled: bool = True
    default_range_rotation: bool = True
    august_risk_multiplier: float = 1.2
    regime_risk_off_multiplier: float = 1.5
    regime_ai_infra_multiplier: float = 1.3
    regime_earnings_multiplier: float = 1.25
    regime_rotation_multiplier: float = 1.0
    regime_confidence_boost_risk_off: float = 0.05
    regime_confidence_boost_ai_infra: float = 0.05
    regime_confidence_boost_earnings: float = 0.03
    regime_kelly_fraction_risk_off: float = 1 / 3
    regime_kelly_fraction_ai_infra: float = 1 / 3
    regime_kelly_fraction_earnings: float = 1 / 3
    earnings_sellthebeat_horizon_hours: int = 48

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
