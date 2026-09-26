import pytest

from contentflow.packaging import PackagingInputError, build_packaging_messages


def test_packaging_messages_are_grounded_in_current_content() -> None:
    messages = build_packaging_messages("# 学习计划\n\n每天复盘十分钟。", platform="小红书笔记")

    assert messages[0]["role"] == "system"
    assert "不得加入原文没有依据" in messages[0]["content"]
    assert "小红书笔记" in messages[1]["content"]
    assert "每天复盘十分钟" in messages[1]["content"]


def test_packaging_rejects_empty_content() -> None:
    with pytest.raises(PackagingInputError, match="must not be empty"):
        build_packaging_messages(" ", platform="长文章")
