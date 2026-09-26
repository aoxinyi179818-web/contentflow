"""Generate local publication packaging from a reviewed content version."""

from contentflow.config import Settings
from contentflow.llm_client import create_deepseek_client
from contentflow.models import ContentPlatform, PublishingAssets
from contentflow.observability import record_llm_usage
from contentflow.prompting import load_prompt
from contentflow.structured import parse_structured_output


class PackagingInputError(ValueError):
    """Raised when publication packaging lacks usable source content."""


class PackagingConfigurationError(RuntimeError):
    """Raised when the configured LLM cannot prepare publishing assets."""


PACKAGING_INSTRUCTIONS = load_prompt("packaging")


def build_packaging_messages(content: str, *, platform: ContentPlatform) -> list[dict[str, str]]:
    """Build a structured request that stays grounded in the reviewed content."""
    normalized_content = content.strip()
    if not normalized_content:
        raise PackagingInputError("content must not be empty")
    if len(normalized_content) > 20_000:
        raise PackagingInputError("content must not exceed 20000 characters")
    return [
        {"role": "system", "content": PACKAGING_INSTRUCTIONS},
        {
            "role": "user",
            "content": (
                f"目标发布平台：{platform}\n\n"
                f"已审核内容：\n\n{normalized_content}\n\n"
                "请生成发布包装 JSON，platform 必须与目标发布平台完全一致。"
            ),
        },
    ]


def generate_publishing_assets(
    content: str, *, platform: ContentPlatform, settings: Settings | None = None
) -> PublishingAssets:
    """Generate and validate titles, hooks, tags, and a CTA without publishing anywhere."""
    active_settings = settings or Settings.from_env()
    client = create_deepseek_client(
        active_settings,
        consumer_name="Publishing Assets",
        error_type=PackagingConfigurationError,
    )
    response = client.chat.completions.create(
        model=active_settings.llm_model,
        messages=build_packaging_messages(content, platform=platform),
        response_format={"type": "json_object"},
        max_tokens=1200,
    )
    record_llm_usage(response, node="publishing_assets")
    content_value = response.choices[0].message.content
    if not content_value:
        raise RuntimeError("Publishing Assets returned an empty response.")
    assets = parse_structured_output(content_value, PublishingAssets)
    if assets.platform != platform:
        raise RuntimeError("Publishing Assets returned the wrong platform.")
    return assets
