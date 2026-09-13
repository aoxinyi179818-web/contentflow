import math
import os
from dataclasses import dataclass, replace
from pathlib import Path

from dotenv import load_dotenv


class SettingsConfigurationError(ValueError):
    """Raised when a local environment setting cannot form a safe Settings value."""


DEEPSEEK_ENV_DEFAULTS = {
    "LLM_PROVIDER": "deepseek",
    "LLM_MODEL": "deepseek-chat",
    "LLM_BASE_URL": "https://api.deepseek.com",
    "LLM_TIMEOUT_SECONDS": "30",
    "DATABASE_URL": "sqlite:///./data/contentflow.db",
}


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

    def with_deepseek_api_key(self, api_key: str) -> "Settings":
        """Return session-only DeepSeek settings without changing process environment variables."""
        normalized_key = _normalize_api_key(api_key)
        return replace(
            self,
            llm_provider="deepseek",
            llm_model=self.llm_model or DEEPSEEK_ENV_DEFAULTS["LLM_MODEL"],
            llm_base_url=self.llm_base_url or DEEPSEEK_ENV_DEFAULTS["LLM_BASE_URL"],
            deepseek_api_key=normalized_key,
        )

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


def save_deepseek_api_key(api_key: str, *, env_path: Path | None = None) -> Path:
    """Persist one local DeepSeek key without logging it or changing other .env values."""
    normalized_key = _normalize_api_key(api_key)
    target = env_path or Path(".env")
    existing_lines = target.read_text(encoding="utf-8").splitlines() if target.exists() else []
    values = _read_env_lines(existing_lines)
    for name, value in DEEPSEEK_ENV_DEFAULTS.items():
        values.setdefault(name, value)
    values["DEEPSEEK_API_KEY"] = normalized_key

    lines = _replace_env_values(existing_lines, values)
    temporary = target.with_name(f".{target.name}.tmp")
    temporary.write_text("\n".join(lines) + "\n", encoding="utf-8")
    temporary.replace(target)
    return target


def _normalize_api_key(api_key: str) -> str:
    normalized_key = api_key.strip()
    if not normalized_key:
        raise SettingsConfigurationError("请输入有效的 DeepSeek API Key。")
    if "\n" in normalized_key or "\r" in normalized_key:
        raise SettingsConfigurationError("API Key 不能包含换行符。")
    return normalized_key


def _read_env_lines(lines: list[str]) -> dict[str, str]:
    values: dict[str, str] = {}
    for line in lines:
        if "=" not in line or line.lstrip().startswith("#"):
            continue
        name, value = line.split("=", 1)
        values[name.strip()] = value
    return values


def _replace_env_values(lines: list[str], values: dict[str, str]) -> list[str]:
    remaining = dict(values)
    updated: list[str] = []
    for line in lines:
        if "=" not in line or line.lstrip().startswith("#"):
            updated.append(line)
            continue
        name, _ = line.split("=", 1)
        normalized_name = name.strip()
        if normalized_name in remaining:
            updated.append(f"{normalized_name}={remaining.pop(normalized_name)}")
        else:
            updated.append(line)
    return [*updated, *(f"{name}={value}" for name, value in remaining.items())]
