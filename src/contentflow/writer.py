"""Minimal draft-writing node for ContentFlow AI Step 22."""

import argparse
from pathlib import Path

from contentflow.config import Settings
from contentflow.llm_client import create_deepseek_client
from contentflow.models import ContentPlan
from contentflow.observability import record_llm_usage
from contentflow.platforms import build_platform_guidance
from contentflow.prompting import load_prompt


class WriterInputError(ValueError):
    """Raised when the Writer receives an unusable content plan."""


class WriterConfigurationError(RuntimeError):
    """Raised when the configured LLM cannot run the Writer."""


WRITER_INSTRUCTIONS = load_prompt("writer")


def build_writer_messages(plan: str | ContentPlan) -> list[dict[str, str]]:
    """Validate a confirmed plan and build the first Writer request."""
    normalized_plan = plan.model_dump_json(indent=2) if isinstance(plan, ContentPlan) else plan.strip()
    if not normalized_plan:
        raise WriterInputError("Confirmed plan must not be empty.")

    platform_guidance = (
        f"\n\n除计划外，必须遵守以下平台规则：\n{build_platform_guidance(plan.platform)}"
        if isinstance(plan, ContentPlan)
        else ""
    )
    brand_voice_guidance = (
        f"\n\n还必须遵守这组品牌写作规则：\n{plan.brand_voice}"
        if isinstance(plan, ContentPlan) and plan.brand_voice
        else ""
    )

    return [
        {"role": "system", "content": WRITER_INSTRUCTIONS},
        {
            "role": "user",
            "content": (
                f"请依据以下已确认计划写出初稿：\n\n{normalized_plan}"
                f"{platform_guidance}{brand_voice_guidance}"
            ),
        },
    ]


def create_draft(plan: str | ContentPlan, settings: Settings | None = None) -> str:
    """Request one Markdown draft from the configured DeepSeek model."""
    active_settings = settings or Settings.from_env()
    client = create_deepseek_client(
        active_settings,
        consumer_name="Writer",
        error_type=WriterConfigurationError,
    )
    response = client.chat.completions.create(
        model=active_settings.llm_model,
        messages=build_writer_messages(plan),
    )
    record_llm_usage(response, node="writer")
    content = response.choices[0].message.content
    if not content:
        raise RuntimeError("Writer returned an empty response.")
    return content


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate a ContentFlow AI draft from a plan file.")
    parser.add_argument("--plan-file", type=Path, required=True, help="Path to a confirmed Markdown plan.")
    args = parser.parse_args()
    print(create_draft(args.plan_file.read_text(encoding="utf-8")))


if __name__ == "__main__":
    main()
