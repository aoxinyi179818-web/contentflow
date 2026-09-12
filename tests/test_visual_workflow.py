"""Integration test for visual planning after final content is ready."""

from contentflow.agents.research import ResearchResult
from contentflow.config import Settings
from contentflow.models import (
    ContentPlan,
    ContentSection,
    ReviewReport,
    VisualAssetPlan,
    VisualPlan,
)
from contentflow.tools.local_research import ResearchSource
from contentflow.workflow.research_graph import (
    ResearchWorkflowServices,
    run_researched_contentflow_graph,
)


def test_visual_planner_runs_after_final_content() -> None:
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
        return "最终内容：每天安排两个专注时段。"

    def reviewer(draft: str, *, settings: Settings) -> ReviewReport:
        calls.append("reviewer")
        return review

    def rewriter(draft: str, review: ReviewReport, *, settings: Settings) -> str:
        calls.append("rewrite")
        return draft

    def visual_planner(content: str, *, max_assets: int, settings: Settings) -> VisualPlan:
        calls.append(f"visual:{max_assets}")
        assert content == "最终内容：每天安排两个专注时段。"
        return VisualPlan(
            overview="使用一张学习时间块插画。",
            assets=[
                VisualAssetPlan(
                    section_anchor="每天安排两个专注时段",
                    purpose="解释时间块安排。",
                    asset_type="image",
                    tool="image_generation",
                    query_or_prompt="学习时间块插画",
                    rationale="抽象概念适合插画。",
                )
            ],
        )

    result = run_researched_contentflow_graph(
        "复习",
        settings=Settings(),
        services=ResearchWorkflowServices(
            planner, research, writer, reviewer, rewriter, visual_planner=visual_planner
        ),
    )

    assert result["visual_plan"].assets[0].tool == "image_generation"
    assert calls == ["planner", "research", "writer", "reviewer", "visual:3"]
