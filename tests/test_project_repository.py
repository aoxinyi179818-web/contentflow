import pytest
from datetime import date

from contentflow.agents.research import ResearchResult
from contentflow.database.projects import DatabaseUrlError, ProjectRepository
from contentflow.models import (
    AdaptedContent,
    ContentPlan,
    ContentSection,
    ReviewReport,
    VisualAssetPlan,
    VisualPlan,
    PublishingAssets,
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


def test_repository_upserts_feedback_and_builds_a_quality_overview(tmp_path) -> None:
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

    repository.save_feedback(first.id, rating="需要改进", comment="请增加例子。")
    updated = repository.save_feedback(first.id, rating="有帮助", comment="已经清楚了。")
    repository.save_feedback(second.id, rating="需要改进")
    overview = repository.get_feedback_overview()

    assert repository.get_feedback(first.id) == updated
    assert overview.total_count == 2
    assert overview.helpful_count == 1
    assert overview.improvement_count == 1
    assert overview.helpful_rate == 50
    assert overview.average_review_score == 90
    assert {item.topic for item in overview.recent_items} == {"主题一", "主题二"}
    with pytest.raises(ValueError, match="project does not exist"):
        repository.save_feedback("missing", rating="有帮助")


def test_repository_keeps_one_adaptation_for_each_platform(tmp_path) -> None:
    repository = ProjectRepository(f"sqlite:///{(tmp_path / 'contentflow.db').as_posix()}")
    project = repository.save_project(
        topic="主题一",
        plan=make_plan(),
        draft="初稿一",
        review=make_review(),
        final_content="终稿一",
        status="completed",
    )
    xiaohongshu = AdaptedContent(
        platform="小红书笔记",
        title="学习笔记",
        content="短段落内容",
        format_notes=["短段落"],
    )
    ppt = AdaptedContent(
        platform="PPT 大纲",
        title="学习计划 PPT",
        content="第 1 页：目标",
        format_notes=["一页一个主题"],
    )

    repository.save_adaptation(project.id, xiaohongshu)
    repository.save_adaptation(project.id, ppt)
    repository.save_adaptation(project.id, xiaohongshu.model_copy(update={"title": "更新的学习笔记"}))
    loaded = repository.get_project(project.id)

    assert loaded is not None
    assert {item.content.platform for item in loaded.adaptations} == {"小红书笔记", "PPT 大纲"}
    assert next(item for item in loaded.adaptations if item.content.platform == "小红书笔记").content.title == "更新的学习笔记"


def test_repository_keeps_local_workbench_assets_without_changing_original_final(tmp_path) -> None:
    repository = ProjectRepository(f"sqlite:///{(tmp_path / 'contentflow.db').as_posix()}")
    project = repository.save_project(
        topic="主题一",
        plan=make_plan(),
        draft="初稿一",
        review=make_review(),
        final_content="原始终稿",
        status="completed",
    )
    voice = repository.save_brand_voice(name="克制专业", instructions="先说结论，避免夸张。")
    same_voice = repository.save_brand_voice(name="克制专业", instructions="短句，避免夸张。")
    idea = repository.create_topic_idea(
        title="下一个选题",
        notes="面向新手",
        platform="小红书笔记",
        status="创作中",
        scheduled_for=date(2026, 9, 20),
        project_id=project.id,
    )
    updated_idea = repository.update_topic_idea(idea.id, status="待发布", scheduled_for=None)
    assets = PublishingAssets(
        platform="小红书笔记",
        titles=["标题一", "标题二", "标题三"],
        cover_hooks=["一分钟看懂"],
        tags=["学习方法"],
        call_to_action="收藏后今晚试一次。",
    )
    repository.save_content_override(project.id, "人工编辑后的终稿")
    repository.save_publishing_assets(project.id, assets)
    loaded = repository.get_project(project.id)

    assert voice.id == same_voice.id
    assert repository.list_brand_voices()[0].instructions == "短句，避免夸张。"
    assert updated_idea.status == "待发布"
    assert updated_idea.scheduled_for is None
    assert repository.list_topic_ideas()[0].title == "下一个选题"
    assert loaded is not None
    assert loaded.final_content == "原始终稿"
    assert loaded.edited_content == "人工编辑后的终稿"
    assert loaded.publishing_assets[0].assets == assets
