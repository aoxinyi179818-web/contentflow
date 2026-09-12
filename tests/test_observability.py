"""Regression tests for safe, correlated workflow debug events."""

import logging
from dataclasses import dataclass
from types import SimpleNamespace

import pytest

from contentflow import mvp
from contentflow.agents import research as research_module
from contentflow.config import Settings
from contentflow.database import ProjectRepository
from contentflow.models import ContentPlan, ContentSection, ReviewReport
from contentflow.observability import LOGGER_NAME
from contentflow.workflow.graph import WorkflowServices, run_contentflow_graph


def make_plan() -> ContentPlan:
    return ContentPlan(
        topic="机密主题",
        audience="大学生",
        tone="清晰",
        sections=[ContentSection(title=f"第{i}部分", objective="说明要点") for i in range(1, 6)],
    )


def make_review() -> ReviewReport:
    return ReviewReport(
        score=85,
        summary="可发布",
        structure_score=25,
        clarity_score=25,
        audience_tone_score=20,
        completeness_score=15,
    )


def make_services() -> WorkflowServices:
    return WorkflowServices(
        create_plan=lambda topic, *, settings: make_plan(),
        create_draft=lambda plan, *, settings: "初稿",
        review_draft=lambda draft, *, settings: make_review(),
        rewrite_draft=lambda draft, review, *, settings: "修订稿",
    )


def event_messages(caplog) -> list[str]:
    return [record.getMessage() for record in caplog.records if record.name == LOGGER_NAME]


def test_graph_logs_a_safe_correlated_node_and_router_chain(caplog) -> None:
    caplog.set_level(logging.INFO, logger=LOGGER_NAME)

    result = run_contentflow_graph(
        "机密主题",
        settings=Settings(),
        services=make_services(),
        run_id="trace-graph-01",
    )

    messages = event_messages(caplog)
    assert result["status"] == "completed"
    assert any("event=workflow_start run_id=trace-graph-01" in message for message in messages)
    assert any("event=node_start run_id=trace-graph-01 node=planner" in message for message in messages)
    assert any("event=node_end run_id=trace-graph-01 node=finalize" in message for message in messages)
    assert any("event=router_decision run_id=trace-graph-01" in message for message in messages)
    assert any("event=workflow_end run_id=trace-graph-01 status=completed" in message for message in messages)
    assert all("机密主题" not in message for message in messages)


def test_failed_node_logs_node_and_workflow_errors(caplog) -> None:
    caplog.set_level(logging.INFO, logger=LOGGER_NAME)

    def fail_planner(topic: str, *, settings: Settings) -> ContentPlan:
        raise RuntimeError("provider unavailable")

    services = WorkflowServices(
        create_plan=fail_planner,
        create_draft=lambda plan, *, settings: "不会执行",
        review_draft=lambda draft, *, settings: make_review(),
        rewrite_draft=lambda draft, review, *, settings: "不会执行",
    )

    with pytest.raises(RuntimeError, match="provider unavailable"):
        run_contentflow_graph(
            "机密主题",
            settings=Settings(),
            services=services,
            run_id="trace-error-01",
        )

    messages = event_messages(caplog)
    assert any(
        "event=node_error run_id=trace-error-01 node=planner error_type=RuntimeError" in message
        for message in messages
    )
    assert any(
        "event=workflow_error run_id=trace-error-01 error_type=RuntimeError" in message
        for message in messages
    )


def test_mvp_passes_one_run_id_to_graph_and_storage(monkeypatch) -> None:
    captured: dict[str, object] = {}
    plan = make_plan()
    review = make_review()

    def fake_graph(topic: str, *, settings: Settings, services: WorkflowServices, run_id: str):
        captured["graph_run_id"] = run_id
        return {
            "plan": plan,
            "draft": "初稿",
            "review": review,
            "final_content": "终稿",
            "status": "completed",
        }

    @dataclass
    class RecordingRepository:
        saved: dict[str, object] | None = None

        def save_project(self, **kwargs: object) -> None:
            self.saved = kwargs

    monkeypatch.setattr(mvp, "run_contentflow_graph", fake_graph)
    repository = RecordingRepository()

    result = mvp.run_mvp("机密主题", settings=Settings(), repository=repository, run_id="trace-mvp-01")

    assert result.status == "completed"
    assert captured["graph_run_id"] == "trace-mvp-01"
    assert repository.saved is not None
    assert repository.saved["run_id"] == "trace-mvp-01"


def test_tool_and_database_events_keep_the_same_safe_run_id(caplog, monkeypatch, tmp_path) -> None:
    caplog.set_level(logging.INFO, logger=LOGGER_NAME)
    source = research_module.ResearchSource(
        source_id="source-1",
        title="测试来源",
        url="https://example.invalid/source-1",
        summary="演示摘要",
    )
    tool_call = SimpleNamespace(
        id="call-1",
        function=SimpleNamespace(name="search_research_knowledge", arguments='{"query":"机密主题"}'),
    )
    monkeypatch.setattr(research_module, "search_research_knowledge", lambda arguments: [source])

    research_module._execute_tool_call(tool_call, run_id="trace-storage-01")
    repository = ProjectRepository(f"sqlite:///{(tmp_path / 'projects.db').as_posix()}")
    repository.save_project(
        topic="机密主题",
        plan=make_plan(),
        draft="初稿",
        review=make_review(),
        final_content="终稿",
        status="completed",
        run_id="trace-storage-01",
    )

    messages = event_messages(caplog)
    assert any("event=tool_call_start run_id=trace-storage-01" in message for message in messages)
    assert any(
        "event=tool_call_end run_id=trace-storage-01" in message and "source_count=1" in message
        for message in messages
    )
    assert any("event=database_save_start run_id=trace-storage-01" in message for message in messages)
    assert any("event=database_save_end run_id=trace-storage-01" in message for message in messages)
    assert all("机密主题" not in message for message in messages)
