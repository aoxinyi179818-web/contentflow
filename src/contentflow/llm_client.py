"""Shared construction and validation for ContentFlow LLM clients."""

from openai import OpenAI

from contentflow.config import Settings

DEFAULT_DEEPSEEK_BASE_URL = "https://api.deepseek.com"


def create_deepseek_client(
    settings: Settings,
    *,
    consumer_name: str,
    error_type: type[RuntimeError],
) -> OpenAI:
    """Build one configured DeepSeek client while preserving caller error semantics."""
    if settings.llm_provider != "deepseek":
        raise error_type(f"LLM_PROVIDER must be 'deepseek' for the {consumer_name}.")
    if not settings.deepseek_api_key:
        raise error_type("DEEPSEEK_API_KEY is missing from the local environment.")
    if not settings.llm_model:
        raise error_type(f"LLM_MODEL is required for the {consumer_name}.")

    return OpenAI(
        api_key=settings.deepseek_api_key,
        base_url=settings.llm_base_url or DEFAULT_DEEPSEEK_BASE_URL,
        timeout=settings.llm_timeout_seconds,
    )
