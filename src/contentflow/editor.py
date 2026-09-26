"""Focused, user-directed edits for an already reviewed content package."""

from contentflow.config import Settings
from contentflow.llm_client import create_deepseek_client
from contentflow.observability import record_llm_usage
from contentflow.prompting import load_prompt


class EditorInputError(ValueError):
    """Raised when a targeted edit cannot be applied safely."""


class EditorConfigurationError(RuntimeError):
    """Raised when the configured LLM cannot run the content editor."""


EDITOR_INSTRUCTIONS = load_prompt("editor")


def replace_selected_text(content: str, selected_text: str, replacement: str) -> str:
    """Replace one exact user-selected excerpt, avoiding ambiguous mass replacements."""
    normalized_content = content.strip()
    normalized_selected = selected_text.strip()
    normalized_replacement = replacement.strip()
    if not normalized_content or not normalized_selected or not normalized_replacement:
        raise EditorInputError("content, selected_text, and replacement must not be empty")
    occurrences = normalized_content.count(normalized_selected)
    if occurrences != 1:
        raise EditorInputError("selected_text must appear exactly once in the current content")
    return normalized_content.replace(normalized_selected, normalized_replacement, 1)


def build_editor_messages(
    content: str, instruction: str, *, selected_text: str | None = None
) -> list[dict[str, str]]:
    """Build a bounded edit request; selected edits are returned as replacement text only."""
    normalized_content = content.strip()
    normalized_instruction = instruction.strip()
    normalized_selected = selected_text.strip() if selected_text else ""
    if not normalized_content:
        raise EditorInputError("content must not be empty")
    if not normalized_instruction:
        raise EditorInputError("instruction must not be empty")
    if len(normalized_content) > 20_000:
        raise EditorInputError("content must not exceed 20000 characters")
    request = (
        f"改写要求：{normalized_instruction}\n\n"
        f"当前内容：\n\n{normalized_content}"
    )
    if normalized_selected:
        if normalized_selected not in normalized_content:
            raise EditorInputError("selected_text must appear in the current content")
        request += f"\n\n指定替换片段：\n{normalized_selected}\n\n只返回这一片段的替换文本。"
    else:
        request += "\n\n请返回完整修订后的 Markdown 正文。"
    return [{"role": "system", "content": EDITOR_INSTRUCTIONS}, {"role": "user", "content": request}]


def rewrite_with_instruction(
    content: str,
    instruction: str,
    *,
    selected_text: str | None = None,
    settings: Settings | None = None,
) -> str:
    """Request a full rewrite or a safe replacement for a user-selected excerpt."""
    active_settings = settings or Settings.from_env()
    client = create_deepseek_client(
        active_settings,
        consumer_name="Content Editor",
        error_type=EditorConfigurationError,
    )
    response = client.chat.completions.create(
        model=active_settings.llm_model,
        messages=build_editor_messages(content, instruction, selected_text=selected_text),
    )
    record_llm_usage(response, node="content_editor")
    rewritten = response.choices[0].message.content
    if not rewritten or not rewritten.strip():
        raise RuntimeError("Content Editor returned an empty response.")
    return (
        replace_selected_text(content, selected_text, rewritten)
        if selected_text and selected_text.strip()
        else rewritten.strip()
    )
