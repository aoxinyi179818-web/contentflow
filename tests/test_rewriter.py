import pytest

from contentflow.rewriter import RewriterInputError, build_rewriter_messages


def test_build_rewriter_messages_rejects_empty_input() -> None:
    with pytest.raises(RewriterInputError, match="Draft must not be empty"):
        build_rewriter_messages("\n  ", "# 审阅报告")

    with pytest.raises(RewriterInputError, match="Review report must not be empty"):
        build_rewriter_messages("# 初稿", "\n  ")


def test_build_rewriter_messages_contains_source_text_and_safety_boundary() -> None:
    draft = "# AI 学习指南\n\n请先核对课程规则。"
    review = "# 审阅报告\n\n请删除绝对化说法，并标记待核实信息。"

    messages = build_rewriter_messages(draft, review)

    assert messages[0]["role"] == "system"
    assert "待核实" in messages[0]["content"]
    assert "只输出修订后的 Markdown 正文" in messages[0]["content"]
    assert messages[1]["role"] == "user"
    assert draft in messages[1]["content"]
    assert review in messages[1]["content"]
