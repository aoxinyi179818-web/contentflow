"""Portable, user-facing exports for completed ContentFlow runs."""

from __future__ import annotations

import re

from contentflow.mvp import MvpResult

_INVALID_FILENAME_CHARACTERS = re.compile(r'[<>:"/\\|?*\x00-\x1f]')
_WHITESPACE = re.compile(r"\s+")


def sanitize_export_stem(value: str, fallback: str = "contentflow-内容包") -> str:
    """Return a safe, readable filename stem without a path or extension."""
    normalized = _INVALID_FILENAME_CHARACTERS.sub("-", value)
    normalized = normalized.replace("..", "-")
    normalized = _WHITESPACE.sub(" ", normalized).strip(" .-")
    return normalized[:80] or fallback


def default_export_stem(topic: str) -> str:
    """Build the initial filename shown to the user for one generated topic."""
    return f"contentflow-{sanitize_export_stem(topic, fallback='内容包')}"


def render_content_package_markdown(result: MvpResult) -> str:
    """Create one portable Markdown package containing each inspectable artifact."""
    plan_lines = [
        f"- 主题：{result.plan.topic}",
        f"- 受众：{result.plan.audience}",
        f"- 语气：{result.plan.tone}",
        f"- 平台：{result.plan.platform}",
        f"- 目标篇幅：{result.plan.target_length}",
    ]
    if result.plan.scope_note:
        plan_lines.append(f"- 范围说明：{result.plan.scope_note}")
    plan_lines.extend(
        f"{index}. **{section.title}**：{section.objective}"
        for index, section in enumerate(result.plan.sections, start=1)
    )

    review_lines = [
        f"- 总分：{result.review.score}/100",
        f"- 结构：{result.review.structure_score}/25",
        f"- 清晰度：{result.review.clarity_score}/25",
        f"- 受众与语气：{result.review.audience_tone_score}/25",
        f"- 完整度：{result.review.completeness_score}/25",
        f"- 审阅结论：{result.review.summary}",
    ]
    if result.review.priority_suggestions:
        review_lines.append("\n### 优先修订建议")
        review_lines.extend(f"- {suggestion}" for suggestion in result.review.priority_suggestions)
    if result.review.problems:
        review_lines.append("\n### 待处理问题")
        review_lines.extend(
            (
                f"- [{problem.severity}] {problem.problem_type}（{problem.location}）："
                f"{problem.reason}；建议：{problem.suggestion}"
            )
            for problem in result.review.problems
        )

    sections = [
        "# ContentFlow AI 内容包",
        "## 内容计划\n" + "\n".join(plan_lines),
        "## 初稿\n" + result.draft,
        "## 审阅报告\n" + "\n".join(review_lines),
        "## 修订稿\n" + result.final_content,
    ]
    if result.research and result.research.sources:
        source_lines = [
            f"- [{source.source_id}] {source.title}：{source.url}"
            for source in result.research.sources
        ]
        sections.insert(2, "## 本次参考来源\n" + "\n".join(source_lines))
    sections.extend(
        f"## 平台版本：{adaptation.platform}\n"
        f"### {adaptation.title}\n\n{adaptation.content}\n\n"
        + "\n".join(f"- {note}" for note in adaptation.format_notes)
        for adaptation in result.adaptations
    )
    sections.extend(
        "## 发布包装：" + assets.platform + "\n"
        + "### 标题备选\n"
        + "\n".join(f"{index}. {title}" for index, title in enumerate(assets.titles, start=1))
        + "\n\n### 封面 / 开头钩子\n"
        + "\n".join(f"- {hook}" for hook in assets.cover_hooks)
        + ("\n\n### 建议标签\n" + " ".join(f"#{tag}" for tag in assets.tags) if assets.tags else "")
        + "\n\n### 互动收尾\n" + assets.call_to_action
        for assets in result.publishing_assets
    )
    if result.visual_plan:
        visual_lines = [f"- 规划说明：{result.visual_plan.overview}"]
        visual_lines.extend(
            (
                f"- {asset.section_anchor}：{asset.purpose}；"
                f"提示词 / 搜索词：{asset.query_or_prompt}；理由：{asset.rationale}"
            )
            for asset in result.visual_plan.assets
        )
        sections.append("## 视觉素材建议（仅规划）\n" + "\n".join(visual_lines))
    return "\n\n".join(sections) + "\n"
