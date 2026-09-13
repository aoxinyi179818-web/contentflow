from pathlib import Path

import pytest

from contentflow.config import Settings, SettingsConfigurationError, save_deepseek_api_key


def test_session_key_override_sets_only_runtime_settings() -> None:
    settings = Settings(llm_provider="mock")

    active = settings.with_deepseek_api_key(" session-key ")

    assert active.deepseek_api_key == "session-key"
    assert active.llm_provider == "deepseek"
    assert active.llm_model == "deepseek-chat"
    assert active.llm_base_url == "https://api.deepseek.com"
    assert settings.deepseek_api_key == ""
    assert settings.llm_provider == "mock"


@pytest.mark.parametrize("api_key", ["", "   ", "key\nsecond-line"])
def test_session_key_override_rejects_unsafe_values(api_key: str) -> None:
    with pytest.raises(SettingsConfigurationError):
        Settings().with_deepseek_api_key(api_key)


def test_save_deepseek_api_key_preserves_other_env_values(tmp_path: Path) -> None:
    env_path = tmp_path / ".env"
    env_path.write_text("APP_ENV=development\nCUSTOM_VALUE=keep\nDEEPSEEK_API_KEY=old\n", encoding="utf-8")

    saved_path = save_deepseek_api_key("new-test-key", env_path=env_path)

    assert saved_path == env_path
    assert env_path.read_text(encoding="utf-8") == (
        "APP_ENV=development\n"
        "CUSTOM_VALUE=keep\n"
        "DEEPSEEK_API_KEY=new-test-key\n"
        "LLM_PROVIDER=deepseek\n"
        "LLM_MODEL=deepseek-chat\n"
        "LLM_BASE_URL=https://api.deepseek.com\n"
        "LLM_TIMEOUT_SECONDS=30\n"
        "DATABASE_URL=sqlite:///./data/contentflow.db\n"
    )
