from contentflow.export import (
    default_export_stem,
    render_content_package_markdown,
    sanitize_export_stem,
)
from contentflow.models import (
    AdaptedContent,
    ContentPlan,
    ContentSection,
    ReviewProblem,
    ReviewReport,
)
from contentflow.mvp import MvpResult


def _result() -> MvpResult:
    return MvpResult(
        plan=ContentPlan(
            topic="为新生建立学习习惯",
            audience="大学新生",
            tone="鼓励且清晰",
            sections=[ContentSection(title=f"第 {number} 部分", objective="说明一个行动") for number in range(1, 6)],
        ),
        draft="这里是初稿。",
        review=ReviewReport(
            score=80,
            summary="结构完整，还需补充例子。",
            structure_score=20,
            clarity_score=20,
            audience_tone_score=20,
            completeness_score=20,
            problems=[
                ReviewProblem(
                    problem_type="例子不足",
                    severity="中",
                    location="第二部分",
                    reason="行动建议缺少场景。",
                    suggestion="补充一个新生的日常例子。",
                )
            ],
            priority_suggestions=["补充一个可执行的示例。"],
        ),
        final_content="这里是修订稿。",
        status="completed",
        adaptations=(
            AdaptedContent(
                platform="小红书笔记",
                title="学习习惯笔记",
                content="这里是平台版本。",
                format_notes=["短段落"],
            ),
        ),
    )


def test_sanitize_export_stem_removes_path_and_windows_invalid_characters() -> None:
    filename = sanitize_export_stem(" ../../学习:计划? ")

    assert "/" not in filename
    assert "\\" not in filename
    assert ":" not in filename
    assert "?" not in filename
    assert ".." not in filename


def test_default_export_stem_uses_the_topic() -> None:
    assert default_export_stem("学习计划") == "contentflow-学习计划"


def test_content_package_contains_each_workflow_artifact() -> None:
    package = render_content_package_markdown(_result())

    assert "# ContentFlow AI 内容包" in package
    assert "为新生建立学习习惯" in package
    assert "这里是初稿。" in package
    assert "总分：80/100" in package
    assert "例子不足" in package
    assert "这里是修订稿。" in package
    assert "平台版本：小红书笔记" in package
    assert "这里是平台版本。" in package
