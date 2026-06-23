"""Configuration and credential handling for CHURN.

Uses pydantic-settings for 12-factor friendly config.
Secrets can be extended to keyring later.
"""

from __future__ import annotations

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class ChurnSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="CHURN_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # General
    log_level: str = Field(default="INFO", description="Logging level")

    # Driver specific (examples)
    http_timeout: float = Field(default=30.0)
    s3_region: str | None = None
    s3_endpoint: str | None = None
    s3_access_key_id: str | None = None
    s3_secret_access_key: str | None = None

    # Future: credentials via keyring or external vault
    # For now, drivers pull from env or explicit config dicts.


settings = ChurnSettings()
