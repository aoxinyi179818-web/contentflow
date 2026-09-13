from contentflow import mvp
from contentflow.config import Settings
from contentflow.database import ProjectRepository
from contentflow.models import ContentPlan, ContentSection, ReviewReport


def test_run_mvp_persists_completed_artifacts_when_repository_is_provided(
    monkeypatch, tmp_path
) -> None:
    plan = ContentPlan(
        topic="测试主题",
        audience="大学生",
        tone="清晰",
        sections=[ContentSection(title=f"部分{i}", objective="说明") for i in range(5)],
    )
    review = ReviewReport(
        score=90,
        summary="通过",
        structure_score=25,
        clarity_score=25,
        audience_tone_score=20,
        completeness_score=20,
    )
    monkeypatch.setattr(
        mvp,
        "run_contentflow_graph",
        lambda topic, *, settings, services, run_id: {
            "plan": plan,
            "draft": "初稿",
            "review": review,
            "final_content": "终稿",
            "status": "completed",
        },
    )
    repository = ProjectRepository(f"sqlite:///{(tmp_path / 'contentflow.db').as_posix()}")

    result = mvp.run_mvp("测试主题", settings=Settings(), repository=repository)
    summaries = repository.list_recent_projects()
    loaded = repository.get_project(summaries[0].id)

    assert result.final_content == "终稿"
    assert result.status == "completed"
    assert loaded is not None
    assert result.project_id == loaded.id
    assert loaded.topic == "测试主题"
    assert loaded.final_content == "终稿"
