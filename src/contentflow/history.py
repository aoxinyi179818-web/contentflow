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
    adaptations = [item.content for item in record.adaptations]
    if record.adapted_content and all(
        item.platform != record.adapted_content.platform for item in adaptations
    ):
        adaptations.append(record.adapted_content)
    return MvpResult(
        plan=record.plan,
        draft=record.draft,
        review=record.review,
        final_content=record.final_content,
        status=record.status,
        project_id=record.id,
        adaptations=tuple(adaptations),
    )
