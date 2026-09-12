from contentflow import mvp
from contentflow.config import Settings
from contentflow.models import ContentPlan, ContentSection, ReviewReport


def test_run_mvp_passes_structured_artifacts_to_downstream_nodes(monkeypatch) -> None:
    settings = Settings(
        llm_provider="deepseek", deepseek_api_key="test-key", llm_model="test-model"
    )
    plan = ContentPlan(
        topic="测试主题",
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

    def fake_plan(topic: str, *, settings: Settings) -> ContentPlan:
        assert topic == "测试主题"
        return plan

    def fake_draft(received_plan: ContentPlan, *, settings: Settings) -> str:
        assert received_plan is plan
        return "DRAFT"

    def fake_review(draft: str, *, settings: Settings) -> ReviewReport:
        assert draft == "DRAFT"
        return review

    def fake_rewrite(draft: str, received_review: ReviewReport, *, settings: Settings) -> str:
        assert draft == "DRAFT"
        assert received_review is review
        return "FINAL"

    monkeypatch.setattr(mvp, "create_plan", fake_plan)
    monkeypatch.setattr(mvp, "create_draft", fake_draft)
    monkeypatch.setattr(mvp, "review_draft", fake_review)
    monkeypatch.setattr(mvp, "rewrite_draft", fake_rewrite)

    result = mvp.run_mvp("测试主题", settings=settings)

    assert result.plan is plan
    assert result.review is review
    assert result.final_content == "DRAFT"
