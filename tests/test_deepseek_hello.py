import pytest

from contentflow.deepseek_hello import DeepSeekConfigurationError, request_hello


def test_request_hello_requires_an_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)

    with pytest.raises(DeepSeekConfigurationError, match="DEEPSEEK_API_KEY"):
        request_hello()
