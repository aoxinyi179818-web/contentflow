"""Integration test for the Adapter node after Research Workflow finalization."""

from contentflow.agents.research import ResearchResult
from contentflow.config import Settings
from contentflow.models import AdaptedContent, ContentPlan, ContentSection, ReviewReport
from contentflow.tools.local_research import ResearchSource
from contentflow.workflow.research_graph import (
    ResearchWorkflowServices,
    run_researched_contentflow_graph,
)


def test_adapter_runs_after_a_passed_review() -> None:
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
        summary="复习任务应拆分为时间块。",
    )
    review = ReviewReport(
        score=90,
        summary="通过",
        structure_score=25,
        clarity_score=25,
        audience_tone_score=20,
        completeness_score=20,
        evidence_score=20,
    )

    def planner(topic: str, *, settings: Settings) -> ContentPlan:
        calls.append("planner")
        return plan

    def research(question: str, *, settings: Settings) -> ResearchResult:
        calls.append("research")
        return ResearchResult(answer="资料", sources=[source])

    def writer(plan: ContentPlan, *, research_context: str, settings: Settings) -> str:
        calls.append("writer")
        return "最终内容"

    def reviewer(draft: str, *, settings: Settings) -> ReviewReport:
        calls.append("reviewer")
        return review

    def rewriter(draft: str, review: ReviewReport, *, settings: Settings) -> str:
        calls.append("rewrite")
        return draft

    def adapter(content: str, *, platform: str, settings: Settings) -> AdaptedContent:
        calls.append(f"adapter:{platform}")
        assert content == "最终内容"
        return AdaptedContent(
            platform="PPT 大纲",
            title="复习计划 PPT",
            content="第 1 页：目标",
            format_notes=["每页一个主题"],
        )

    result = run_researched_contentflow_graph(
        "复习",
        settings=Settings(),
        services=ResearchWorkflowServices(planner, research, writer, reviewer, rewriter, adapter),
        platform="PPT 大纲",
    )

    assert result["final_content"] == "最终内容"
    assert result["adapted_content"].platform == "PPT 大纲"
    assert calls == ["planner", "research", "writer", "reviewer", "adapter:PPT 大纲"]
