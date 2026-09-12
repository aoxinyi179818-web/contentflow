"""Minimal draft-review node for ContentFlow AI Step 23."""

import argparse
from pathlib import Path

from contentflow.config import Settings
from contentflow.llm_client import create_deepseek_client
from contentflow.models import ReviewReport
from contentflow.observability import record_llm_usage
from contentflow.prompting import load_prompt
from contentflow.structured import parse_structured_output


class ReviewerInputError(ValueError):
    """Raised when the Reviewer receives an unusable draft."""


class ReviewerConfigurationError(RuntimeError):
    """Raised when the configured LLM cannot run the Reviewer."""


REVIEWER_INSTRUCTIONS = load_prompt("reviewer")


def build_reviewer_messages(
    draft: str, research_context: str | None = None
) -> list[dict[str, str]]:
    """Validate a draft and build the first Reviewer request."""
    normalized_draft = draft.strip()
    if not normalized_draft:
        raise ReviewerInputError("Draft must not be empty.")

    context = research_context.strip() if research_context else "未提供 Research Context。"
    return [
        {"role": "system", "content": REVIEWER_INSTRUCTIONS},
        {
            "role": "user",
            "content": f"请审阅以下初稿：\n\n{normalized_draft}\n\nResearch Context：\n\n{context}",
        },
    ]


def review_draft(draft: str, settings: Settings | None = None) -> ReviewReport:
    """Request and validate one structured review report from DeepSeek."""
    active_settings = settings or Settings.from_env()
    client = create_deepseek_client(
        active_settings,
        consumer_name="Reviewer",
        error_type=ReviewerConfigurationError,
    )
    response = client.chat.completions.create(
        model=active_settings.llm_model,
        messages=build_reviewer_messages(draft),
        response_format={"type": "json_object"},
        max_tokens=2500,
    )
    record_llm_usage(response, node="reviewer")
    content = response.choices[0].message.content
    if not content:
        raise RuntimeError("Reviewer returned an empty response.")
    return parse_structured_output(content, ReviewReport)


def main() -> None:
    parser = argparse.ArgumentParser(description="Review a ContentFlow AI draft.")
    parser.add_argument("--draft-file", type=Path, required=True, help="Path to a Markdown draft.")
    args = parser.parse_args()
    print(review_draft(args.draft_file.read_text(encoding="utf-8")).model_dump_json(indent=2))


if __name__ == "__main__":
    main()
