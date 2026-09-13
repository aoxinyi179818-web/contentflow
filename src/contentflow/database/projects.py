"""Repository for durable ContentFlow project records."""

import sqlite3
from dataclasses import dataclass, replace
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from contentflow.agents.research import ResearchResult
from contentflow.models import (
    AdaptedContent,
    ContentPlan,
    FeedbackRating,
    ProjectFeedbackInput,
    ReviewReport,
    VisualPlan,
)
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
    adaptations: tuple["ProjectAdaptation", ...] = ()


@dataclass(frozen=True)
class ProjectSummary:
    """Lightweight record for a future history-list interface."""

    id: str
    topic: str
    status: str
    created_at: datetime


@dataclass(frozen=True)
class ProjectFeedback:
    """The latest user feedback stored for one project."""

    project_id: str
    rating: FeedbackRating
    comment: str
    updated_at: datetime


@dataclass(frozen=True)
class ProjectAdaptation:
    """One saved platform-specific version of a project's final content."""

    project_id: str
    content: AdaptedContent
    updated_at: datetime


@dataclass(frozen=True)
class FeedbackProjectItem:
    """A feedback item joined with the review score needed for local evaluation."""

    project_id: str
    topic: str
    rating: FeedbackRating
    comment: str
    review_score: int
    updated_at: datetime


@dataclass(frozen=True)
class FeedbackOverview:
    """Small, local quality summary based on latest feedback per project."""

    total_count: int
    helpful_count: int
    improvement_count: int
    helpful_rate: int | None
    average_review_score: int | None
    recent_items: tuple[FeedbackProjectItem, ...]


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
                CREATE TABLE IF NOT EXISTS project_feedback (
                    project_id TEXT PRIMARY KEY,
                    rating TEXT NOT NULL CHECK (rating IN ('有帮助', '需要改进')),
                    comment TEXT NOT NULL DEFAULT '',
                    updated_at TEXT NOT NULL,
                    FOREIGN KEY (project_id) REFERENCES projects(id)
                );
                CREATE INDEX IF NOT EXISTS idx_project_feedback_updated_at
                    ON project_feedback(updated_at DESC);
                CREATE TABLE IF NOT EXISTS project_adaptations (
                    project_id TEXT NOT NULL,
                    platform TEXT NOT NULL,
                    adapted_content_json TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    PRIMARY KEY (project_id, platform),
                    FOREIGN KEY (project_id) REFERENCES projects(id)
                );
                CREATE INDEX IF NOT EXISTS idx_project_adaptations_updated_at
                    ON project_adaptations(updated_at DESC);
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
        if not row:
            return None
        record = self._to_record(row)
        return replace(record, adaptations=tuple(self.list_adaptations(record.id)))

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

    def save_feedback(self, project_id: str, *, rating: str, comment: str = "") -> ProjectFeedback:
        """Insert or update one project's latest user quality judgment."""
        normalized_project_id = project_id.strip()
        if not normalized_project_id:
            raise ValueError("project_id must not be empty")
        feedback = ProjectFeedbackInput(rating=rating, comment=comment)
        updated_at = datetime.now(UTC)
        with self._connect() as connection:
            exists = connection.execute(
                "SELECT 1 FROM projects WHERE id = ?", (normalized_project_id,)
            ).fetchone()
            if not exists:
                raise ValueError("project does not exist")
            connection.execute(
                """
                INSERT INTO project_feedback (project_id, rating, comment, updated_at)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(project_id) DO UPDATE SET
                    rating = excluded.rating,
                    comment = excluded.comment,
                    updated_at = excluded.updated_at
                """,
                (normalized_project_id, feedback.rating, feedback.comment, updated_at.isoformat()),
            )
        return ProjectFeedback(
            project_id=normalized_project_id,
            rating=feedback.rating,
            comment=feedback.comment,
            updated_at=updated_at,
        )

    def save_adaptation(
        self, project_id: str, adapted_content: AdaptedContent
    ) -> ProjectAdaptation:
        """Save one platform version without overwriting a different platform's version."""
        normalized_project_id = project_id.strip()
        if not normalized_project_id:
            raise ValueError("project_id must not be empty")
        updated_at = datetime.now(UTC)
        with self._connect() as connection:
            exists = connection.execute(
                "SELECT 1 FROM projects WHERE id = ?", (normalized_project_id,)
            ).fetchone()
            if not exists:
                raise ValueError("project does not exist")
            connection.execute(
                """
                INSERT INTO project_adaptations (
                    project_id, platform, adapted_content_json, updated_at
                ) VALUES (?, ?, ?, ?)
                ON CONFLICT(project_id, platform) DO UPDATE SET
                    adapted_content_json = excluded.adapted_content_json,
                    updated_at = excluded.updated_at
                """,
                (
                    normalized_project_id,
                    adapted_content.platform,
                    adapted_content.model_dump_json(),
                    updated_at.isoformat(),
                ),
            )
        return ProjectAdaptation(
            project_id=normalized_project_id,
            content=adapted_content,
            updated_at=updated_at,
        )

    def list_adaptations(self, project_id: str) -> list[ProjectAdaptation]:
        """Return every saved platform version for one project, newest first."""
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT project_id, adapted_content_json, updated_at
                FROM project_adaptations
                WHERE project_id = ?
                ORDER BY updated_at DESC, platform ASC
                """,
                (project_id,),
            ).fetchall()
        return [
            ProjectAdaptation(
                project_id=row["project_id"],
                content=AdaptedContent.model_validate_json(row["adapted_content_json"]),
                updated_at=datetime.fromisoformat(row["updated_at"]),
            )
            for row in rows
        ]

    def get_feedback(self, project_id: str) -> ProjectFeedback | None:
        """Return the latest feedback for one project when it exists."""
        with self._connect() as connection:
            row = connection.execute(
                "SELECT project_id, rating, comment, updated_at FROM project_feedback WHERE project_id = ?",
                (project_id,),
            ).fetchone()
        return self._to_feedback(row) if row else None

    def get_feedback_overview(self, *, limit: int = 20) -> FeedbackOverview:
        """Aggregate user judgments with the stored review score for local evaluation."""
        if not 1 <= limit <= 100:
            raise ValueError("limit must be between 1 and 100")
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT feedback.project_id, feedback.rating, feedback.comment, feedback.updated_at,
                       projects.topic, projects.review_json
                FROM project_feedback AS feedback
                JOIN projects ON projects.id = feedback.project_id
                ORDER BY feedback.updated_at DESC, feedback.project_id DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
        items = tuple(
            FeedbackProjectItem(
                project_id=row["project_id"],
                topic=row["topic"],
                rating=row["rating"],  # type: ignore[arg-type]
                comment=row["comment"],
                review_score=ReviewReport.model_validate_json(row["review_json"]).score,
                updated_at=datetime.fromisoformat(row["updated_at"]),
            )
            for row in rows
        )
        helpful_count = sum(item.rating == "有帮助" for item in items)
        total_count = len(items)
        return FeedbackOverview(
            total_count=total_count,
            helpful_count=helpful_count,
            improvement_count=total_count - helpful_count,
            helpful_rate=round(helpful_count / total_count * 100) if total_count else None,
            average_review_score=round(sum(item.review_score for item in items) / total_count)
            if total_count
            else None,
            recent_items=items,
        )

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

    @staticmethod
    def _to_feedback(row: sqlite3.Row) -> ProjectFeedback:
        return ProjectFeedback(
            project_id=row["project_id"],
            rating=row["rating"],  # type: ignore[arg-type]
            comment=row["comment"],
            updated_at=datetime.fromisoformat(row["updated_at"]),
        )
