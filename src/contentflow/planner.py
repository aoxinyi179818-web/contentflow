"""Minimal content-planning node for ContentFlow AI Step 21."""

import argparse

from contentflow.config import Settings
from contentflow.llm_client import create_deepseek_client
from contentflow.models import ContentPlan, ContentPreferences
from contentflow.observability import record_llm_usage
from contentflow.platforms import build_platform_guidance
from contentflow.prompting import load_prompt
from contentflow.structured import parse_structured_output


class PlannerInputError(ValueError):
    """Raised when a user submits an unusable planning topic."""


class PlannerConfigurationError(RuntimeError):
    """Raised when the selected LLM provider cannot run the Planner."""


PLANNER_INSTRUCTIONS = load_prompt("planner")


def build_planner_messages(
    topic: str, *, preferences: ContentPreferences | None = None
) -> list[dict[str, str]]:
    """Validate a topic and build the first Planner request."""
    normalized_topic = topic.strip()
    if not normalized_topic:
        raise PlannerInputError("Topic must not be empty.")

    request = f"请为这个主题制定内容计划：{normalized_topic}"
    if preferences:
        request += (
            "\n\n用户已确定以下创作要求，必须严格遵守："
            f"\n- 目标受众：{preferences.audience}"
            f"\n- 语气：{preferences.tone}"
            f"\n- 输出平台：{preferences.platform}"
            f"\n- 目标篇幅：{preferences.target_length}"
            + (f"\n- 品牌写作规则：{preferences.brand_voice}" if preferences.brand_voice else "")
            + f"\n\n{build_platform_guidance(preferences.platform)}"
        )
    return [
        {"role": "system", "content": PLANNER_INSTRUCTIONS},
        {"role": "user", "content": request},
    ]


def create_plan(
    topic: str,
    settings: Settings | None = None,
    *,
    preferences: ContentPreferences | None = None,
) -> ContentPlan:
    """Request and validate one structured content plan from DeepSeek."""
    active_settings = settings or Settings.from_env()
    client = create_deepseek_client(
        active_settings,
        consumer_name="Planner",
        error_type=PlannerConfigurationError,
    )
    response = client.chat.completions.create(
        model=active_settings.llm_model,
        messages=build_planner_messages(topic, preferences=preferences),
        response_format={"type": "json_object"},
        max_tokens=2000,
    )
    record_llm_usage(response, node="planner")
    content = response.choices[0].message.content
    if not content:
        raise RuntimeError("Planner returned an empty response.")
    plan = parse_structured_output(content, ContentPlan)
    if preferences:
        return ContentPlan.model_validate(
            {
                **plan.model_dump(),
                "audience": preferences.audience,
                "tone": preferences.tone,
                "platform": preferences.platform,
                "target_length": preferences.target_length,
                "brand_voice": preferences.brand_voice,
            }
        )
    return plan


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate a ContentFlow AI content plan.")
    parser.add_argument("topic", help="The topic to plan.")
    args = parser.parse_args()
    print(create_plan(args.topic).model_dump_json(indent=2))


if __name__ == "__main__":
    main()
