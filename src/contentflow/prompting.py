"""Load versioned, repository-owned prompts for ContentFlow nodes."""

from pathlib import Path

from contentflow.safe_files import read_allowed_text


class PromptNotFoundError(FileNotFoundError):
    """Raised when code requests a prompt that is not part of the application."""


PROMPT_NAMES = frozenset(
    {"planner", "writer", "reviewer", "rewriter", "adapter", "visual", "editor", "packaging"}
)
PROMPTS_DIRECTORY = Path(__file__).resolve().parents[2] / "prompts"


def load_prompt(name: str) -> str:
    """Return a non-empty prompt by approved name without accepting file paths."""
    if name not in PROMPT_NAMES:
        raise PromptNotFoundError(f"Unknown ContentFlow prompt: {name}")

    content = read_allowed_text(
        PROMPTS_DIRECTORY / f"{name}.md",
        allowed_root=PROMPTS_DIRECTORY,
        allowed_suffixes={".md"},
    ).strip()
    if not content:
        raise PromptNotFoundError(f"ContentFlow prompt is empty: {name}")
    return content
