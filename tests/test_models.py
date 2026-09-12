import pytest
from pydantic import ValidationError

from contentflow.models import ContentPlan, ReviewReport


def test_content_plan_requires_five_to_seven_sections() -> None:
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

    with pytest.raises(ValidationError, match="List should have at least 5 items"):
        ContentPlan.model_validate(
            {
                "topic": "AI 学习入门",
                "audience": "大学生",
                "tone": "清晰",
                "sections": [{"title": "第一章", "objective": "解释一个学习步骤"}],
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
