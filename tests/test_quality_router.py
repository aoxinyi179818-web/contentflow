"""Tests for evidence-first routing in the researched workflow."""

from contentflow.agents.research import ResearchResult
from contentflow.config import Settings
from contentflow.models import ContentPlan, ContentSection, ReviewReport
from contentflow.tools.local_research import ResearchSource
from contentflow.workflow.research_graph import (
    ResearchWorkflowServices,
    run_researched_contentflow_graph,
)


def make_plan() -> ContentPlan:
    return ContentPlan(
        topic="复习",
        audience="大学生",
        tone="清晰",
        sections=[ContentSection(title=f"部分{i}", objective="说明") for i in range(5)],
    )


def make_review(evidence_score: int) -> ReviewReport:
    return ReviewReport(
        score=90,
        summary="测试审阅",
        structure_score=25,
        clarity_score=25,
        audience_tone_score=20,
        completeness_score=20,
        evidence_score=evidence_score,
    )


def test_low_evidence_researches_again_before_finalizing() -> None:
    calls: list[str] = []
    reviews = [make_review(10), make_review(20)]
    source = ResearchSource(
        source_id="study",
        title="学习计划",
        url="https://example.invalid/study",
        summary="复习任务应拆分为时间块，并记录完成情况。",
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
        return draft

    result = run_researched_contentflow_graph(
        "复习",
        settings=Settings(),
        services=ResearchWorkflowServices(planner, research, writer, reviewer, rewriter),
    )

    assert result["status"] == "completed"
    assert result["research_count"] == 2
    assert calls == ["planner", "research", "writer", "reviewer", "research", "writer", "reviewer"]
