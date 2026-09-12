import pytest

from contentflow import llm_client
from contentflow.config import Settings


class ConsumerConfigurationError(RuntimeError):
    """Test-only error type used to verify caller-specific failures."""


def test_factory_passes_one_complete_deepseek_configuration(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, object] = {}
    expected_client = object()

    def fake_openai(**kwargs: object) -> object:
        captured.update(kwargs)
        return expected_client

    monkeypatch.setattr(llm_client, "OpenAI", fake_openai)
    settings = Settings(
        llm_provider="deepseek",
        llm_model="deepseek-chat",
        deepseek_api_key="test-key",
        llm_timeout_seconds=12.5,
    )

    client = llm_client.create_deepseek_client(
        settings,
        consumer_name="Test Consumer",
        error_type=ConsumerConfigurationError,
    )

    assert client is expected_client
    assert captured == {
        "api_key": "test-key",
        "base_url": "https://api.deepseek.com",
        "timeout": 12.5,
    }


@pytest.mark.parametrize(
    ("settings", "expected_message"),
    [
        (Settings(llm_provider="mock", llm_model="model", deepseek_api_key="key"), "LLM_PROVIDER"),
        (Settings(llm_provider="deepseek", llm_model="model"), "DEEPSEEK_API_KEY"),
        (Settings(llm_provider="deepseek", deepseek_api_key="key"), "LLM_MODEL"),
    ],
)
def test_factory_preserves_the_callers_configuration_error(
    settings: Settings, expected_message: str
) -> None:
    with pytest.raises(ConsumerConfigurationError, match=expected_message):
        llm_client.create_deepseek_client(
            settings,
            consumer_name="Test Consumer",
            error_type=ConsumerConfigurationError,
        )
