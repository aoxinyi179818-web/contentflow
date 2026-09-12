"""Minimal content-planning node for ContentFlow AI Step 21."""

import argparse

from contentflow.config import Settings
from contentflow.llm_client import create_deepseek_client
from contentflow.models import ContentPlan
from contentflow.observability import record_llm_usage
from contentflow.prompting import load_prompt
from contentflow.structured import parse_structured_output


class PlannerInputError(ValueError):
    """Raised when a user submits an unusable planning topic."""


class PlannerConfigurationError(RuntimeError):
    """Raised when the selected LLM provider cannot run the Planner."""


PLANNER_INSTRUCTIONS = load_prompt("planner")


def build_planner_messages(topic: str) -> list[dict[str, str]]:
    """Validate a topic and build the first Planner request."""
    normalized_topic = topic.strip()
    if not normalized_topic:
        raise PlannerInputError("Topic must not be empty.")

    return [
        {"role": "system", "content": PLANNER_INSTRUCTIONS},
        {"role": "user", "content": f"请为这个主题制定内容计划：{normalized_topic}"},
    ]


def create_plan(topic: str, settings: Settings | None = None) -> ContentPlan:
    """Request and validate one structured content plan from DeepSeek."""
    active_settings = settings or Settings.from_env()
    client = create_deepseek_client(
        active_settings,
        consumer_name="Planner",
        error_type=PlannerConfigurationError,
    )
    response = client.chat.completions.create(
        model=active_settings.llm_model,
        messages=build_planner_messages(topic),
        response_format={"type": "json_object"},
        max_tokens=2000,
    )
    record_llm_usage(response, node="planner")
    content = response.choices[0].message.content
    if not content:
        raise RuntimeError("Planner returned an empty response.")
    return parse_structured_output(content, ContentPlan)


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate a ContentFlow AI content plan.")
    parser.add_argument("topic", help="The topic to plan.")
    args = parser.parse_args()
    print(create_plan(args.topic).model_dump_json(indent=2))


if __name__ == "__main__":
    main()
