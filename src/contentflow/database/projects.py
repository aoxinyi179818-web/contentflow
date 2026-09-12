"""Repository for durable ContentFlow project records."""

import sqlite3
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from contentflow.agents.research import ResearchResult
from contentflow.models import AdaptedContent, ContentPlan, ReviewReport, VisualPlan
from contentflow.observability import log_event, new_run_id

SQLITE_URL_PREFIX = "sqlite:///"


class DatabaseUrlError(ValueError):
    """Raised when the project storage URL is not a local SQLite URL."""


@dataclass(frozen=True)
class ProjectRecord:
    """Complete, typed project artifact loaded from SQLite."""

    id: str
    topic: str
    plan: ContentPlan
    research: ResearchResult | None
    draft: str
    review: ReviewReport
    final_content: str
    adapted_content: AdaptedContent | None
    visual_plan: VisualPlan | None
    status: str
    created_at: datetime


@dataclass(frozen=True)
class ProjectSummary:
    """Lightweight record for a future history-list interface."""

    id: str
    topic: str
    status: str
    created_at: datetime


def database_path_from_url(database_url: str) -> Path:
    """Return a local file path and reject non-SQLite backends for this MVP."""
    if not database_url.startswith(SQLITE_URL_PREFIX):
        raise DatabaseUrlError("DATABASE_URL must use the sqlite:/// prefix.")
    raw_path = database_url.removeprefix(SQLITE_URL_PREFIX)
    if not raw_path or raw_path == ":memory:":
        raise DatabaseUrlError("DATABASE_URL must point to a SQLite file.")
    return Path(raw_path)


class ProjectRepository:
    """Keep SQLite access separate from the AI workflow and UI layers."""

    def __init__(self, database_url: str) -> None:
        self._path = database_path_from_url(database_url)
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self.initialize()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self._path)
        connection.row_factory = sqlite3.Row
        return connection

    def initialize(self) -> None:
        """Create the single-project table and its history lookup index."""
        with self._connect() as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS projects (
                    id TEXT PRIMARY KEY,
                    topic TEXT NOT NULL,
                    plan_json TEXT NOT NULL,
                    research_json TEXT,
                    draft TEXT NOT NULL,
                    review_json TEXT NOT NULL,
                    final_content TEXT NOT NULL,
                    adapted_content_json TEXT,
                    visual_plan_json TEXT,
                    status TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS idx_projects_created_at
                    ON projects(created_at DESC);
                """
            )

    def save_project(
        self,
        *,
        topic: str,
        plan: ContentPlan,
        draft: str,
        review: ReviewReport,
        final_content: str,
        status: str,
        research: ResearchResult | None = None,
        adapted_content: AdaptedContent | None = None,
        visual_plan: VisualPlan | None = None,
        run_id: str | None = None,
    ) -> ProjectRecord:
        """Persist one completed project and return its typed record."""
        active_run_id = run_id or new_run_id()
        log_event("database_save_start", run_id=active_run_id, topic_length=len(topic.strip()))
        try:
            normalized_topic = topic.strip()
            normalized_draft = draft.strip()
            normalized_final = final_content.strip()
            normalized_status = status.strip()
            if not normalized_topic:
                raise ValueError("topic must not be empty")
            if not normalized_draft or not normalized_final:
                raise ValueError("draft and final_content must not be empty")
            if not normalized_status:
                raise ValueError("status must not be empty")
            record = ProjectRecord(
                id=str(uuid4()),
                topic=normalized_topic,
                plan=plan,
                research=research,
                draft=normalized_draft,
                review=review,
                final_content=normalized_final,
                adapted_content=adapted_content,
                visual_plan=visual_plan,
                status=normalized_status,
                created_at=datetime.now(UTC),
            )
            with self._connect() as connection:
                connection.execute(
                    """
                    INSERT INTO projects (
                        id, topic, plan_json, research_json, draft, review_json,
                        final_content, adapted_content_json, visual_plan_json, status, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        record.id,
                        record.topic,
                        record.plan.model_dump_json(),
                        record.research.model_dump_json() if record.research else None,
                        record.draft,
                        record.review.model_dump_json(),
                        record.final_content,
                        record.adapted_content.model_dump_json()
                        if record.adapted_content
                        else None,
                        record.visual_plan.model_dump_json() if record.visual_plan else None,
                        record.status,
                        record.created_at.isoformat(),
                    ),
                )
        except Exception as error:
            log_event("database_save_error", run_id=active_run_id, error_type=type(error).__name__)
            raise
        log_event("database_save_end", run_id=active_run_id, project_id=record.id)
        return record

    def get_project(self, project_id: str) -> ProjectRecord | None:
        """Load one project by opaque identifier, or None when it does not exist."""
        with self._connect() as connection:
            row = connection.execute(
                "SELECT * FROM projects WHERE id = ?", (project_id,)
            ).fetchone()
        return self._to_record(row) if row else None

    def list_recent_projects(self, *, limit: int = 20) -> list[ProjectSummary]:
        """Return newest project metadata without loading every large content artifact."""
        if not 1 <= limit <= 100:
            raise ValueError("limit must be between 1 and 100")
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT id, topic, status, created_at
                FROM projects
                ORDER BY created_at DESC, id DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
        return [
            ProjectSummary(
                id=row["id"],
                topic=row["topic"],
                status=row["status"],
                created_at=datetime.fromisoformat(row["created_at"]),
            )
            for row in rows
        ]

    @staticmethod
    def _to_record(row: sqlite3.Row) -> ProjectRecord:
        return ProjectRecord(
            id=row["id"],
            topic=row["topic"],
            plan=ContentPlan.model_validate_json(row["plan_json"]),
            research=ResearchResult.model_validate_json(row["research_json"])
            if row["research_json"]
            else None,
            draft=row["draft"],
            review=ReviewReport.model_validate_json(row["review_json"]),
            final_content=row["final_content"],
            adapted_content=AdaptedContent.model_validate_json(row["adapted_content_json"])
            if row["adapted_content_json"]
            else None,
            visual_plan=VisualPlan.model_validate_json(row["visual_plan_json"])
            if row["visual_plan_json"]
            else None,
            status=row["status"],
            created_at=datetime.fromisoformat(row["created_at"]),
        )
