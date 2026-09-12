import pytest

from contentflow.agents.research import ResearchResult
from contentflow.database.projects import DatabaseUrlError, ProjectRepository
from contentflow.models import (
    AdaptedContent,
    ContentPlan,
    ContentSection,
    ReviewReport,
    VisualAssetPlan,
    VisualPlan,
)
from contentflow.tools.local_research import ResearchSource


def make_plan() -> ContentPlan:
    return ContentPlan(
        topic="复习",
        audience="大学生",
        tone="清晰",
        sections=[ContentSection(title=f"部分{i}", objective="说明") for i in range(5)],
    )


def make_review() -> ReviewReport:
    return ReviewReport(
        score=90,
        summary="通过",
        structure_score=25,
        clarity_score=25,
        audience_tone_score=20,
        completeness_score=20,
        evidence_score=20,
    )


def test_repository_round_trips_every_project_artifact(tmp_path) -> None:
    repository = ProjectRepository(f"sqlite:///{(tmp_path / 'contentflow.db').as_posix()}")
    research = ResearchResult(
        answer="资料结论",
        sources=[
            ResearchSource(
                source_id="study",
                title="学习计划",
                url="https://example.invalid/study",
                summary="复习任务应拆分为时间块。",
            )
        ],
    )
    adapted = AdaptedContent(
        platform="PPT 大纲",
        title="复习计划 PPT",
        content="第 1 页：目标",
        format_notes=["每页一个主题"],
    )
    visual = VisualPlan(
        overview="一张学习时间块插画。",
        assets=[
            VisualAssetPlan(
                section_anchor="专注时段",
                purpose="说明时间安排。",
                asset_type="image",
                tool="image_generation",
                query_or_prompt="学习时间块插画",
                rationale="抽象概念适合插画。",
            )
        ],
    )

    saved = repository.save_project(
        topic="复习",
        plan=make_plan(),
        research=research,
        draft="初稿内容",
        review=make_review(),
        final_content="最终内容：专注时段。",
        adapted_content=adapted,
        visual_plan=visual,
        status="completed",
    )
    loaded = repository.get_project(saved.id)

    assert loaded == saved
    assert loaded is not None
    assert loaded.research is not None
    assert loaded.adapted_content is not None
    assert loaded.visual_plan is not None


def test_repository_lists_recent_projects_and_validates_inputs(tmp_path) -> None:
    repository = ProjectRepository(f"sqlite:///{(tmp_path / 'contentflow.db').as_posix()}")
    first = repository.save_project(
        topic="主题一",
        plan=make_plan(),
        draft="初稿一",
        review=make_review(),
        final_content="终稿一",
        status="completed",
    )
    second = repository.save_project(
        topic="主题二",
        plan=make_plan(),
        draft="初稿二",
        review=make_review(),
        final_content="终稿二",
        status="completed",
    )

    summaries = repository.list_recent_projects(limit=2)

    assert {summary.id for summary in summaries} == {first.id, second.id}
    assert repository.get_project("missing") is None
    with pytest.raises(ValueError, match="limit must be between 1 and 100"):
        repository.list_recent_projects(limit=0)
    with pytest.raises(DatabaseUrlError, match="sqlite"):
        ProjectRepository("postgresql://example")
