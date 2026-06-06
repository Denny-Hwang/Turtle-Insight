"""Application settings loaded from the environment (pydantic-settings).

Single source of configuration (TDD §8). Secrets and model identifiers are
injected via environment / ``.env`` only — never hardcoded in code
(see ``docs/guidelines/engineering.md`` and ``CLAUDE.md`` GOLDEN RULE 6).
"""

from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Environment-backed settings.

    Field names map case-insensitively to the ``TI_*`` / source env keys in
    TDD §8 (e.g. field ``ti_deep_model`` <- env ``TI_DEEP_MODEL``).
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # --- LLM tiers: model identifiers come from env only (no hardcoded model names) ---
    ti_deep_model: str | None = None  # TI_DEEP_MODEL (Claude / deep tier)
    ti_fast_model: str | None = None  # TI_FAST_MODEL (optional local; else fall back to deep)
    anthropic_api_key: str | None = None  # ANTHROPIC_API_KEY (secret)
    ti_ollama_url: str | None = None  # TI_OLLAMA_URL (optional local fast-tier endpoint)

    # --- storage ---
    ti_db_url: str = "sqlite:///ti.db"  # TI_DB_URL (v1+: postgres://...)
    ti_redis_url: str | None = None  # TI_REDIS_URL (v1+, Dramatiq broker)

    # --- data source keys (secrets; never commit) ---
    dart_api_key: str | None = None  # DART_API_KEY
    fred_api_key: str | None = None  # FRED_API_KEY
    market_api_key: str | None = None  # MARKET_API_KEY


@lru_cache
def get_settings() -> Settings:
    """Return the process-wide cached :class:`Settings` instance."""
    return Settings()
