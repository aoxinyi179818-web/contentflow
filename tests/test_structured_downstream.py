from contentflow.models import ContentPlan, ContentSection, ReviewReport
from contentflow.rewriter import build_rewriter_messages
from contentflow.writer import build_writer_messages


def test_writer_and_rewriter_serialize_structured_artifacts() -> None:
    plan = ContentPlan(
        topic="AI 学习入门",
        audience="大学生",
        tone="清晰",
        sections=[ContentSection(title=f"第{i}章", objective="解释一个步骤") for i in range(1, 6)],
    )
    review = ReviewReport(
        score=80,
        summary="结构完整。",
        structure_score=20,
        clarity_score=20,
        audience_tone_score=20,
        completeness_score=20,
    )

    writer_messages = build_writer_messages(plan)
    rewriter_messages = build_rewriter_messages("# 初稿", review)

    assert '"topic": "AI 学习入门"' in writer_messages[1]["content"]
    assert '"score": 80' in rewriter_messages[1]["content"]
