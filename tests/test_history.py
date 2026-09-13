from datetime import UTC, datetime

from contentflow.database.projects import ProjectRecord, ProjectSummary
from contentflow.history import format_project_label, result_from_project_record
from contentflow.models import ContentPlan, ContentSection, ReviewReport


def _plan() -> ContentPlan:
    return ContentPlan(
        topic="新生学习计划",
        audience="大学新生",
        tone="清晰",
        sections=[ContentSection(title=f"第 {index} 部分", objective="说明一个行动") for index in range(1, 6)],
    )


def _review() -> ReviewReport:
    return ReviewReport(
        score=80,
        summary="内容完整。",
        structure_score=20,
        clarity_score=20,
        audience_tone_score=20,
        completeness_score=20,
    )


def test_format_project_label_contains_human_readable_metadata() -> None:
    summary = ProjectSummary(
        id="project-1",
        topic="新生学习计划",
        status="completed",
        created_at=datetime(2026, 9, 13, 8, 30, tzinfo=UTC),
    )

    label = format_project_label(summary)

    assert "新生学习计划" in label
    assert "已完成" in label
    assert "2026-09-13" in label


def test_result_from_project_record_keeps_the_viewer_artifacts() -> None:
    record = ProjectRecord(
        id="project-1",
        topic="新生学习计划",
        plan=_plan(),
        research=None,
        draft="初稿",
        review=_review(),
        final_content="修订稿",
        adapted_content=None,
        visual_plan=None,
        status="completed",
        created_at=datetime(2026, 9, 13, tzinfo=UTC),
    )

    result = result_from_project_record(record)

    assert result.plan == record.plan
    assert result.draft == "初稿"
    assert result.review == record.review
    assert result.final_content == "修订稿"
    assert result.metrics is None
    assert result.project_id == "project-1"
