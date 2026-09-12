import pytest

from contentflow import deepseek_hello


@pytest.fixture(autouse=True)
def isolate_real_api_configuration(monkeypatch: pytest.MonkeyPatch) -> None:
    """Prevent unit tests from loading a real local API key from .env."""
    monkeypatch.setattr(deepseek_hello, "load_dotenv", lambda **_: False)
    monkeypatch.setenv("DEEPSEEK_API_KEY", "")
    monkeypatch.setenv("LLM_PROVIDER", "mock")
    monkeypatch.setenv("APP_ENV", "development")
