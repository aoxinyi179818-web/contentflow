import pytest

from contentflow.reviewer import ReviewerInputError, build_reviewer_messages


def test_build_reviewer_messages_rejects_an_empty_draft() -> None:
    with pytest.raises(ReviewerInputError, match="Draft must not be empty"):
        build_reviewer_messages("\n  ")


def test_build_reviewer_messages_requires_actionable_review_sections() -> None:
    messages = build_reviewer_messages("# 初稿\n\n这是需要审阅的内容。")
    prompt = messages[0]["content"]

    assert '"score"' in prompt
    assert "问题清单" in prompt
    assert "待核实" in prompt
    assert "JSON" in prompt
    assert messages[1]["role"] == "user"
