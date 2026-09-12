import pytest

from contentflow.adapter import AdapterInputError, build_adapter_messages


def test_adapter_rejects_empty_final_content() -> None:
    with pytest.raises(AdapterInputError, match="Final content must not be empty"):
        build_adapter_messages("  ", platform="社交媒体文案")


def test_adapter_rejects_an_unknown_platform() -> None:
    with pytest.raises(AdapterInputError, match="Unsupported platform"):
        build_adapter_messages("已审核内容", platform="邮件")


def test_adapter_messages_constrain_platform_and_preserve_source_boundary() -> None:
    content = "# 学习计划\n\n每天安排两个专注时段。"
    messages = build_adapter_messages(content, platform="PPT 大纲", audience="大学生")

    assert messages[0]["role"] == "system"
    assert "不补充" in messages[0]["content"]
    assert "JSON" in messages[0]["content"]
    assert messages[1]["role"] == "user"
    assert "目标平台：PPT 大纲" in messages[1]["content"]
    assert "目标受众：大学生" in messages[1]["content"]
    assert content in messages[1]["content"]
