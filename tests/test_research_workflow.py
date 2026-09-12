"""Integration tests for Planner -> Research -> Writer ordering."""

from contentflow.agents.research import ResearchResult
from contentflow.config import Settings
from contentflow.models import ContentPlan, ContentSection, ReviewReport
from contentflow.tools.local_research import ResearchSource
from contentflow.workflow.research_graph import (
    ResearchWorkflowServices,
    run_researched_contentflow_graph,
)


def test_research_runs_before_writer_and_passes_traceable_context() -> None:
    calls: list[str] = []
    plan = ContentPlan(
        topic="复习",
        audience="大学生",
        tone="清晰",
        sections=[ContentSection(title=f"部分{i}", objective="说明") for i in range(5)],
    )
    source = ResearchSource(
        source_id="study",
        title="学习计划",
        url="https://example.invalid/study",
        summary="复习任务应拆分为时间块，并记录完成情况。",
    )
    review = ReviewReport(
        score=90,
        summary="通过",
        structure_score=25,
        clarity_score=25,
        audience_tone_score=20,
        completeness_score=20,
    )

    def planner(topic: str, *, settings: Settings) -> ContentPlan:
        calls.append("planner")
        return plan

    def research(question: str, *, settings: Settings) -> ResearchResult:
        calls.append("research")
        return ResearchResult(answer="资料", sources=[source])

    def writer(plan: ContentPlan, *, research_context: str, settings: Settings) -> str:
        calls.append("writer")
        assert "[study]" in research_context
        return "初稿"

    def reviewer(draft: str, *, settings: Settings) -> ReviewReport:
        calls.append("reviewer")
        return review

    def rewriter(draft: str, review: ReviewReport, *, settings: Settings) -> str:
        calls.append("rewrite")
        return draft

    result = run_researched_contentflow_graph(
        "复习",
        settings=Settings(),
        services=ResearchWorkflowServices(planner, research, writer, reviewer, rewriter),
    )
    assert result["status"] == "completed"
    assert calls == ["planner", "research", "writer", "reviewer"]
