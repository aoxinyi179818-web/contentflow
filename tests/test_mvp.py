from contentflow import mvp
from contentflow.config import Settings
from contentflow.models import ContentPlan, ContentPreferences, ContentSection, ReviewReport
from contentflow.tools.local_research import ResearchSource
from contentflow.web_sources import WebReferenceCollection


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


def test_run_mvp_passes_user_web_references_to_every_generation_node(monkeypatch) -> None:
    plan = ContentPlan(
        topic="测试主题",
        audience="读者",
        tone="清晰",
        sections=[ContentSection(title=f"部分{i}", objective="说明") for i in range(5)],
    )
    review = ReviewReport(
        score=90,
        summary="通过。",
        structure_score=25,
        clarity_score=25,
        audience_tone_score=20,
        completeness_score=20,
    )
    source = ResearchSource(
        source_id="user-url-1",
        title="公开资料",
        url="https://example.com/article",
        summary="这是用户提供的网址正文，用于生成内容。",
        source_type="user_url",
    )
    contexts: list[str] = []
    monkeypatch.setattr(
        mvp,
        "collect_web_references",
        lambda urls: WebReferenceCollection((source,), ("https://bad.example：读取失败",)),
    )
    monkeypatch.setattr(
        mvp,
        "create_plan",
        lambda topic, *, settings, preferences=None, source_context=None: (
            contexts.append(source_context or "") or plan
        ),
    )
    monkeypatch.setattr(
        mvp,
        "create_draft",
        lambda received_plan, *, settings, source_context=None: (
            contexts.append(source_context or "") or "初稿"
        ),
    )
    monkeypatch.setattr(
        mvp,
        "review_draft",
        lambda draft, *, settings, research_context=None: (
            contexts.append(research_context or "") or review
        ),
    )
    monkeypatch.setattr(mvp, "rewrite_draft", lambda draft, review, *, settings: "修订稿")

    result = mvp.run_mvp("测试主题", settings=Settings(), reference_urls="https://example.com/article")

    assert len(contexts) == 3
    assert all("[user-url-1]" in context for context in contexts)
    assert result.research is not None
    assert result.research.sources == [source]
    assert result.reference_failures == ("https://bad.example：读取失败",)
