import pytest

from contentflow.writer import WriterInputError, build_writer_messages


def test_build_writer_messages_rejects_an_empty_plan() -> None:
    with pytest.raises(WriterInputError, match="Confirmed plan must not be empty"):
        build_writer_messages("  \n")


def test_build_writer_messages_contains_the_confirmed_plan() -> None:
    plan = "# 内容计划\n\n## 第一章\n解释核心概念。"

    messages = build_writer_messages(plan)

    assert messages[0]["role"] == "system"
    assert "不要编造来源" in messages[0]["content"]
    assert messages[1]["role"] == "user"
    assert plan in messages[1]["content"]
