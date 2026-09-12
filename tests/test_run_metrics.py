"""Tests for safe per-run performance and cost metrics."""

from types import SimpleNamespace

from contentflow.config import Settings
from contentflow.models import ContentPlan, ContentSection, ReviewReport
from contentflow.observability import (
    clear_run_metrics,
    get_run_metrics,
    log_event,
    record_llm_call,
    record_llm_usage,
    run_context,
)
from contentflow.workflow.graph import WorkflowServices, run_contentflow_graph


def make_plan() -> ContentPlan:
    return ContentPlan(
        topic="性能测试主题",
        audience="大学生",
        tone="清晰",
        sections=[ContentSection(title=f"第{i}部分", objective="说明") for i in range(1, 6)],
    )


def make_review(score: int) -> ReviewReport:
    return ReviewReport(
        score=score,
        summary="测试通过",
        structure_score=25,
        clarity_score=25,
        audience_tone_score=20,
        completeness_score=score - 70,
    )


def test_workflow_metrics_count_model_calls_rewrites_and_duration() -> None:
    clear_run_metrics()
    reviews = [make_review(75), make_review(85)]
    services = WorkflowServices(
        create_plan=lambda topic, *, settings: make_plan(),
        create_draft=lambda plan, *, settings: "初稿",
        review_draft=lambda draft, *, settings: reviews.pop(0),
        rewrite_draft=lambda draft, review, *, settings: "修订稿",
    )

    run_contentflow_graph(
        "性能测试主题",
        settings=Settings(),
        services=services,
        run_id="metrics-workflow-01",
    )

    metrics = get_run_metrics("metrics-workflow-01")

    assert metrics is not None
    assert metrics.llm_call_count == 5
    assert metrics.tool_call_count == 0
    assert metrics.rewrite_count == 1
    assert metrics.duration_ms is not None
    assert metrics.duration_ms >= 0
    assert metrics.status == "completed"
    assert metrics.total_tokens is None


def test_metrics_accumulate_provider_usage_when_response_exposes_it() -> None:
    clear_run_metrics()
    run_id = "metrics-usage-01"
    response = SimpleNamespace(
        usage=SimpleNamespace(prompt_tokens=120, completion_tokens=45, total_tokens=165)
    )

    log_event("workflow_start", run_id=run_id, workflow="contentflow")
    record_llm_call(run_id, node="planner")
    with run_context(run_id):
        record_llm_usage(response, node="planner")
    log_event("tool_call_start", run_id=run_id, tool="search_research_knowledge")
    log_event("workflow_end", run_id=run_id, status="completed", rewrite_count=0)

    metrics = get_run_metrics(run_id)

    assert metrics is not None
    assert metrics.llm_call_count == 1
    assert metrics.tool_call_count == 1
    assert metrics.input_tokens == 120
    assert metrics.output_tokens == 45
    assert metrics.total_tokens == 165
    assert metrics.token_usage_recorded_call_count == 1
