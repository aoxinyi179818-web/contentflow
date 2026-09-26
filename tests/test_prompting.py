import pytest

from contentflow.adapter import ADAPTER_INSTRUCTIONS
from contentflow.agents.visual import VISUAL_INSTRUCTIONS
from contentflow.editor import EDITOR_INSTRUCTIONS
from contentflow.packaging import PACKAGING_INSTRUCTIONS
from contentflow.planner import PLANNER_INSTRUCTIONS
from contentflow.prompting import PROMPT_NAMES, PromptNotFoundError, load_prompt
from contentflow.reviewer import REVIEWER_INSTRUCTIONS
from contentflow.rewriter import REWRITER_INSTRUCTIONS
from contentflow.writer import WRITER_INSTRUCTIONS


def test_load_prompt_returns_every_current_node_prompt() -> None:
    assert PROMPT_NAMES == {
        "planner", "writer", "reviewer", "rewriter", "adapter", "visual", "editor", "packaging"
    }

    for name in PROMPT_NAMES:
        assert load_prompt(name)


def test_nodes_use_their_matching_prompt_files() -> None:
    assert PLANNER_INSTRUCTIONS == load_prompt("planner")
    assert WRITER_INSTRUCTIONS == load_prompt("writer")
    assert REVIEWER_INSTRUCTIONS == load_prompt("reviewer")
    assert REWRITER_INSTRUCTIONS == load_prompt("rewriter")
    assert ADAPTER_INSTRUCTIONS == load_prompt("adapter")
    assert VISUAL_INSTRUCTIONS == load_prompt("visual")
    assert EDITOR_INSTRUCTIONS == load_prompt("editor")
    assert PACKAGING_INSTRUCTIONS == load_prompt("packaging")


def test_load_prompt_rejects_unknown_names() -> None:
    with pytest.raises(PromptNotFoundError, match="Unknown ContentFlow prompt"):
        load_prompt("../../.env")
