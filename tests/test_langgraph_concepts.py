"""Tests for the isolated LangGraph concepts exercise."""

import pytest

from tools.langgraph_state_node_edge_demo import run_demo


def test_learning_graph_passes_state_between_nodes() -> None:
    result = run_demo("大学生学习方法")

    assert result["topic"] == "大学生学习方法"
    assert "大学生学习方法" in result["plan"]
    assert result["plan"] in result["draft"]
    assert result["events"] == [
        "planner: 已写入内容计划",
        "writer: 已读取计划并写入初稿",
    ]


def test_learning_graph_rejects_empty_topic() -> None:
    with pytest.raises(ValueError, match="topic must not be empty"):
        run_demo("   ")
