"""LangGraph workflow that inserts Research and RAG context before writing."""

from dataclasses import dataclass
from typing import Literal, Protocol, TypedDict, cast

from langgraph.graph import END, START, StateGraph

from contentflow.agents.research import ResearchResult
from contentflow.config import Settings
from contentflow.input_validation import validate_topic
from contentflow.models import AdaptedContent, ContentPlan, ReviewReport, VisualPlan
from contentflow.observability import log_event, new_run_id, record_llm_call, trace_node
from contentflow.rag import build_retriever, format_writer_context


class ResearchWorkflowState(TypedDict):
    topic: str
    run_id: str
    settings: Settings
    quality_threshold: int
    max_rewrite_count: int
    evidence_threshold: int
    max_research_count: int
    research_count: int
    max_visual_assets: int
    rewrite_count: int
    status: str
    plan: ContentPlan
    research: ResearchResult
    research_context: str
    draft: str
    current_content: str
    review: ReviewReport
    final_content: str
    platform: str
    adapted_content: AdaptedContent
    visual_plan: VisualPlan


class PlannerService(Protocol):
    def __call__(self, topic: str, *, settings: Settings) -> ContentPlan: ...


class ResearchService(Protocol):
    def __call__(self, question: str, *, settings: Settings) -> ResearchResult: ...


class WriterService(Protocol):
    def __call__(self, plan: ContentPlan, *, research_context: str, settings: Settings) -> str: ...


class ReviewerService(Protocol):
    def __call__(self, draft: str, *, settings: Settings) -> ReviewReport: ...


class RewriterService(Protocol):
    def __call__(self, draft: str, review: ReviewReport, *, settings: Settings) -> str: ...


class AdapterService(Protocol):
    def __call__(self, content: str, *, platform: str, settings: Settings) -> AdaptedContent: ...


class VisualPlannerService(Protocol):
    def __call__(self, content: str, *, max_assets: int, settings: Settings) -> VisualPlan: ...


@dataclass(frozen=True)
class ResearchWorkflowServices:
    create_plan: PlannerService
    research: ResearchService
    create_draft: WriterService
    review_draft: ReviewerService
    rewrite_draft: RewriterService
    adapt_content: AdapterService | None = None
    visual_planner: VisualPlannerService | None = None


def build_research_question(topic: str, plan: ContentPlan) -> str:
    return (
        f"请为主题“{topic}”查找可以支持以下内容计划的资料，并明确来源。"
        f"目标受众是{plan.audience}。重点章节：{plan.sections[0].title}。"
    )


def build_research_context(result: ResearchResult, topic: str) -> str:
    if not result.sources:
        return format_writer_context([])
    evidence = build_retriever(result.sources).search(topic, top_k=3)
    return format_writer_context(evidence)


def build_researched_contentflow_graph(services: ResearchWorkflowServices):
    """Build Planner -> Research -> Writer -> Reviewer with the existing quality loop."""

    def planner_node(state: dict[str, object]) -> dict[str, object]:
        def plan() -> dict[str, object]:
            record_llm_call(str(state["run_id"]), node="planner")
            return {
                "plan": services.create_plan(
                    str(state["topic"]), settings=cast(Settings, state["settings"])
                ),
                "status": "planned",
            }

        return trace_node(
            str(state["run_id"]),
            "planner",
            plan,
        )

    def research_node(state: dict[str, object]) -> dict[str, object]:
        def research() -> dict[str, object]:
            plan = cast(ContentPlan, state["plan"])
            result = services.research(
                build_research_question(str(state["topic"]), plan),
                settings=cast(Settings, state["settings"]),
            )
            return {
                "research_count": int(state["research_count"]) + 1,
                "research": result,
                "research_context": build_research_context(result, str(state["topic"])),
                "status": "researched",
            }

        return trace_node(str(state["run_id"]), "research", research)

    def writer_node(state: dict[str, object]) -> dict[str, object]:
        def write() -> dict[str, object]:
            record_llm_call(str(state["run_id"]), node="writer")
            draft = services.create_draft(
                cast(ContentPlan, state["plan"]),
                research_context=str(state["research_context"]),
                settings=cast(Settings, state["settings"]),
            )
            return {"draft": draft, "current_content": draft, "status": "draft_ready"}

        return trace_node(str(state["run_id"]), "writer", write)

    def reviewer_node(state: dict[str, object]) -> dict[str, object]:
        def review() -> dict[str, object]:
            record_llm_call(str(state["run_id"]), node="reviewer")
            result = services.review_draft(
                str(state["current_content"]), settings=cast(Settings, state["settings"])
            )
            return {"review": result, "status": "reviewed"}

        return trace_node(str(state["run_id"]), "reviewer", review)

    def route(state: dict[str, object]) -> Literal["research", "rewrite", "finalize"]:
        review = cast(ReviewReport, state["review"])
        if review.evidence_score < int(state["evidence_threshold"]):
            if int(state["research_count"]) < int(state["max_research_count"]):
                destination = "research"
            else:
                destination = "finalize"
        elif review.score < int(state["quality_threshold"]) and int(state["rewrite_count"]) < int(
            state["max_rewrite_count"]
        ):
            destination = "rewrite"
        else:
            destination = "finalize"
        log_event(
            "router_decision",
            run_id=str(state["run_id"]),
            router="research_quality",
            destination=destination,
            evidence_score=review.evidence_score,
            review_score=review.score,
        )
        return destination

    def rewrite_node(state: dict[str, object]) -> dict[str, object]:
        def rewrite() -> dict[str, object]:
            record_llm_call(str(state["run_id"]), node="rewrite")
            content = services.rewrite_draft(
                str(state["current_content"]),
                cast(ReviewReport, state["review"]),
                settings=cast(Settings, state["settings"]),
            )
            return {
                "current_content": content,
                "rewrite_count": int(state["rewrite_count"]) + 1,
                "status": "rewritten",
            }

        return trace_node(str(state["run_id"]), "rewrite", rewrite)

    def finalize_node(state: dict[str, object]) -> dict[str, object]:
        def finalize() -> dict[str, object]:
            review = cast(ReviewReport, state["review"])
            at_research_limit = review.evidence_score < int(state["evidence_threshold"]) and int(
                state["research_count"]
            ) >= int(state["max_research_count"])
            at_rewrite_limit = (
                not at_research_limit
                and review.score < int(state["quality_threshold"])
                and int(state["rewrite_count"]) >= int(state["max_rewrite_count"])
            )
            return {
                "final_content": state["current_content"],
                "status": (
                    "completed_at_research_limit"
                    if at_research_limit
                    else "completed_at_rewrite_limit"
                    if at_rewrite_limit
                    else "completed"
                ),
            }

        return trace_node(str(state["run_id"]), "finalize", finalize)

    def adapter_node(state: dict[str, object]) -> dict[str, object]:
        def adapt() -> dict[str, object]:
            if services.adapt_content is None:
                return {"status": "adapter_skipped"}
            record_llm_call(str(state["run_id"]), node="adapter")
            adapted = services.adapt_content(
                str(state["final_content"]),
                platform=str(state["platform"]),
                settings=cast(Settings, state["settings"]),
            )
            return {"adapted_content": adapted}

        result = trace_node(str(state["run_id"]), "adapter", adapt)
        return {} if "adapted_content" not in result else result

    def visual_planner_node(state: dict[str, object]) -> dict[str, object]:
        def plan_visuals() -> dict[str, object]:
            if services.visual_planner is None:
                return {"status": "visual_planner_skipped"}
            record_llm_call(str(state["run_id"]), node="visual_planner")
            content = str(state["final_content"])
            if "adapted_content" in state:
                content = cast(AdaptedContent, state["adapted_content"]).content
            visual_plan = services.visual_planner(
                content,
                max_assets=int(state["max_visual_assets"]),
                settings=cast(Settings, state["settings"]),
            )
            return {"visual_plan": visual_plan}

        result = trace_node(str(state["run_id"]), "visual_planner", plan_visuals)
        return {} if "visual_plan" not in result else result

    builder = StateGraph(ResearchWorkflowState)
    builder.add_node("planner", planner_node)
    builder.add_node("research", research_node)
    builder.add_node("writer", writer_node)
    builder.add_node("reviewer", reviewer_node)
    builder.add_node("rewrite", rewrite_node)
    builder.add_node("finalize", finalize_node)
    builder.add_node("adapter", adapter_node)
    builder.add_node("visual_planner", visual_planner_node)
    builder.add_edge(START, "planner")
    builder.add_edge("planner", "research")
    builder.add_edge("research", "writer")
    builder.add_edge("writer", "reviewer")
    builder.add_conditional_edges("reviewer", route)
    builder.add_edge("rewrite", "reviewer")
    builder.add_edge("finalize", "adapter")
    builder.add_edge("adapter", "visual_planner")
    builder.add_edge("visual_planner", END)
    return builder.compile()


def run_researched_contentflow_graph(
    topic: str,
    *,
    settings: Settings,
    services: ResearchWorkflowServices,
    platform: str = "社交媒体文案",
    run_id: str | None = None,
) -> dict[str, object]:
    normalized_topic = validate_topic(topic)
    active_run_id = run_id or new_run_id()
    log_event("workflow_start", run_id=active_run_id, workflow="researched_contentflow")
    try:
        result = build_researched_contentflow_graph(services).invoke(
            {
                "topic": normalized_topic,
                "run_id": active_run_id,
                "settings": settings,
                "quality_threshold": 80,
                "max_rewrite_count": 1,
                "rewrite_count": 0,
                "evidence_threshold": 15,
                "max_research_count": 2,
                "research_count": 0,
                "max_visual_assets": 3,
                "platform": platform,
                "status": "started",
            }
        )
    except Exception as error:
        log_event("workflow_error", run_id=active_run_id, error_type=type(error).__name__)
        raise
    log_event(
        "workflow_end",
        run_id=active_run_id,
        status=result["status"],
        rewrite_count=result["rewrite_count"],
    )
    return cast(dict[str, object], result)
