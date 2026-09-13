from contentflow import mvp
from contentflow.config import Settings
from contentflow.models import ContentPlan, ContentPreferences, ContentSection, ReviewReport


def test_run_mvp_preserves_its_result_interface_with_quality_loop(monkeypatch) -> None:
    calls: list[str] = []
    settings = Settings(
        llm_provider="deepseek", deepseek_api_key="test-key", llm_model="test-model"
    )
    plan = ContentPlan(
        topic="测试主题",
        audience="大学生",
        tone="清晰",
        sections=[ContentSection(title=f"第{i}章", objective="解释一个步骤") for i in range(1, 6)],
    )
    reviews = [
        ReviewReport(
            score=70,
            summary="需要改写。",
            structure_score=20,
            clarity_score=20,
            audience_tone_score=20,
            completeness_score=10,
        ),
        ReviewReport(
            score=85,
            summary="改写后通过。",
            structure_score=20,
            clarity_score=20,
            audience_tone_score=20,
            completeness_score=25,
        ),
    ]

    def fake_plan(topic: str, *, settings: Settings) -> ContentPlan:
        calls.append(f"plan:{topic}")
        return plan

    def fake_draft(received_plan: ContentPlan, *, settings: Settings) -> str:
        assert received_plan is plan
        calls.append("draft")
        return "DRAFT"

    def fake_review(draft: str, *, settings: Settings) -> ReviewReport:
        calls.append(f"review:{draft}")
        return reviews.pop(0)

    def fake_rewrite(draft: str, review: ReviewReport, *, settings: Settings) -> str:
        calls.append(f"rewrite:{draft}:{review.score}")
        return "FINAL"

    monkeypatch.setattr(mvp, "create_plan", fake_plan)
    monkeypatch.setattr(mvp, "create_draft", fake_draft)
    monkeypatch.setattr(mvp, "review_draft", fake_review)
    monkeypatch.setattr(mvp, "rewrite_draft", fake_rewrite)

    result = mvp.run_mvp("测试主题", settings=settings)

    assert result.plan is plan
    assert result.draft == "DRAFT"
    assert result.review.score == 85
    assert result.final_content == "FINAL"
    assert calls == [
        "plan:测试主题",
        "draft",
        "review:DRAFT",
        "rewrite:DRAFT:70",
        "review:FINAL",
    ]


def test_run_mvp_passes_user_preferences_to_the_planner(monkeypatch) -> None:
    settings = Settings()
    preferences = ContentPreferences(
        audience="大学新生",
        tone="友好易懂",
        platform="短视频脚本",
        target_length="短（约 300 字）",
    )
    plan = ContentPlan(
        topic="测试主题",
        audience="大学新生",
        tone="友好易懂",
        platform="短视频脚本",
        target_length="短（约 300 字）",
        sections=[ContentSection(title=f"第{i}章", objective="解释一个步骤") for i in range(1, 6)],
    )
    review = ReviewReport(
        score=80,
        summary="通过。",
        structure_score=20,
        clarity_score=20,
        audience_tone_score=20,
        completeness_score=20,
    )

    def fake_plan(
        topic: str, *, settings: Settings, preferences: ContentPreferences
    ) -> ContentPlan:
        assert topic == "测试主题"
        assert preferences == expected_preferences
        return plan

    monkeypatch.setattr(mvp, "create_plan", fake_plan)
    monkeypatch.setattr(mvp, "create_draft", lambda plan, *, settings: "初稿")
    monkeypatch.setattr(mvp, "review_draft", lambda draft, *, settings: review)
    monkeypatch.setattr(
        mvp, "rewrite_draft", lambda draft, review, *, settings: "修订稿"
    )

    expected_preferences = preferences
    result = mvp.run_mvp("测试主题", settings=settings, preferences=expected_preferences)

    assert result.plan.platform == "短视频脚本"
