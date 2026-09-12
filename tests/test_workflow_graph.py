"""Tests for ContentFlow's bounded LangGraph quality loop."""

from contentflow.config import Settings
from contentflow.models import ContentPlan, ContentSection, ReviewReport
from contentflow.workflow.graph import WorkflowServices, run_contentflow_graph


def make_plan() -> ContentPlan:
    return ContentPlan(
        topic="测试主题",
        audience="大学生",
        tone="清晰",
        sections=[
            ContentSection(title=f"第{i}部分", objective="说明一个要点") for i in range(1, 6)
        ],
    )


def make_review(score: int) -> ReviewReport:
    return ReviewReport(
        score=score,
        summary="测试审阅结果",
        structure_score=20,
        clarity_score=20,
        audience_tone_score=20,
        completeness_score=score - 60,
    )


def make_services(reviews: list[ReviewReport], calls: list[str]) -> WorkflowServices:
    def create_plan(topic: str, *, settings: Settings) -> ContentPlan:
        calls.append(f"planner:{topic}")
        return make_plan()

    def create_draft(plan: ContentPlan, *, settings: Settings) -> str:
        calls.append("writer")
        return "初稿"

    def review_draft(draft: str, *, settings: Settings) -> ReviewReport:
        calls.append(f"reviewer:{draft}")
        return reviews.pop(0)

    def rewrite_draft(draft: str, review: ReviewReport, *, settings: Settings) -> str:
        calls.append(f"rewrite:{draft}")
        return "修订稿"

    return WorkflowServices(create_plan, create_draft, review_draft, rewrite_draft)


def run_with(
    reviews: list[ReviewReport], max_rewrite_count: int = 1
) -> tuple[dict[str, object], list[str]]:
    calls: list[str] = []
    result = run_contentflow_graph(
        "测试主题",
        settings=Settings(),
        services=make_services(reviews, calls),
        max_rewrite_count=max_rewrite_count,
    )
    return result, calls


def test_high_score_bypasses_rewrite() -> None:
    result, calls = run_with([make_review(80)])

    assert result["final_content"] == "初稿"
    assert result["rewrite_count"] == 0
    assert result["status"] == "completed"
    assert calls == ["planner:测试主题", "writer", "reviewer:初稿"]


def test_low_score_rewrites_then_reviews_again() -> None:
    result, calls = run_with([make_review(70), make_review(85)])

    assert result["draft"] == "初稿"
    assert result["final_content"] == "修订稿"
    assert result["review"].score == 85
    assert result["rewrite_count"] == 1
    assert result["status"] == "completed"
    assert calls == [
        "planner:测试主题",
        "writer",
        "reviewer:初稿",
        "rewrite:初稿",
        "reviewer:修订稿",
    ]


def test_low_score_stops_at_rewrite_limit() -> None:
    result, calls = run_with([make_review(70), make_review(70)])

    assert result["final_content"] == "修订稿"
    assert result["rewrite_count"] == 1
    assert result["status"] == "completed_at_rewrite_limit"
    assert calls.count("reviewer:初稿") == 1
    assert calls.count("reviewer:修订稿") == 1
    assert calls.count("rewrite:初稿") == 1
