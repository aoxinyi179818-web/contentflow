import pytest

from contentflow.config import Settings, SettingsConfigurationError


def test_default_settings_are_safe_for_local_development() -> None:
    settings = Settings.from_env()

    assert settings.app_env == "development"
    assert settings.llm_provider == "mock"


@pytest.mark.parametrize("timeout", ["not-a-number", "0", "-1", "nan", "inf"])
def test_settings_reject_invalid_timeout_values(
    monkeypatch: pytest.MonkeyPatch, timeout: str
) -> None:
    monkeypatch.setenv("LLM_TIMEOUT_SECONDS", timeout)

    with pytest.raises(SettingsConfigurationError, match="positive number"):
        Settings.from_env()
