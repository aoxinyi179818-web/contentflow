import pytest

from contentflow.agents.research import ResearchResult
from contentflow.config import Settings
from contentflow.models import ContentPlan, ContentSection, ReviewReport
from contentflow.tools.local_research import ResearchSource
from contentflow.workflow.research_graph import (
    ResearchWorkflowPolicy,
    ResearchWorkflowServices,
    run_researched_contentflow_graph,
)


def make_plan() -> ContentPlan:
    return ContentPlan(
        topic="复习",
        audience="大学生",
        tone="清晰",
        sections=[ContentSection(title=f"部分{index}", objective="说明") for index in range(5)],
    )


def make_review(score: int, evidence_score: int) -> ReviewReport:
    dimensions = (20, 20, 15, 15) if score == 70 else (25, 25, 20, 20)
    return ReviewReport(
        score=score,
        summary="测试审阅",
        structure_score=dimensions[0],
        clarity_score=dimensions[1],
        audience_tone_score=dimensions[2],
        completeness_score=dimensions[3],
        evidence_score=evidence_score,
    )


def make_services(reviews: list[ReviewReport], calls: list[str], *, visual_budget: list[int] | None = None) -> ResearchWorkflowServices:
    source = ResearchSource(
        source_id="study",
        title="学习计划",
        url="https://example.invalid/study",
        summary="复习任务应拆分为时间块。",
    )

    def planner(topic: str, *, settings: Settings) -> ContentPlan:
        calls.append("planner")
        return make_plan()

    def research(question: str, *, settings: Settings) -> ResearchResult:
        calls.append("research")
        return ResearchResult(answer="资料", sources=[source])

    def writer(plan: ContentPlan, *, research_context: str, settings: Settings) -> str:
        calls.append("writer")
        return "初稿"

    def reviewer(draft: str, *, settings: Settings) -> ReviewReport:
        calls.append("reviewer")
        return reviews.pop(0)

    def rewriter(draft: str, review: ReviewReport, *, settings: Settings) -> str:
        calls.append("rewrite")
        return "修订稿"

    def visual_planner(content: str, *, max_assets: int, settings: Settings):
        if visual_budget is not None:
            visual_budget.append(max_assets)
        calls.append("visual")
        from contentflow.models import VisualPlan

        return VisualPlan(overview="无需素材", assets=[])

    return ResearchWorkflowServices(
        planner,
        research,
        writer,
        reviewer,
        rewriter,
        visual_planner=visual_planner if visual_budget is not None else None,
    )


@pytest.mark.parametrize(
    ("kwargs", "message"),
    [
        ({"quality_threshold": 101}, "quality_threshold"),
        ({"evidence_threshold": -1}, "evidence_threshold"),
        ({"max_rewrite_count": -1}, "max_rewrite_count"),
        ({"max_research_count": -1}, "max_research_count"),
        ({"max_visual_assets": 6}, "max_visual_assets"),
    ],
)
def test_policy_rejects_invalid_product_boundaries(kwargs: dict[str, int], message: str) -> None:
    with pytest.raises(ValueError, match=message):
        ResearchWorkflowPolicy(**kwargs)


def test_custom_quality_policy_allows_the_configured_rewrite_budget() -> None:
    calls: list[str] = []
    result = run_researched_contentflow_graph(
        "复习",
        settings=Settings(),
        services=make_services(
            [make_review(70, 20), make_review(70, 20), make_review(90, 20)], calls
        ),
        policy=ResearchWorkflowPolicy(max_rewrite_count=2),
    )

    assert result["rewrite_count"] == 2
    assert calls.count("rewrite") == 2
    assert result["status"] == "completed"


def test_custom_evidence_policy_stops_at_the_configured_research_budget() -> None:
    calls: list[str] = []
    result = run_researched_contentflow_graph(
        "复习",
        settings=Settings(),
        services=make_services([make_review(90, 10)], calls),
        policy=ResearchWorkflowPolicy(max_research_count=1),
    )

    assert result["status"] == "completed_at_research_limit"
    assert result["research_count"] == 1
    assert calls == ["planner", "research", "writer", "reviewer"]


def test_custom_visual_budget_reaches_the_visual_planner() -> None:
    calls: list[str] = []
    visual_budget: list[int] = []
    run_researched_contentflow_graph(
        "复习",
        settings=Settings(),
        services=make_services([make_review(90, 20)], calls, visual_budget=visual_budget),
        policy=ResearchWorkflowPolicy(max_visual_assets=2),
    )

    assert visual_budget == [2]
