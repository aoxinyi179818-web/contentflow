"""Shared state definitions for the ContentFlow LangGraph workflow."""

from typing import NotRequired, TypedDict

from contentflow.config import Settings
from contentflow.models import ContentPlan, ReviewReport


class ContentFlowState(TypedDict):
    """Data shared across the base content creation graph."""

    topic: str
    run_id: str
    settings: Settings
    quality_threshold: int
    max_rewrite_count: int
    rewrite_count: int
    status: str
    plan: NotRequired[ContentPlan]
    draft: NotRequired[str]
    current_content: NotRequired[str]
    review: NotRequired[ReviewReport]
    final_content: NotRequired[str]
