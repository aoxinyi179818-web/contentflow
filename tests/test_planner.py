import pytest

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
