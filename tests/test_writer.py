import pytest

from contentflow.models import ContentPlan, ContentSection
from contentflow.writer import WriterInputError, build_writer_messages


def test_build_writer_messages_rejects_an_empty_plan() -> None:
    with pytest.raises(WriterInputError, match="Confirmed plan must not be empty"):
        build_writer_messages("  \n")


def test_build_writer_messages_contains_the_confirmed_plan() -> None:
    plan = "# 内容计划\n\n## 第一章\n解释核心概念。"

    messages = build_writer_messages(plan)

    assert messages[0]["role"] == "system"
    assert "不要编造来源" in messages[0]["content"]
    assert messages[1]["role"] == "user"
    assert plan in messages[1]["content"]


def test_writer_messages_include_platform_native_rules_for_structured_plans() -> None:
    plan = ContentPlan(
        topic="学习方法",
        audience="大学新生",
        tone="友好易懂",
        platform="小红书笔记",
        sections=[ContentSection(title=f"部分{index}", objective="短内容表达") for index in range(4)],
    )

    message = build_writer_messages(plan)[1]["content"]

    assert "小红书笔记" in message
    assert "封面标题" in message
    assert "不要改写成传统长文章" in message
