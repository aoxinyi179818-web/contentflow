"""A no-LLM LangGraph concept demo for ContentFlow Step 30."""

import json
from operator import add
from typing import Annotated, NotRequired, TypedDict

from langgraph.graph import END, START, StateGraph


class LearningState(TypedDict):
    """Shared state for the isolated State, Node, and Edge exercise."""

    topic: str
    plan: NotRequired[str]
    draft: NotRequired[str]
    events: Annotated[list[str], add]


def planner_node(state: LearningState) -> dict[str, object]:
    """Read the topic and return only Planner-owned state updates."""
    topic = state["topic"]
    return {
        "plan": f"围绕“{topic}”设计三个要点：背景、方法、行动建议。",
        "events": ["planner: 已写入内容计划"],
    }


def writer_node(state: LearningState) -> dict[str, object]:
    """Read the plan produced upstream and return Writer-owned updates."""
    plan = state["plan"]
    return {
        "draft": f"初稿依据以下计划生成：{plan}",
        "events": ["writer: 已读取计划并写入初稿"],
    }


def build_learning_graph():
    """Build the smallest fixed path: START -> planner -> writer -> END."""
    builder = StateGraph(LearningState)
    builder.add_node("planner", planner_node)
    builder.add_node("writer", writer_node)
    builder.add_edge(START, "planner")
    builder.add_edge("planner", "writer")
    builder.add_edge("writer", END)
    return builder.compile()


def run_demo(topic: str) -> LearningState:
    """Run the isolated graph without calling any model or external service."""
    normalized_topic = topic.strip()
    if not normalized_topic:
        raise ValueError("topic must not be empty")
    return build_learning_graph().invoke({"topic": normalized_topic, "events": []})


def main() -> None:
    result = run_demo("大学生如何建立可持续学习习惯")
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
