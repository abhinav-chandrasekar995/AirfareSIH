"""Application settings, environment-driven. No secrets are ever committed (build prompt Sec.6)."""
from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "India Airfare Intelligence"
    environment: Literal["local", "staging", "production"] = "local"
    debug: bool = True

    database_url: str = "postgresql+asyncpg://airfare:airfare@localhost:5432/airfare"
    redis_url: str = "redis://localhost:6379/0"

    # Statistical configuration. Bundled into methodology_version so any published
    # number is traceable to the settings that produced it (build prompt Sec.5).
    methodology_version: str = "idx-1.0.0"
    quality_threshold: float = 60.0
    min_observations_per_period: int = 5
    default_estimator: str = "TRIMMED_MEAN_10"
    index_base_period: str = "2025-09-01"
    default_cpi_weight_pct: float = 2.5
    forecast_horizon_days: int = 14

    # Data-mode resolution (build prompt Sec.33).
    live_freshness_hours: int = 6
    force_data_mode: str | None = None  # "LIVE" | "CACHED" | "REPLAY" | None (auto)

    # Security
    api_key_header: str = "X-API-Key"
    default_rate_limit_per_min: int = 60
    public_rate_limit_per_min: int = 30
    cors_origins: list[str] = ["http://localhost:3000"]

    # Collection ethics (build prompt Sec.3). These are floors, not suggestions.
    respect_robots_txt: bool = True
    default_source_rate_limit_rpm: int = 20
    collection_enabled: bool = False  # off by default; demo runs on seeded data

    CPI_DISCLAIMER: str = (
        "This module is a simulation for analytical demonstration. It does not "
        "represent an official CPI revision or official NSO methodology."
    )
    ATTRIBUTION_NOTE: str = (
        "Model-based attribution; contribution shares are estimated, not measured."
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
