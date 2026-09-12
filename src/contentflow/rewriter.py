"""Minimal draft-rewriting node for ContentFlow AI Step 24."""

import argparse
from pathlib import Path

from contentflow.config import Settings
from contentflow.llm_client import create_deepseek_client
from contentflow.models import ReviewReport
from contentflow.observability import record_llm_usage
from contentflow.prompting import load_prompt


class RewriterInputError(ValueError):
    """Raised when the Rewriter receives unusable text input."""


class RewriterConfigurationError(RuntimeError):
    """Raised when the configured LLM cannot run the Rewriter."""


REWRITER_INSTRUCTIONS = load_prompt("rewriter")


def build_rewriter_messages(draft: str, review: str | ReviewReport) -> list[dict[str, str]]:
    """Validate draft and review text, then build the Rewriter request."""
    normalized_draft = draft.strip()
    normalized_review = review.model_dump_json(indent=2) if isinstance(review, ReviewReport) else review.strip()
    if not normalized_draft:
        raise RewriterInputError("Draft must not be empty.")
    if not normalized_review:
        raise RewriterInputError("Review report must not be empty.")

    return [
        {"role": "system", "content": REWRITER_INSTRUCTIONS},
        {
            "role": "user",
            "content": (
                "原始初稿：\n\n"
                f"{normalized_draft}\n\n"
                "Reviewer 审阅报告：\n\n"
                f"{normalized_review}\n\n"
                "请输出修订后的 Markdown 正文。"
            ),
        },
    ]


def rewrite_draft(draft: str, review: str | ReviewReport, settings: Settings | None = None) -> str:
    """Request one revised Markdown draft from the configured DeepSeek model."""
    active_settings = settings or Settings.from_env()
    client = create_deepseek_client(
        active_settings,
        consumer_name="Rewriter",
        error_type=RewriterConfigurationError,
    )
    response = client.chat.completions.create(
        model=active_settings.llm_model,
        messages=build_rewriter_messages(draft, review),
    )
    record_llm_usage(response, node="rewrite")
    content = response.choices[0].message.content
    if not content:
        raise RuntimeError("Rewriter returned an empty response.")
    return content


def main() -> None:
    parser = argparse.ArgumentParser(description="Rewrite a ContentFlow AI draft from a review report.")
    parser.add_argument("--draft-file", type=Path, required=True, help="Path to the original Markdown draft.")
    parser.add_argument("--review-file", type=Path, required=True, help="Path to the Markdown review report.")
    args = parser.parse_args()
    print(
        rewrite_draft(
            args.draft_file.read_text(encoding="utf-8"),
            args.review_file.read_text(encoding="utf-8"),
        )
    )


if __name__ == "__main__":
    main()
