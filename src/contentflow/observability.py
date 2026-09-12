"""Safe, correlated event logging for ContentFlow workflow debugging."""

import logging
from collections.abc import Callable, Mapping
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass
from threading import RLock
from time import perf_counter
from typing import TypeVar
from uuid import uuid4

LOGGER_NAME = "contentflow"
_SENSITIVE_FIELD_NAMES = frozenset({"api_key", "authorization", "content", "prompt", "topic"})
Result = TypeVar("Result", bound=Mapping[str, object])
_MAX_RETAINED_RUNS = 100
_ACTIVE_RUN_ID: ContextVar[str | None] = ContextVar("contentflow_run_id", default=None)
_METRICS_LOCK = RLock()


@dataclass(frozen=True)
class RunMetrics:
    """Safe runtime and cost signals for one workflow execution."""

    run_id: str
    workflow: str
    llm_call_count: int
    tool_call_count: int
    rewrite_count: int
    duration_ms: int | None
    status: str | None
    input_tokens: int | None
    output_tokens: int | None
    total_tokens: int | None
    token_usage_recorded_call_count: int


@dataclass
class _MutableRunMetrics:
    workflow: str
    started_at: float
    llm_call_count: int = 0
    tool_call_count: int = 0
    rewrite_count: int = 0
    finished_at: float | None = None
    status: str | None = None
    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0
    token_usage_recorded_call_count: int = 0


_RUN_METRICS: dict[str, _MutableRunMetrics] = {}


def configure_logging() -> None:
    """Configure concise local logs once without overriding a host application."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )


def new_run_id() -> str:
    """Return a short opaque identifier shared by one user-visible run."""
    return uuid4().hex[:12]


def current_run_id() -> str | None:
    """Return the run id active in the current workflow node, if any."""
    return _ACTIVE_RUN_ID.get()


@contextmanager
def run_context(run_id: str):
    """Make a workflow run id available to nested provider helpers."""
    token = _ACTIVE_RUN_ID.set(run_id)
    try:
        yield
    finally:
        _ACTIVE_RUN_ID.reset(token)


def get_run_metrics(run_id: str) -> RunMetrics | None:
    """Return an immutable snapshot for one run without exposing content payloads."""
    with _METRICS_LOCK:
        metrics = _RUN_METRICS.get(run_id)
        if metrics is None:
            return None
        ended_at = metrics.finished_at
        duration_ms = int(((ended_at or perf_counter()) - metrics.started_at) * 1000)
        has_usage = metrics.token_usage_recorded_call_count > 0
        return RunMetrics(
            run_id=run_id,
            workflow=metrics.workflow,
            llm_call_count=metrics.llm_call_count,
            tool_call_count=metrics.tool_call_count,
            rewrite_count=metrics.rewrite_count,
            duration_ms=duration_ms if ended_at is not None else None,
            status=metrics.status,
            input_tokens=metrics.input_tokens if has_usage else None,
            output_tokens=metrics.output_tokens if has_usage else None,
            total_tokens=metrics.total_tokens if has_usage else None,
            token_usage_recorded_call_count=metrics.token_usage_recorded_call_count,
        )


def clear_run_metrics() -> None:
    """Clear retained in-memory metrics for deterministic tests and local restarts."""
    with _METRICS_LOCK:
        _RUN_METRICS.clear()


def record_llm_call(run_id: str, *, node: str) -> None:
    """Record a model request attempt before the provider call begins."""
    log_event("llm_call", run_id=run_id, node=node)


def record_llm_usage(response: object, *, node: str) -> None:
    """Record provider usage when available, without saving model content."""
    run_id = current_run_id()
    if run_id is None:
        return
    usage = getattr(response, "usage", None)
    if usage is None:
        return
    prompt_tokens = getattr(usage, "prompt_tokens", None)
    completion_tokens = getattr(usage, "completion_tokens", None)
    total_tokens = getattr(usage, "total_tokens", None)
    if not any(isinstance(value, int) for value in (prompt_tokens, completion_tokens, total_tokens)):
        return
    log_event(
        "llm_usage",
        run_id=run_id,
        node=node,
        input_tokens=prompt_tokens if isinstance(prompt_tokens, int) else None,
        output_tokens=completion_tokens if isinstance(completion_tokens, int) else None,
        total_tokens=total_tokens if isinstance(total_tokens, int) else None,
    )


def log_event(event: str, /, **fields: object) -> None:
    """Write one safe, structured debug event without payloads or secrets."""
    _record_metric_event(event, fields)
    safe_fields = {
        key: value
        for key, value in fields.items()
        if key not in _SENSITIVE_FIELD_NAMES and value is not None
    }
    serialized_fields = " ".join(f"{key}={value}" for key, value in safe_fields.items())
    message = f"event={event}"
    if serialized_fields:
        message = f"{message} {serialized_fields}"
    logging.getLogger(LOGGER_NAME).info(message)


def _record_metric_event(event: str, fields: Mapping[str, object]) -> None:
    run_id = fields.get("run_id")
    if not isinstance(run_id, str):
        return
    with _METRICS_LOCK:
        if event == "workflow_start":
            _start_metrics(run_id, str(fields.get("workflow", "workflow")))
        elif event == "agent_start":
            _start_metrics(run_id, str(fields.get("agent", "agent")))
        metrics = _RUN_METRICS.get(run_id)
        if metrics is None:
            return
        if event == "llm_call":
            metrics.llm_call_count += 1
        elif event == "tool_call_start":
            metrics.tool_call_count += 1
        elif event == "llm_usage":
            _add_usage(metrics, fields)
        elif event == "workflow_end":
            metrics.rewrite_count = _int_field(fields, "rewrite_count", metrics.rewrite_count)
            _finish_metrics(metrics, fields.get("status"))
        elif event == "workflow_error":
            _finish_metrics(metrics, "failed")
        elif event == "agent_end" and metrics.workflow == "research":
            _finish_metrics(metrics, "completed")
        elif event == "agent_error" and metrics.workflow == "research":
            _finish_metrics(metrics, "failed")


def _start_metrics(run_id: str, workflow: str) -> None:
    if run_id in _RUN_METRICS:
        return
    if len(_RUN_METRICS) >= _MAX_RETAINED_RUNS:
        oldest_run_id = next(iter(_RUN_METRICS))
        _RUN_METRICS.pop(oldest_run_id)
    _RUN_METRICS[run_id] = _MutableRunMetrics(workflow=workflow, started_at=perf_counter())


def _add_usage(metrics: _MutableRunMetrics, fields: Mapping[str, object]) -> None:
    values = (
        _int_field(fields, "input_tokens", 0),
        _int_field(fields, "output_tokens", 0),
        _int_field(fields, "total_tokens", 0),
    )
    metrics.input_tokens += values[0]
    metrics.output_tokens += values[1]
    metrics.total_tokens += values[2]
    metrics.token_usage_recorded_call_count += 1


def _finish_metrics(metrics: _MutableRunMetrics, status: object) -> None:
    metrics.finished_at = perf_counter()
    metrics.status = str(status) if status is not None else None


def _int_field(fields: Mapping[str, object], key: str, default: int) -> int:
    value = fields.get(key)
    return value if isinstance(value, int) else default


def trace_node(run_id: str, node: str, operation: Callable[[], Result]) -> Result:
    """Log one node's start, end, and typed failure without leaking its payload."""
    log_event("node_start", run_id=run_id, node=node)
    try:
        with run_context(run_id):
            result = operation()
    except Exception as error:
        log_event("node_error", run_id=run_id, node=node, error_type=type(error).__name__)
        raise
    log_event("node_end", run_id=run_id, node=node, status=result.get("status"))
    return result
