"""Traceable TC01-TC10 acceptance cases for the current ContentFlow MVP."""

from types import SimpleNamespace

import pytest
from httpx import Request, Response
from openai import AuthenticationError, InternalServerError

from contentflow.agents import research
from contentflow.agents.research import ResearchResult
from contentflow.config import Settings
from contentflow.database.projects import ProjectRepository
from contentflow.error_handling import present_failure
from contentflow.input_validation import MAX_TOPIC_LENGTH, TopicInputError, validate_topic
from contentflow.models import ContentPlan, ContentSection, ReviewReport
from contentflow.structured import StructuredOutputError, parse_structured_output
from contentflow.tools.local_research import ResearchSource
from contentflow.workflow.graph import WorkflowServices, run_contentflow_graph
from contentflow.workflow.research_graph import (
    ResearchWorkflowServices,
    run_researched_contentflow_graph,
)


def make_plan(topic: str = "考试复习计划") -> ContentPlan:
    return ContentPlan(
        topic=topic,
        audience="大学生",
        tone="清晰",
        sections=[
            ContentSection(title=f"第{i}部分", objective="说明一个可执行要点") for i in range(1, 6)
        ],
    )


def make_review(score: int, *, evidence_score: int = 25) -> ReviewReport:
    remaining_score = score
    dimensions: list[int] = []
    for _ in range(4):
        dimension_score = min(25, remaining_score)
        dimensions.append(dimension_score)
        remaining_score -= dimension_score
    return ReviewReport(
        score=score,
        summary="测试评审结果",
        structure_score=dimensions[0],
        clarity_score=dimensions[1],
        audience_tone_score=dimensions[2],
        completeness_score=dimensions[3],
        evidence_score=evidence_score,
    )


def make_services(reviews: list[ReviewReport], calls: list[str]) -> WorkflowServices:
    def planner(topic: str, *, settings: Settings) -> ContentPlan:
        calls.append("planner")
        return make_plan(topic)

    def writer(plan: ContentPlan, *, settings: Settings) -> str:
        calls.append("writer")
        return "初稿内容"

    def reviewer(draft: str, *, settings: Settings) -> ReviewReport:
        calls.append("reviewer")
        return reviews.pop(0)

    def rewriter(draft: str, review: ReviewReport, *, settings: Settings) -> str:
        calls.append("rewrite")
        return "修订稿内容"

    return WorkflowServices(planner, writer, reviewer, rewriter)


def run_basic_workflow(
    reviews: list[ReviewReport], *, max_rewrite_count: int = 1
) -> tuple[dict, list[str]]:
    calls: list[str] = []
    result = run_contentflow_graph(
        "考试复习计划",
        settings=Settings(),
        services=make_services(reviews, calls),
        max_rewrite_count=max_rewrite_count,
    )
    return result, calls


def test_tc01_valid_topic_completes_core_workflow() -> None:
    """AC-IN-01 / AC-PL-01 / AC-FN-01: a valid topic reaches Final."""
    result, calls = run_basic_workflow([make_review(90)])

    assert result["status"] == "completed"
    assert result["final_content"] == "初稿内容"
    assert calls == ["planner", "writer", "reviewer"]


def test_tc02_empty_topic_is_rejected_before_workflow() -> None:
    """AC-IN-02: blank input does not enter Planner."""
    with pytest.raises(TopicInputError, match="empty"):
        validate_topic(" \n ")


def test_tc03_overlong_topic_is_rejected_with_a_known_limit() -> None:
    """AC-IN-04: input beyond 500 characters is rejected safely."""
    with pytest.raises(TopicInputError, match="exceed"):
        validate_topic("a" * (MAX_TOPIC_LENGTH + 1))


def test_tc04_llm_failures_have_safe_recovery_messages() -> None:
    """AC-PL-06 / AC-ST-04: Timeout, 401 and 500 remain actionable and safe."""
    request = Request("POST", "https://api.example.invalid/chat")
    unauthorized = AuthenticationError(
        "invalid key", response=Response(401, request=request), body=None
    )
    service_error = InternalServerError(
        "provider failed", response=Response(500, request=request), body=None
    )

    assert present_failure(TimeoutError()).code == "llm_timeout"
    assert present_failure(unauthorized).code == "api_configuration"
    assert present_failure(service_error).code == "service_unavailable"


def test_tc05_invalid_json_is_rejected_by_the_structured_contract() -> None:
    """AC-PL-06: an incomplete model response cannot become a plan."""
    with pytest.raises(StructuredOutputError, match="Invalid ContentPlan JSON"):
        parse_structured_output('{"topic":"只有主题"}', ContentPlan)


def test_tc06_low_review_score_routes_through_rewrite() -> None:
    """AC-RW-01: a score below the quality threshold triggers one rewrite."""
    result, calls = run_basic_workflow([make_review(70), make_review(85)])

    assert result["status"] == "completed"
    assert result["final_content"] == "修订稿内容"
    assert calls == ["planner", "writer", "reviewer", "rewrite", "reviewer"]


def test_tc07_low_evidence_routes_back_to_research() -> None:
    """AC-RS-03 / AC-ST-02: insufficient evidence causes a bounded research retry."""
    calls: list[str] = []
    reviews = [make_review(90, evidence_score=10), make_review(90, evidence_score=25)]
    source = ResearchSource(
        source_id="study",
        title="学习计划资料",
        url="https://example.invalid/study",
        summary="将复习任务拆分为时间块，并记录完成情况。",
    )

    def planner(topic: str, *, settings: Settings) -> ContentPlan:
        calls.append("planner")
        return make_plan(topic)

    def search(question: str, *, settings: Settings) -> ResearchResult:
        calls.append("research")
        return ResearchResult(answer="资料结论", sources=[source])

    def writer(plan: ContentPlan, *, research_context: str, settings: Settings) -> str:
        calls.append("writer")
        assert "[study]" in research_context
        return "研究后的初稿"

    def reviewer(draft: str, *, settings: Settings) -> ReviewReport:
        calls.append("reviewer")
        return reviews.pop(0)

    def rewriter(draft: str, review: ReviewReport, *, settings: Settings) -> str:
        calls.append("rewrite")
        return draft

    result = run_researched_contentflow_graph(
        "考试复习计划",
        settings=Settings(),
        services=ResearchWorkflowServices(planner, search, writer, reviewer, rewriter),
    )

    assert result["status"] == "completed"
    assert result["research_count"] == 2
    assert calls == ["planner", "research", "writer", "reviewer", "research", "writer", "reviewer"]


def test_tc08_search_timeout_stops_the_tool_call_safely(monkeypatch: pytest.MonkeyPatch) -> None:
    """AC-RS-03: a failing search becomes a domain-level timeout."""
    call = SimpleNamespace(
        id="call_1",
        function=SimpleNamespace(
            name="search_research_knowledge",
            arguments='{"query":"学习计划"}',
        ),
    )

    def slow_search(arguments: object) -> None:
        raise TimeoutError("simulated search timeout")

    monkeypatch.setattr(research, "search_research_knowledge", slow_search)

    with pytest.raises(research.SearchTimeoutError, match="time budget"):
        research._execute_tool_call(call)


def test_tc09_rewrite_stops_at_the_configured_limit() -> None:
    """AC-ST-07: repeated low scores cannot create an infinite rewrite loop."""
    result, calls = run_basic_workflow([make_review(70), make_review(70)], max_rewrite_count=1)

    assert result["status"] == "completed_at_rewrite_limit"
    assert result["rewrite_count"] == 1
    assert calls.count("rewrite") == 1


def test_tc10_completed_project_round_trips_through_sqlite(tmp_path) -> None:
    """AC-HI-01: a completed artifact remains available after local persistence."""
    repository = ProjectRepository(f"sqlite:///{(tmp_path / 'contentflow.db').as_posix()}")
    saved = repository.save_project(
        topic="考试复习计划",
        plan=make_plan(),
        draft="初稿内容",
        review=make_review(90),
        final_content="最终内容",
        status="completed",
    )

    loaded = repository.get_project(saved.id)

    assert loaded == saved
    assert loaded is not None
    assert loaded.final_content == "最终内容"
