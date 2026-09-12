import math
import os
from dataclasses import dataclass

from dotenv import load_dotenv


class SettingsConfigurationError(ValueError):
    """Raised when a local environment setting cannot form a safe Settings value."""


def _read_timeout_seconds() -> float:
    """Return a finite, positive provider timeout from the local environment."""
    raw_timeout = os.getenv("LLM_TIMEOUT_SECONDS", "30")
    try:
        timeout = float(raw_timeout)
    except ValueError as error:
        raise SettingsConfigurationError(
            "LLM_TIMEOUT_SECONDS must be a positive number."
        ) from error
    if not math.isfinite(timeout) or timeout <= 0:
        raise SettingsConfigurationError("LLM_TIMEOUT_SECONDS must be a positive number.")
    return timeout


@dataclass(frozen=True)
class Settings:
    """Application configuration; no secrets are committed to the repository."""

    app_env: str = "development"
    log_level: str = "INFO"
    llm_provider: str = "mock"
    llm_model: str = ""
    database_url: str = "sqlite:///./data/contentflow.db"
    llm_base_url: str = ""
    llm_timeout_seconds: float = 30.0
    deepseek_api_key: str = ""

    @classmethod
    def from_env(cls) -> "Settings":
        load_dotenv(override=False)
        return cls(
            app_env=os.getenv("APP_ENV", "development"),
            log_level=os.getenv("LOG_LEVEL", "INFO"),
            llm_provider=os.getenv("LLM_PROVIDER", "mock"),
            llm_model=os.getenv("LLM_MODEL", ""),
            database_url=os.getenv("DATABASE_URL", "sqlite:///./data/contentflow.db"),
            llm_base_url=os.getenv("LLM_BASE_URL", ""),
            llm_timeout_seconds=_read_timeout_seconds(),
            deepseek_api_key=os.getenv("DEEPSEEK_API_KEY", ""),
        )
