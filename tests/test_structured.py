import pytest

from contentflow.models import ContentPlan
from contentflow.structured import StructuredOutputError, parse_structured_output


def test_parse_structured_output_returns_a_validated_model() -> None:
    content = """{
        "topic": "AI 学习入门",
        "audience": "大学生",
        "tone": "清晰",
        "sections": [
            {"title": "第一章", "objective": "建立整体认识"},
            {"title": "第二章", "objective": "解释基础概念"},
            {"title": "第三章", "objective": "给出实践方法"},
            {"title": "第四章", "objective": "说明使用边界"},
            {"title": "第五章", "objective": "给出行动建议"}
        ]
    }"""

    plan = parse_structured_output(content, ContentPlan)

    assert plan.topic == "AI 学习入门"
    assert plan.sections[0].title == "第一章"


def test_parse_structured_output_explains_invalid_json() -> None:
    with pytest.raises(StructuredOutputError, match="Invalid ContentPlan JSON response"):
        parse_structured_output('{"topic": "缺字段"}', ContentPlan)
