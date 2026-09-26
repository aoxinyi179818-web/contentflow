"""One-pass pure Python MVP workflow for ContentFlow AI Step 24."""

import argparse
from dataclasses import dataclass
from functools import partial

from contentflow.config import Settings
from contentflow.database import ProjectRepository
from contentflow.models import (
    AdaptedContent,
    ContentPlan,
    ContentPreferences,
    PublishingAssets,
    ReviewReport,
    VisualPlan,
)
from contentflow.observability import (
    RunMetrics,
    configure_logging,
    get_run_metrics,
    log_event,
    new_run_id,
)
from contentflow.planner import create_plan
from contentflow.reviewer import review_draft
from contentflow.rewriter import rewrite_draft
from contentflow.workflow.graph import WorkflowServices, run_contentflow_graph
from contentflow.writer import create_draft


@dataclass(frozen=True)
class MvpResult:
    """Artifacts produced by the first end-to-end ContentFlow MVP run."""

    plan: ContentPlan
    draft: str
    review: ReviewReport
    final_content: str
    status: str
    metrics: RunMetrics | None = None
    project_id: str | None = None
    adaptations: tuple[AdaptedContent, ...] = ()
    visual_plan: VisualPlan | None = None
    publishing_assets: tuple[PublishingAssets, ...] = ()
    original_final_content: str | None = None


def run_mvp(
    topic: str,
    settings: Settings | None = None,
    repository: ProjectRepository | None = None,
    run_id: str | None = None,
    preferences: ContentPreferences | None = None,
) -> MvpResult:
    """Run the bounded LangGraph workflow while preserving the MVP result interface."""
    active_settings = settings or Settings.from_env()
    active_run_id = run_id or new_run_id()
    log_event("mvp_start", run_id=active_run_id)
    try:
        planner_service = (
            partial(create_plan, preferences=preferences) if preferences else create_plan
        )
        workflow_result = run_contentflow_graph(
            topic,
            settings=active_settings,
            services=WorkflowServices(planner_service, create_draft, review_draft, rewrite_draft),
            run_id=active_run_id,
        )
        project_id = None
        if repository:
            saved_project = repository.save_project(
                topic=topic,
                plan=workflow_result["plan"],
                draft=workflow_result["draft"],
                review=workflow_result["review"],
                final_content=workflow_result["final_content"],
                status=workflow_result["status"],
                run_id=active_run_id,
            )
            project_id = saved_project.id if saved_project else None
        result = MvpResult(
            plan=workflow_result["plan"],
            draft=workflow_result["draft"],
            review=workflow_result["review"],
            final_content=workflow_result["final_content"],
            status=workflow_result["status"],
            metrics=get_run_metrics(active_run_id),
            project_id=project_id,
            original_final_content=workflow_result["final_content"],
        )
    except Exception as error:
        log_event("mvp_error", run_id=active_run_id, error_type=type(error).__name__)
        raise
    log_event("mvp_end", run_id=active_run_id, status=result.status)
    return result


def main() -> None:
    configure_logging()
    parser = argparse.ArgumentParser(description="Run the one-pass ContentFlow AI MVP workflow.")
    parser.add_argument("topic", help="Topic for the content workflow.")
    args = parser.parse_args()
    result = run_mvp(args.topic)
    print(f"# 内容计划\n\n{result.plan.model_dump_json(indent=2)}\n\n# 初稿\n\n{result.draft}")
    print(
        f"\n\n# 审阅报告\n\n{result.review.model_dump_json(indent=2)}\n\n# 修订稿\n\n{result.final_content}"
    )


if __name__ == "__main__":
    main()
