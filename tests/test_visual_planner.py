import pytest

from contentflow.agents.visual import (
    VisualPlannerInputError,
    build_visual_messages,
    validate_visual_plan,
)
from contentflow.models import VisualAssetPlan, VisualPlan


def test_visual_planner_rejects_empty_content_and_invalid_limit() -> None:
    with pytest.raises(VisualPlannerInputError, match="Final content must not be empty"):
        build_visual_messages("  ")
    with pytest.raises(VisualPlannerInputError, match="max_assets must be between 1 and 5"):
        build_visual_messages("内容", max_assets=6)


def test_visual_messages_specify_the_tool_selection_rules() -> None:
    content = "# 学习计划\n\n每天安排两个专注时段。"
    messages = build_visual_messages(content, max_assets=2)

    assert messages[0]["role"] == "system"
    assert "image_search" in messages[0]["content"]
    assert "不得为图表编造数据" in messages[0]["content"]
    assert messages[1]["role"] == "user"
    assert "最多规划 2 个视觉素材" in messages[1]["content"]
    assert content in messages[1]["content"]


def test_visual_plan_requires_grounded_anchors_and_respects_budget() -> None:
    content = "# 学习计划\n\n每天安排两个专注时段。"
    grounded = VisualPlan(
        overview="用一张概念插画说明专注时段。",
        assets=[
            VisualAssetPlan(
                section_anchor="每天安排两个专注时段",
                purpose="帮助读者理解时间块安排。",
                asset_type="image",
                tool="image_generation",
                query_or_prompt="简洁扁平插画，展示两个专注学习时间块。",
                rationale="这是抽象学习方法，适合示意插画。",
            )
        ],
    )
    assert validate_visual_plan(grounded, content, max_assets=1) is grounded

    ungrounded = grounded.model_copy(
        update={"assets": [grounded.assets[0].model_copy(update={"section_anchor": "不存在"})]}
    )
    with pytest.raises(RuntimeError, match="anchors"):
        validate_visual_plan(ungrounded, content, max_assets=1)
