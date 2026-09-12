"""Chinese-first Streamlit interface for the ContentFlow AI MVP."""

from __future__ import annotations

import streamlit as st

from contentflow.config import Settings
from contentflow.database import ProjectRepository
from contentflow.error_handling import present_failure
from contentflow.mvp import MvpResult, run_mvp
from contentflow.observability import configure_logging, log_event, new_run_id

configure_logging()

st.set_page_config(
    page_title="ContentFlow AI",
    page_icon="✦",
    layout="wide",
    initial_sidebar_state="collapsed",
)


def apply_styles() -> None:
    """Keep the first interface intentional without introducing a component library."""
    st.markdown(
        """
        <style>
        .stApp { background: #eef3f5; color: #17232b; }
        .block-container { max-width: 1240px; padding-top: 3.5rem; padding-bottom: 4rem; }
        .eyebrow { color: #d55e4d; font-size: 0.76rem; font-weight: 700; letter-spacing: 0.14em; text-transform: uppercase; }
        .hero-copy { max-width: 46rem; color: #52616a; font-size: 1.05rem; line-height: 1.65; margin: 0.4rem 0 1.8rem; }
        .workflow-card { background: #17232b; border-radius: 20px; color: #f7fafb; padding: 1.25rem 1.3rem; margin-bottom: 1.25rem; }
        .workflow-label { color: #aebcc3; font-size: 0.77rem; letter-spacing: 0.1em; text-transform: uppercase; margin-bottom: 0.9rem; }
        .flow-rail { display: flex; gap: 0.4rem; align-items: stretch; }
        .flow-node { flex: 1; border: 1px solid #43515a; border-radius: 12px; padding: 0.8rem 0.7rem; min-height: 88px; }
        .flow-index { color: #f5826d; font-size: 0.72rem; font-weight: 700; }
        .flow-title { display: block; font-size: 1rem; font-weight: 700; margin: 0.32rem 0; }
        .flow-desc { color: #bfcbd0; font-size: 0.79rem; line-height: 1.35; }
        .panel-note { color: #64727a; font-size: 0.88rem; line-height: 1.55; }
        .empty-state { background: #fff; border: 1px dashed #b9c8ce; border-radius: 16px; padding: 2.4rem 1.8rem; text-align: center; color: #64727a; }
        div[data-testid="stForm"] { background: #fff; border: 1px solid #d9e2e5; border-radius: 18px; padding: 1.2rem 1.25rem 1.3rem; }
        div[data-testid="stTabs"] button { font-weight: 650; }
        .stDownloadButton button, .stFormSubmitButton button { border-radius: 10px; font-weight: 700; }
        @media (max-width: 760px) { .flow-rail { flex-direction: column; } }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_workflow_rail() -> None:
    """Render the actual four-stage workflow users are about to run."""
    steps = (
        ("01", "策划", "澄清受众、语气与结构"),
        ("02", "写作", "根据计划生成内容初稿"),
        ("03", "审阅", "按四个维度评估质量"),
        ("04", "修订", "依据建议完成一轮改写"),
    )
    nodes = "".join(
        (
            '<div class="flow-node">'
            f'<span class="flow-index">{index}</span>'
            f'<span class="flow-title">{title}</span>'
            f'<span class="flow-desc">{description}</span>'
            "</div>"
        )
        for index, title, description in steps
    )
    st.markdown(
        f'<section class="workflow-card"><div class="workflow-label">一次运行，四个真实节点</div>'
        f'<div class="flow-rail">{nodes}</div></section>',
        unsafe_allow_html=True,
    )


def render_plan(result: MvpResult) -> None:
    st.caption(f"受众：{result.plan.audience}　·　语气：{result.plan.tone}")
    if result.plan.scope_note:
        st.info(result.plan.scope_note)
    for order, section in enumerate(result.plan.sections, start=1):
        st.markdown(f"**{order:02d}. {section.title}**　{section.objective}")


def render_review(result: MvpResult) -> None:
    report = result.review
    score, structure, clarity, tone, completeness = st.columns(5)
    score.metric("总分", f"{report.score}/100")
    structure.metric("结构", f"{report.structure_score}/25")
    clarity.metric("清晰度", f"{report.clarity_score}/25")
    tone.metric("受众与语气", f"{report.audience_tone_score}/25")
    completeness.metric("完整度", f"{report.completeness_score}/25")
    st.markdown(f"**审阅结论：** {report.summary}")

    if report.problems:
        st.markdown("**待处理问题**")
        st.dataframe(
            [
                {
                    "严重程度": item.severity,
                    "问题类型": item.problem_type,
                    "位置": item.location,
                    "原因": item.reason,
                    "建议": item.suggestion,
                }
                for item in report.problems
            ],
            hide_index=True,
            use_container_width=True,
        )
    if report.priority_suggestions:
        st.markdown("**优先修订建议**")
        for suggestion in report.priority_suggestions:
            st.markdown(f"- {suggestion}")


def render_result(result: MvpResult) -> None:
    """Present every workflow artifact so users can inspect, not only copy, AI output."""
    st.divider()
    st.subheader("本次内容包")
    st.info(
        "使用提示：AI 生成内容可能有错误，请核查关键事实、引用和适用范围。"
        "当前 Research 使用本地演示资料，不等同于实时网络检索。"
    )
    if result.metrics:
        metrics = result.metrics
        llm, tools, rewrites, duration, tokens = st.columns(5)
        llm.metric("模型调用", metrics.llm_call_count)
        tools.metric("工具调用", metrics.tool_call_count)
        rewrites.metric("改写次数", metrics.rewrite_count)
        duration.metric("工作流耗时", f"{metrics.duration_ms or 0} ms")
        tokens.metric("Token", metrics.total_tokens if metrics.total_tokens is not None else "未采集")
        if metrics.total_tokens is None:
            st.caption("当前模型响应未提供可用 Token usage，因此只展示真实调用次数，不估算成本。")
    plan_tab, draft_tab, review_tab, final_tab = st.tabs(["内容计划", "初稿", "审阅报告", "修订稿"])
    with plan_tab:
        render_plan(result)
    with draft_tab:
        st.markdown(result.draft)
    with review_tab:
        render_review(result)
    with final_tab:
        st.markdown(result.final_content)
        st.download_button(
            "下载修订稿 (.md)",
            data=result.final_content,
            file_name="contentflow-修订稿.md",
            mime="text/markdown",
            use_container_width=True,
        )


def main() -> None:
    apply_styles()
    st.markdown('<div class="eyebrow">ContentFlow AI · MVP</div>', unsafe_allow_html=True)
    st.title("把一个主题，变成可审阅的内容")
    st.markdown(
        '<p class="hero-copy">输入内容主题，依次运行策划、写作、审阅和修订。你可以保留每一环的产物，判断 AI 的结论是否可靠，而不只是拿走一段成稿。</p>',
        unsafe_allow_html=True,
    )
    render_workflow_rail()

    left, right = st.columns((1.08, 0.92), gap="large")
    with left:
        st.subheader("开始一轮创作")
        with st.form("创作配置", border=False):
            topic = st.text_area(
                "本次想创作什么？",
                placeholder="例如：面向大学新生，写一篇 800 字的文章，解释如何建立可持续的学习习惯。",
                height=150,
            )
            submitted = st.form_submit_button("开始生成内容包", use_container_width=True)
        st.markdown(
            '<p class="panel-note">当前 MVP 的输入仅为“主题”。受众、语气和文章结构由策划节点先生成，后续阶段会继续扩展为可编辑配置。</p>',
            unsafe_allow_html=True,
        )

    with right:
        st.subheader("你会看到什么")
        st.markdown(
            """
            - 可检查的内容计划，而不是黑箱提示词
            - 初稿与修订稿，便于比较改写是否真的改善
            - 结构、清晰度、受众语气、完整度四项评分
            """
        )

    if submitted:
        if not topic.strip():
            log_event("ui_input_error", error_type="TopicInputError", topic_length=0)
            st.error("请输入内容主题后再开始生成。")
        else:
            run_id = new_run_id()
            normalized_topic = topic.strip()
            log_event("ui_submit", run_id=run_id, topic_length=len(normalized_topic))
            try:
                with st.spinner("正在依次完成策划、写作、审阅和修订…"):
                    settings = Settings.from_env()
                    repository = ProjectRepository(settings.database_url)
                    st.session_state["mvp_result"] = run_mvp(
                        normalized_topic,
                        settings=settings,
                        repository=repository,
                        run_id=run_id,
                    )
                log_event("ui_complete", run_id=run_id)
                st.success("内容包已保存到本地项目历史。")
            except Exception as error:
                log_event("ui_error", run_id=run_id, error_type=type(error).__name__)
                presentation = present_failure(error)
                if presentation.code == "unexpected":
                    raise
                st.error(f"{presentation.title}：{presentation.message}")

    result = st.session_state.get("mvp_result")
    if result is None:
        st.markdown(
            '<div class="empty-state"><strong>还没有内容包</strong><br>在左侧输入主题并开始生成；结果会留在本次页面会话中供你检查。</div>',
            unsafe_allow_html=True,
        )
    else:
        render_result(result)


if __name__ == "__main__":
    main()
