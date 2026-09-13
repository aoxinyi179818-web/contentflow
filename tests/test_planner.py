import pytest

from contentflow.models import ContentPreferences
from contentflow.planner import PlannerInputError, build_planner_messages


def test_build_planner_messages_rejects_an_empty_topic() -> None:
    with pytest.raises(PlannerInputError, match="Topic must not be empty"):
        build_planner_messages("   ")


def test_build_planner_messages_contains_the_requested_topic() -> None:
    messages = build_planner_messages("AI 学习方法")

    assert messages[0]["role"] == "system"
    assert "JSON" in messages[0]["content"]
    assert '"sections"' in messages[0]["content"]
    assert "章节" in messages[0]["content"]
    assert messages[1]["role"] == "user"
    assert "AI 学习方法" in messages[1]["content"]


def test_build_planner_messages_includes_confirmed_content_preferences() -> None:
    preferences = ContentPreferences(
        audience="大学新生",
        tone="友好易懂",
        platform="短视频脚本",
        target_length="短（约 300 字）",
    )

    message = build_planner_messages("学习方法", preferences=preferences)[1]["content"]

    assert "大学新生" in message
    assert "友好易懂" in message
    assert "短视频脚本" in message
    assert "短（约 300 字）" in message
