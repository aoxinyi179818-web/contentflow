"""View-model helpers for browsing durable local projects."""

from contentflow.database import ProjectRecord, ProjectSummary
from contentflow.mvp import MvpResult


def format_project_label(summary: ProjectSummary) -> str:
    """Return a concise, local-time label for a selectable project summary."""
    timestamp = summary.created_at.astimezone().strftime("%Y-%m-%d %H:%M")
    status = "已完成" if summary.status == "completed" else summary.status
    return f"{timestamp} · {status} · {summary.topic}"


def result_from_project_record(record: ProjectRecord) -> MvpResult:
    """Adapt a persisted record to the existing result viewer contract."""
    return MvpResult(
        plan=record.plan,
        draft=record.draft,
        review=record.review,
        final_content=record.final_content,
        status=record.status,
    )
