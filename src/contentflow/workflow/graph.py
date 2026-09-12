"""Base LangGraph workflow for Planner, Writer, Reviewer, and Rewrite."""

from dataclasses import dataclass
from typing import Literal, Protocol, cast

from langgraph.graph import END, START, StateGraph

from contentflow.config import Settings
from contentflow.input_validation import validate_topic
from contentflow.models import ContentPlan, ReviewReport
from contentflow.observability import log_event, new_run_id, record_llm_call, trace_node
from contentflow.workflow.state import ContentFlowState


class PlannerService(Protocol):
    def __call__(self, topic: str, *, settings: Settings) -> ContentPlan: ...


class WriterService(Protocol):
    def __call__(self, plan: ContentPlan, *, settings: Settings) -> str: ...


class ReviewerService(Protocol):
    def __call__(self, draft: str, *, settings: Settings) -> ReviewReport: ...


class RewriterService(Protocol):
    def __call__(self, draft: str, review: ReviewReport, *, settings: Settings) -> str: ...


@dataclass(frozen=True)
class WorkflowServices:
    """Existing business functions injected into the orchestration layer."""

    create_plan: PlannerService
    create_draft: WriterService
    review_draft: ReviewerService
    rewrite_draft: RewriterService


def build_contentflow_graph(services: WorkflowServices):
    """Build the smallest production graph with a bounded quality loop."""

    def planner_node(state: ContentFlowState) -> dict[str, object]:
        def plan() -> dict[str, object]:
            record_llm_call(state["run_id"], node="planner")
            return {
                "plan": services.create_plan(state["topic"], settings=state["settings"]),
                "status": "planned",
            }

        return trace_node(
            state["run_id"],
            "planner",
            plan,
        )

    def writer_node(state: ContentFlowState) -> dict[str, object]:
        def write() -> dict[str, object]:
            record_llm_call(state["run_id"], node="writer")
            draft = services.create_draft(state["plan"], settings=state["settings"])
            return {"draft": draft, "current_content": draft, "status": "draft_ready"}

        return trace_node(state["run_id"], "writer", write)

    def reviewer_node(state: ContentFlowState) -> dict[str, object]:
        def review() -> dict[str, object]:
            record_llm_call(state["run_id"], node="reviewer")
            result = services.review_draft(state["current_content"], settings=state["settings"])
            return {"review": result, "status": "reviewed"}

        return trace_node(state["run_id"], "reviewer", review)

    def quality_router(state: ContentFlowState) -> Literal["rewrite", "finalize"]:
        should_rewrite = (
            state["review"].score < state["quality_threshold"]
            and state["rewrite_count"] < state["max_rewrite_count"]
        )
        destination = "rewrite" if should_rewrite else "finalize"
        log_event(
            "router_decision",
            run_id=state["run_id"],
            router="quality",
            destination=destination,
            review_score=state["review"].score,
            rewrite_count=state["rewrite_count"],
        )
        return destination

    def rewrite_node(state: ContentFlowState) -> dict[str, object]:
        def rewrite() -> dict[str, object]:
            record_llm_call(state["run_id"], node="rewrite")
            rewritten_content = services.rewrite_draft(
                state["current_content"], state["review"], settings=state["settings"]
            )
            return {
                "current_content": rewritten_content,
                "rewrite_count": state["rewrite_count"] + 1,
                "status": "rewritten",
            }

        return trace_node(state["run_id"], "rewrite", rewrite)

    def finalize_node(state: ContentFlowState) -> dict[str, object]:
        def finalize() -> dict[str, object]:
            completed_at_limit = (
                state["review"].score < state["quality_threshold"]
                and state["rewrite_count"] >= state["max_rewrite_count"]
            )
            return {
                "final_content": state["current_content"],
                "status": "completed_at_rewrite_limit" if completed_at_limit else "completed",
            }

        return trace_node(state["run_id"], "finalize", finalize)

    builder = StateGraph(ContentFlowState)
    builder.add_node("planner", planner_node)
    builder.add_node("writer", writer_node)
    builder.add_node("reviewer", reviewer_node)
    builder.add_node("rewrite", rewrite_node)
    builder.add_node("finalize", finalize_node)
    builder.add_edge(START, "planner")
    builder.add_edge("planner", "writer")
    builder.add_edge("writer", "reviewer")
    builder.add_conditional_edges("reviewer", quality_router)
    builder.add_edge("rewrite", "reviewer")
    builder.add_edge("finalize", END)
    return builder.compile()


def run_contentflow_graph(
    topic: str,
    *,
    settings: Settings,
    services: WorkflowServices,
    quality_threshold: int = 80,
    max_rewrite_count: int = 1,
    run_id: str | None = None,
) -> ContentFlowState:
    """Invoke the graph with validated controls for its quality loop."""
    normalized_topic = validate_topic(topic)
    if not 0 <= quality_threshold <= 100:
        raise ValueError("quality_threshold must be between 0 and 100")
    if max_rewrite_count < 0:
        raise ValueError("max_rewrite_count must not be negative")

    active_run_id = run_id or new_run_id()
    log_event("workflow_start", run_id=active_run_id, workflow="contentflow")
    try:
        result = build_contentflow_graph(services).invoke(
            {
                "topic": normalized_topic,
                "run_id": active_run_id,
                "settings": settings,
                "quality_threshold": quality_threshold,
                "max_rewrite_count": max_rewrite_count,
                "rewrite_count": 0,
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
    return cast(ContentFlowState, result)
