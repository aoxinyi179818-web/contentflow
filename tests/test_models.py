import pytest
from pydantic import ValidationError

from contentflow.models import ContentPlan, ReviewReport


def test_long_article_plan_requires_five_to_seven_sections() -> None:
    plan = ContentPlan.model_validate(
        {
            "topic": "AI 学习入门",
            "audience": "大学生",
            "tone": "清晰",
            "sections": [
                {"title": f"第{i}章", "objective": "解释一个学习步骤"}
                for i in range(1, 6)
            ],
        }
    )

    assert len(plan.sections) == 5

    with pytest.raises(ValidationError, match="长文章 plan must contain 5 to 7 sections"):
        ContentPlan.model_validate(
            {
                "topic": "AI 学习入门",
                "audience": "大学生",
                "tone": "清晰",
                "sections": [{"title": "第一章", "objective": "解释一个学习步骤"}],
            }
        )


def test_platform_native_plans_use_platform_specific_section_ranges() -> None:
    xiaohongshu = ContentPlan.model_validate(
        {
            "topic": "学习方法",
            "audience": "大学生",
            "tone": "友好易懂",
            "platform": "小红书笔记",
            "sections": [
                {"title": title, "objective": "用短内容表达"}
                for title in ("封面标题", "核心方法", "行动步骤", "互动收尾")
            ],
        }
    )

    assert len(xiaohongshu.sections) == 4
    with pytest.raises(ValidationError, match="短视频脚本 plan must contain 4 to 6 sections"):
        ContentPlan.model_validate(
            {
                "topic": "学习方法",
                "audience": "大学生",
                "tone": "友好易懂",
                "platform": "短视频脚本",
                "sections": [{"title": "钩子", "objective": "吸引观看"}] * 3,
            }
        )


def test_review_report_rejects_scores_outside_the_contract() -> None:
    with pytest.raises(ValidationError, match="less than or equal to 100"):
        ReviewReport.model_validate(
            {
                "score": 101,
                "summary": "内容完整。",
                "structure_score": 20,
                "clarity_score": 20,
                "audience_tone_score": 20,
                "completeness_score": 20,
            }
        )


def test_review_report_requires_total_score_to_match_dimension_scores() -> None:
    with pytest.raises(ValidationError, match="score must equal the sum"):
        ReviewReport.model_validate(
            {
                "score": 80,
                "summary": "内容完整。",
                "structure_score": 20,
                "clarity_score": 20,
                "audience_tone_score": 20,
                "completeness_score": 19,
            }
        )
