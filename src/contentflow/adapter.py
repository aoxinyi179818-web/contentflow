"""Platform-specific content adaptation node for ContentFlow AI Step 40."""

from typing import get_args

from contentflow.config import Settings
from contentflow.llm_client import create_deepseek_client
from contentflow.models import AdaptedContent, ContentPlatform
from contentflow.observability import record_llm_usage
from contentflow.prompting import load_prompt
from contentflow.structured import parse_structured_output


class AdapterInputError(ValueError):
    """Raised when the Adapter receives unsupported or empty input."""


class AdapterConfigurationError(RuntimeError):
    """Raised when the configured LLM cannot run the Adapter."""


ADAPTER_INSTRUCTIONS = load_prompt("adapter")
SUPPORTED_PLATFORMS = frozenset(get_args(ContentPlatform))


def normalize_platform(platform: str) -> ContentPlatform:
    """Return one approved output platform without accepting free-form targets."""
    normalized = platform.strip()
    if normalized not in SUPPORTED_PLATFORMS:
        supported = "、".join(SUPPORTED_PLATFORMS)
        raise AdapterInputError(f"Unsupported platform. Choose one of: {supported}.")
    return normalized  # type: ignore[return-value]


def build_adapter_messages(
    final_content: str, *, platform: str, audience: str = "通用受众"
) -> list[dict[str, str]]:
    """Build a constrained Adapter request from reviewed final content."""
    normalized_content = final_content.strip()
    if not normalized_content:
        raise AdapterInputError("Final content must not be empty.")
    normalized_platform = normalize_platform(platform)
    normalized_audience = audience.strip() or "通用受众"
    return [
        {"role": "system", "content": ADAPTER_INSTRUCTIONS},
        {
            "role": "user",
            "content": (
                f"目标平台：{normalized_platform}\n"
                f"目标受众：{normalized_audience}\n\n"
                f"请适配以下已经审核的最终内容：\n\n{normalized_content}"
            ),
        },
    ]


def adapt_content(
    final_content: str,
    *,
    platform: str,
    audience: str = "通用受众",
    settings: Settings | None = None,
) -> AdaptedContent:
    """Request and validate a platform-specific adaptation from DeepSeek."""
    normalized_platform = normalize_platform(platform)
    active_settings = settings or Settings.from_env()
    client = create_deepseek_client(
        active_settings,
        consumer_name="Adapter",
        error_type=AdapterConfigurationError,
    )
    response = client.chat.completions.create(
        model=active_settings.llm_model,
        messages=build_adapter_messages(
            final_content, platform=normalized_platform, audience=audience
        ),
        response_format={"type": "json_object"},
        max_tokens=2500,
    )
    record_llm_usage(response, node="adapter")
    content = response.choices[0].message.content
    if not content:
        raise RuntimeError("Adapter returned an empty response.")
    adapted = parse_structured_output(content, AdaptedContent)
    if adapted.platform != normalized_platform:
        raise RuntimeError("Adapter returned content for an unexpected platform.")
    return adapted
