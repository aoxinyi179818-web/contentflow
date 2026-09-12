"""Tests for evidence-aware Reviewer contracts."""

from contentflow.models import ReviewReport
from contentflow.reviewer import build_reviewer_messages


def test_review_report_keeps_evidence_score_separate_from_writing_score() -> None:
    report = ReviewReport(
        score=80,
        summary="写作质量合格，但引用不足。",
        structure_score=20,
        clarity_score=20,
        audience_tone_score=20,
        completeness_score=20,
        evidence_score=8,
    )

    assert report.score == 80
    assert report.evidence_score == 8


def test_reviewer_messages_include_research_context_for_evidence_checking() -> None:
    messages = build_reviewer_messages(
        "初稿包含一个外部事实。",
        research_context="[source-a] 演示来源 | https://example.invalid/a\n证据片段",
    )

    assert "Research Context" in messages[1]["content"]
    assert "[source-a]" in messages[1]["content"]
