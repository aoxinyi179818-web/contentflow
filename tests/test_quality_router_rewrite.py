"""Test that writing quality uses Rewrite only after evidence passes."""

from contentflow.agents.research import ResearchResult
from contentflow.config import Settings
from contentflow.models import ContentPlan, ContentSection, ReviewReport
from contentflow.tools.local_research import ResearchSource
from contentflow.workflow.research_graph import (
    ResearchWorkflowServices,
    run_researched_contentflow_graph,
)


def test_low_writing_score_rewrites_when_evidence_is_sufficient() -> None:
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
    reviews = [
        ReviewReport(
            score=70,
            summary="需改写",
            structure_score=20,
            clarity_score=20,
            audience_tone_score=20,
            completeness_score=10,
            evidence_score=20,
        ),
        ReviewReport(
            score=90,
            summary="通过",
            structure_score=25,
            clarity_score=25,
            audience_tone_score=20,
            completeness_score=20,
            evidence_score=20,
        ),
    ]

    def planner(topic: str, *, settings: Settings) -> ContentPlan:
        calls.append("planner")
        return plan

    def research(question: str, *, settings: Settings) -> ResearchResult:
        calls.append("research")
        return ResearchResult(answer="资料", sources=[source])

    def writer(plan: ContentPlan, *, research_context: str, settings: Settings) -> str:
        calls.append("writer")
        return "初稿"

    def reviewer(draft: str, *, settings: Settings) -> ReviewReport:
        calls.append(f"reviewer:{draft}")
        return reviews.pop(0)

    def rewriter(draft: str, review: ReviewReport, *, settings: Settings) -> str:
        calls.append("rewrite")
        return "修订稿"

    result = run_researched_contentflow_graph(
        "复习",
        settings=Settings(),
        services=ResearchWorkflowServices(planner, research, writer, reviewer, rewriter),
    )
    assert result["final_content"] == "修订稿"
    assert calls == ["planner", "research", "writer", "reviewer:初稿", "rewrite", "reviewer:修订稿"]
